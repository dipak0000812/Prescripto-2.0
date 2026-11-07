"""
Prescripto AI 2.0 — Medicine Reminders Application Service.
Handles plan lifecycle, event actioning, adherence metrics, ICS generation, and Web Push dispatch.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from prescripto.db.base import utc_now, ensure_utc
from prescripto.config.settings import settings
from prescripto.db.models.users import User
from prescripto.db.models.patient import Patient
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.medication import PrescriptionMedication
from prescripto.db.models.reminder import ReminderPlan, ReminderEvent, PushSubscription
from prescripto.domain.reminder.generator import (
    generate_default_times,
    compute_due_dates_utc,
    generate_ics_calendar,
    get_timezone,
    DEFAULT_TIMEZONE,
)
from prescripto.api.v1.schemas.reminder import (
    CreatePlansRequest,
    ReminderPlanOut,
    ReminderEventOut,
    TodayRemindersResponse,
    AdherenceReportResponse,
    AdherenceItem,
    PushSubscribeRequest,
    UpdatePlanRequest,
)

logger = logging.getLogger("prescripto.reminders")


class ReminderService:
    @staticmethod
    def create_plans_from_analysis(
        db: Session, caller: User, req: CreatePlansRequest
    ) -> List[ReminderPlanOut]:
        """Creates reminder plans only for reviewed/confirmed medicines."""
        analysis = db.query(Analysis).filter(Analysis.id == req.analysis_id).first()
        if not analysis:
            raise ValueError(f"Analysis {req.analysis_id} not found")

        doc = db.query(PrescriptionDocument).filter(
            PrescriptionDocument.id == analysis.document_id
        ).first()

        # Resolve linked patient if any
        patient_id = None
        if caller.role == "OPERATOR" or getattr(caller, "is_patient", False):
            pat = db.query(Patient).filter(Patient.user_id == caller.id).first()
            if pat:
                patient_id = pat.id
        elif doc and doc.patient_ref:
            pat = db.query(Patient).filter(
                (Patient.patient_id == doc.patient_ref) | (Patient.phone_number == doc.patient_ref)
            ).first()
            if pat:
                patient_id = pat.id

        created_plans: List[ReminderPlan] = []
        tz_str = req.timezone or DEFAULT_TIMEZONE
        now_dt = utc_now()

        for med_item in req.medications:
            # If line_id is provided, verify it is not flagged unreadable
            if med_item.medication_line_id:
                med_line = db.query(PrescriptionMedication).filter(
                    PrescriptionMedication.id == med_item.medication_line_id
                ).first()
                if med_line and med_line.name_state == "UNREADABLE":
                    continue  # Safety constraint: never create alarms for unreadable lines

            times = [t.strip() for t in med_item.local_times if t.strip()]
            if not times:
                times = generate_default_times(None, None)

            end_dt = None
            if med_item.duration_days and med_item.duration_days > 0:
                end_dt = now_dt + timedelta(days=med_item.duration_days)

            plan = ReminderPlan(
                id=uuid.uuid4(),
                user_id=caller.id,
                patient_id=patient_id,
                analysis_id=req.analysis_id,
                prescription_med_id=med_item.medication_line_id,
                medicine_name=med_item.medicine_name.strip(),
                dosage_text=med_item.dosage_text.strip() if med_item.dosage_text else None,
                local_times=times,
                start_date=now_dt,
                end_date=end_dt,
                timezone=tz_str,
                status="ACTIVE",
                created_at=now_dt,
                updated_at=now_dt,
            )
            db.add(plan)
            db.flush()

            # Generate initial events
            due_dates = compute_due_dates_utc(
                local_times=times,
                start_date=now_dt,
                end_date=end_dt,
                tz_str=tz_str,
                days_ahead=14,
            )
            for d_utc in due_dates:
                event = ReminderEvent(
                    id=uuid.uuid4(),
                    plan_id=plan.id,
                    due_at=d_utc,
                    status="PENDING",
                    sent_count=0,
                    created_at=now_dt,
                )
                db.add(event)

            created_plans.append(plan)

        db.commit()

        out_list: List[ReminderPlanOut] = []
        for p in created_plans:
            db.refresh(p)
            out_list.append(
                ReminderPlanOut(
                    id=p.id,
                    user_id=p.user_id,
                    patient_id=p.patient_id,
                    analysis_id=p.analysis_id,
                    prescription_med_id=p.prescription_med_id,
                    medicine_name=p.medicine_name,
                    dosage_text=p.dosage_text,
                    local_times=p.local_times,
                    start_date=ensure_utc(p.start_date) or now_dt,
                    end_date=ensure_utc(p.end_date),
                    timezone=p.timezone,
                    status=p.status,
                    created_at=ensure_utc(p.created_at) or now_dt,
                )
            )
        return out_list

    @staticmethod
    def get_today_reminders(
        db: Session, caller: User, tz_str: str = DEFAULT_TIMEZONE
    ) -> TodayRemindersResponse:
        """Retrieves today's upcoming, overdue, and completed medicine doses."""
        tz = get_timezone(tz_str)
        now_utc = utc_now()
        now_local = now_utc.astimezone(tz)

        start_local = datetime(
            year=now_local.year, month=now_local.month, day=now_local.day, hour=0, minute=0, second=0, tzinfo=tz
        )
        end_local = datetime(
            year=now_local.year, month=now_local.month, day=now_local.day, hour=23, minute=59, second=59, tzinfo=tz
        )

        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)

        # Get all active plans for caller
        plans = db.query(ReminderPlan).filter(
            ReminderPlan.user_id == caller.id,
            ReminderPlan.status == "ACTIVE",
        ).all()
        plan_map = {p.id: p for p in plans}
        plan_ids = list(plan_map.keys())

        if not plan_ids:
            return TodayRemindersResponse(
                today_date=now_local.strftime("%Y-%m-%d"),
                total_due=0,
                taken_count=0,
                pending_count=0,
                upcoming=[],
                overdue=[],
                completed=[],
            )

        events = db.query(ReminderEvent).filter(
            ReminderEvent.plan_id.in_(plan_ids),
            or_(
                # Events due today
                and_(ReminderEvent.due_at >= start_utc, ReminderEvent.due_at <= end_utc),
                # Or past overdue events that are still pending
                and_(ReminderEvent.status.in_(["PENDING", "SENT"]), ReminderEvent.due_at < start_utc),
            ),
        ).order_by(ReminderEvent.due_at.asc()).all()

        upcoming: List[ReminderEventOut] = []
        overdue: List[ReminderEventOut] = []
        completed: List[ReminderEventOut] = []

        grace_threshold = now_utc - timedelta(minutes=15)

        for ev in events:
            p = plan_map.get(ev.plan_id)
            if not p:
                continue

            due_utc = ensure_utc(ev.due_at) or now_utc
            item = ReminderEventOut(
                id=ev.id,
                plan_id=ev.plan_id,
                medicine_name=p.medicine_name,
                dosage_text=p.dosage_text,
                due_at=due_utc,
                status=ev.status,
                acted_at=ensure_utc(ev.acted_at),
            )

            if ev.status in ("TAKEN", "SKIPPED"):
                completed.append(item)
            elif ev.status in ("PENDING", "SENT", "SNOOZED"):
                if due_utc < grace_threshold:
                    overdue.append(item)
                else:
                    upcoming.append(item)

        total_due = len(upcoming) + len(overdue) + len(completed)
        taken_count = sum(1 for c in completed if c.status == "TAKEN")
        pending_count = len(upcoming) + len(overdue)

        return TodayRemindersResponse(
            today_date=now_local.strftime("%Y-%m-%d"),
            total_due=total_due,
            taken_count=taken_count,
            pending_count=pending_count,
            upcoming=upcoming,
            overdue=overdue,
            completed=completed,
        )

    @staticmethod
    def act_on_event(
        db: Session, event_id: uuid.UUID, action: str, caller: User
    ) -> ReminderEventOut:
        """Actions a reminder event: TAKEN, SNOOZE (10 min), or SKIP."""
        ev = db.query(ReminderEvent).filter(ReminderEvent.id == event_id).first()
        if not ev:
            raise ValueError(f"Reminder event {event_id} not found")

        plan = db.query(ReminderPlan).filter(ReminderPlan.id == ev.plan_id).first()
        if not plan or plan.user_id != caller.id:
            raise PermissionError("Access denied to reminder event")

        now_dt = utc_now()
        act = action.upper()

        if act == "TAKEN":
            ev.status = "TAKEN"
            ev.acted_at = now_dt
        elif act == "SKIP":
            ev.status = "SKIPPED"
            ev.acted_at = now_dt
        elif act == "SNOOZE":
            ev.status = "SNOOZED"
            ev.acted_at = now_dt
            # Follow-up alarm in 10 minutes
            followup = ReminderEvent(
                id=uuid.uuid4(),
                plan_id=plan.id,
                due_at=now_dt + timedelta(minutes=10),
                status="PENDING",
                sent_count=0,
                created_at=now_dt,
            )
            db.add(followup)
        else:
            raise ValueError(f"Invalid action: {action}")

        db.commit()
        db.refresh(ev)

        return ReminderEventOut(
            id=ev.id,
            plan_id=ev.plan_id,
            medicine_name=plan.medicine_name,
            dosage_text=plan.dosage_text,
            due_at=ensure_utc(ev.due_at) or now_dt,
            status=ev.status,
            acted_at=ensure_utc(ev.acted_at),
        )

    @staticmethod
    def update_plan(
        db: Session, plan_id: uuid.UUID, req: UpdatePlanRequest, caller: User
    ) -> ReminderPlanOut:
        """Updates plan schedule times or pause/resume status."""
        plan = db.query(ReminderPlan).filter(ReminderPlan.id == plan_id).first()
        if not plan or plan.user_id != caller.id:
            raise ValueError(f"Plan {plan_id} not found")

        now_dt = utc_now()

        if req.status:
            plan.status = req.status

        if req.local_times is not None:
            clean_times = [t.strip() for t in req.local_times if t.strip()]
            plan.local_times = clean_times
            # Remove future pending events and regenerate
            db.query(ReminderEvent).filter(
                ReminderEvent.plan_id == plan.id,
                ReminderEvent.status == "PENDING",
                ReminderEvent.due_at >= now_dt,
            ).delete()

            due_dates = compute_due_dates_utc(
                local_times=clean_times,
                start_date=now_dt,
                end_date=plan.end_date,
                tz_str=plan.timezone,
                days_ahead=14,
            )
            for d_utc in due_dates:
                ev = ReminderEvent(
                    id=uuid.uuid4(),
                    plan_id=plan.id,
                    due_at=d_utc,
                    status="PENDING",
                    sent_count=0,
                    created_at=now_dt,
                )
                db.add(ev)

        plan.updated_at = now_dt
        db.commit()
        db.refresh(plan)

        return ReminderPlanOut(
            id=plan.id,
            user_id=plan.user_id,
            patient_id=plan.patient_id,
            analysis_id=plan.analysis_id,
            prescription_med_id=plan.prescription_med_id,
            medicine_name=plan.medicine_name,
            dosage_text=plan.dosage_text,
            local_times=plan.local_times,
            start_date=ensure_utc(plan.start_date) or now_dt,
            end_date=ensure_utc(plan.end_date),
            timezone=plan.timezone,
            status=plan.status,
            created_at=ensure_utc(plan.created_at) or now_dt,
        )

    @staticmethod
    def delete_plan(db: Session, plan_id: uuid.UUID, caller: User) -> None:
        """Deletes a reminder plan and all its scheduled events."""
        plan = db.query(ReminderPlan).filter(ReminderPlan.id == plan_id).first()
        if not plan or plan.user_id != caller.id:
            raise ValueError(f"Plan {plan_id} not found")
        db.delete(plan)
        db.commit()

    @staticmethod
    def export_plan_ics(db: Session, plan_id: uuid.UUID, caller: User) -> str:
        """Generates standard RFC 5545 iCalendar string with alarms."""
        plan = db.query(ReminderPlan).filter(ReminderPlan.id == plan_id).first()
        if not plan or plan.user_id != caller.id:
            raise ValueError(f"Plan {plan_id} not found")

        events = db.query(ReminderEvent).filter(
            ReminderEvent.plan_id == plan.id,
        ).order_by(ReminderEvent.due_at.asc()).all()

        event_tuples = [(e.id, ensure_utc(e.due_at) or utc_now()) for e in events]
        return generate_ics_calendar(
            medicine_name=plan.medicine_name,
            dosage_text=plan.dosage_text,
            events=event_tuples,
            tz_str=plan.timezone,
        )

    @staticmethod
    def subscribe_push(db: Session, req: PushSubscribeRequest, caller: User) -> None:
        """Registers a browser Web Push subscription with VAPID."""
        sub = db.query(PushSubscription).filter(
            PushSubscription.endpoint == req.endpoint
        ).first()
        if sub:
            sub.user_id = caller.id
            sub.keys_p256dh = req.keys_p256dh
            sub.keys_auth = req.keys_auth
            sub.user_agent = req.user_agent
        else:
            sub = PushSubscription(
                id=uuid.uuid4(),
                user_id=caller.id,
                endpoint=req.endpoint,
                keys_p256dh=req.keys_p256dh,
                keys_auth=req.keys_auth,
                user_agent=req.user_agent,
                created_at=utc_now(),
            )
            db.add(sub)
        db.commit()

    @staticmethod
    def unsubscribe_push(db: Session, endpoint: str, caller: User) -> None:
        """Unregisters Web Push subscription."""
        db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == caller.id,
        ).delete()
        db.commit()

    @staticmethod
    def get_adherence_report(db: Session, caller: User) -> AdherenceReportResponse:
        """Computes adherence metrics (taken, missed, skipped) per medicine."""
        plans = db.query(ReminderPlan).filter(ReminderPlan.user_id == caller.id).all()
        items: List[AdherenceItem] = []
        overall_taken = 0
        overall_total = 0

        for p in plans:
            events = db.query(ReminderEvent).filter(ReminderEvent.plan_id == p.id).all()
            total = len(events)
            taken = sum(1 for e in events if e.status == "TAKEN")
            missed = sum(1 for e in events if e.status == "MISSED")
            skipped = sum(1 for e in events if e.status == "SKIPPED")
            rate = round((taken / max(1, total - skipped)) * 100, 1)

            overall_taken += taken
            overall_total += max(0, total - skipped)

            items.append(
                AdherenceItem(
                    medicine_name=p.medicine_name,
                    plan_id=p.id,
                    total_doses=total,
                    taken=taken,
                    missed=missed,
                    skipped=skipped,
                    adherence_rate=rate,
                )
            )

        overall_rate = round((overall_taken / max(1, overall_total)) * 100, 1)
        return AdherenceReportResponse(
            overall_adherence_rate=overall_rate,
            items=items,
        )

    @staticmethod
    def dispatch_due_reminders(db: Session) -> int:
        """
        Background scheduler iteration. Finds due events, sends Web Push notifications,
        and marks overdue unacted doses as MISSED after 2 hours.
        """
        now_dt = utc_now()
        due_events = db.query(ReminderEvent).filter(
            ReminderEvent.status == "PENDING",
            ReminderEvent.due_at <= now_dt,
        ).limit(50).all()

        sent_count = 0
        for ev in due_events:
            plan = db.query(ReminderPlan).filter(ReminderPlan.id == ev.plan_id).first()
            if not plan or plan.status != "ACTIVE":
                continue

            subs = db.query(PushSubscription).filter(
                PushSubscription.user_id == plan.user_id
            ).all()

            for sub in subs:
                try:
                    from pywebpush import webpush, WebPushException
                    subscription_info = {
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.keys_p256dh,
                            "auth": sub.keys_auth,
                        },
                    }
                    payload = json.dumps({
                        "title": "Prescripto Reminder",
                        "body": f"Time for your medicine: {plan.medicine_name}",
                        "eventId": str(ev.id),
                        "planId": str(plan.id),
                        "medicineName": plan.medicine_name,
                        "tag": f"med-{ev.id}",
                    })

                    vapid_priv = settings.VAPID_PRIVATE_KEY
                    if vapid_priv:
                        # Clean escaped newlines if passed in env
                        vapid_priv_pem = vapid_priv.replace("\\n", "\n")
                        webpush(
                            subscription_info=subscription_info,
                            data=payload,
                            vapid_private_key=vapid_priv_pem,
                            vapid_claims={"sub": settings.VAPID_CLAIMS_SUB},
                            timeout=5,
                        )
                except Exception as ex:
                    # 410 Gone / 404 Not Found -> expired subscription
                    if "410" in str(ex) or "404" in str(ex):
                        db.delete(sub)
                    logger.warning("push_delivery_error", error=str(ex), event_id=str(ev.id))

            ev.status = "SENT"
            ev.sent_count += 1
            sent_count += 1

        # Mark missed after 2 hours without action
        missed_threshold = now_dt - timedelta(hours=2)
        overdue_unacted = db.query(ReminderEvent).filter(
            ReminderEvent.status.in_(["PENDING", "SENT", "SNOOZED"]),
            ReminderEvent.due_at < missed_threshold,
        ).all()
        for ev in overdue_unacted:
            ev.status = "MISSED"

        db.commit()
        return sent_count
