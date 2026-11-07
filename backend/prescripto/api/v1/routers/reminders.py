"""
Prescripto AI 2.0 — Medicine Reminders API Router.
Handles plan creation, schedule adjustments, event actions (taken, snooze, skip),
VAPID public key distribution, Web Push subscriptions, adherence logs, and ICS calendars.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Response, Query
from sqlalchemy.orm import Session

from prescripto.db.session import get_db
from prescripto.db.models.users import User
from prescripto.auth.dependencies import get_current_user
from prescripto.config.settings import settings
from prescripto.application.services.reminder_service import ReminderService
from prescripto.api.v1.schemas.reminder import (
    CreatePlansRequest,
    ReminderPlanOut,
    ReminderEventOut,
    TodayRemindersResponse,
    UpdateEventRequest,
    UpdatePlanRequest,
    PushSubscribeRequest,
    VapidPublicKeyResponse,
    AdherenceReportResponse,
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.post(
    "/plans",
    response_model=List[ReminderPlanOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create reminder plans from confirmed prescription medications",
    operation_id="createReminderPlans",
)
def create_reminder_plans(
    req: CreatePlansRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ReminderPlanOut]:
    try:
        return ReminderService.create_plans_from_analysis(db, current_user, req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/today",
    response_model=TodayRemindersResponse,
    status_code=status.HTTP_200_OK,
    summary="Get today's upcoming, overdue, and completed medicine doses",
    operation_id="getTodayReminders",
)
def get_today_reminders(
    timezone: str = Query(default="Asia/Kolkata"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TodayRemindersResponse:
    return ReminderService.get_today_reminders(db, current_user, timezone)


@router.patch(
    "/events/{event_id}",
    response_model=ReminderEventOut,
    status_code=status.HTTP_200_OK,
    summary="Action a dose event: TAKEN, SNOOZE (10 min), or SKIP",
    operation_id="actOnReminderEvent",
)
def act_on_reminder_event(
    event_id: uuid.UUID,
    req: UpdateEventRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderEventOut:
    try:
        return ReminderService.act_on_event(db, event_id, req.action, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch(
    "/plans/{plan_id}",
    response_model=ReminderPlanOut,
    status_code=status.HTTP_200_OK,
    summary="Update plan schedule times or pause/resume status",
    operation_id="updateReminderPlan",
)
def update_reminder_plan(
    plan_id: uuid.UUID,
    req: UpdatePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderPlanOut:
    try:
        return ReminderService.update_plan(db, plan_id, req, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a reminder plan",
    operation_id="deleteReminderPlan",
)
def delete_reminder_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        ReminderService.delete_plan(db, plan_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/plans/{plan_id}/calendar.ics",
    summary="Download RFC 5545 iCalendar feed for phone calendar with alarms",
    operation_id="downloadPlanIcs",
)
def download_plan_ics(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        ics_text = ReminderService.export_plan_ics(db, plan_id, current_user)
        return Response(
            content=ics_text,
            media_type="text/calendar",
            headers={"Content-Disposition": f"attachment; filename=prescripto-plan-{plan_id}.ics"},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/vapid-public-key",
    response_model=VapidPublicKeyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get VAPID public key for Web Push subscription",
    operation_id="getVapidPublicKey",
)
def get_vapid_public_key() -> VapidPublicKeyResponse:
    key = settings.VAPID_PUBLIC_KEY or ""
    return VapidPublicKeyResponse(public_key=key)


@router.post(
    "/push/subscribe",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Register browser Web Push subscription",
    operation_id="subscribeWebPush",
)
def subscribe_web_push(
    req: PushSubscribeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    ReminderService.subscribe_push(db, req, current_user)


@router.delete(
    "/push/subscribe",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister browser Web Push subscription",
    operation_id="unsubscribeWebPush",
)
def unsubscribe_web_push(
    endpoint: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    ReminderService.unsubscribe_push(db, endpoint, current_user)


@router.get(
    "/adherence",
    response_model=AdherenceReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient medication adherence log (taken, missed, skipped)",
    operation_id="getAdherenceReport",
)
def get_adherence_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdherenceReportResponse:
    return ReminderService.get_adherence_report(db, current_user)

