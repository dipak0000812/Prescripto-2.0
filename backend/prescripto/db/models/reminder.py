"""
Prescripto AI 2.0 — Medicine Reminder Engine Models.
Implements:
- ReminderPlan: Medication regimen schedules, daily time slots, start/end dates.
- ReminderEvent: Scheduled dose instances (due_at, taken, snoozed, skipped, missed).
- PushSubscription: Web Push notification tokens with VAPID authentication.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    String, Integer, DateTime, CheckConstraint, ForeignKey,
    Index, JSON, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from prescripto.db.base import Base, utc_now


class ReminderPlan(Base):
    __tablename__ = "reminder_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_reminder_plans_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", name="fk_reminder_plans_patient_id", ondelete="SET NULL"),
        nullable=True,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", name="fk_reminder_plans_analysis_id", ondelete="CASCADE"),
        nullable=False,
    )
    prescription_med_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescription_medications.id", name="fk_reminder_plans_med_id", ondelete="SET NULL"),
        nullable=True,
    )
    medicine_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    local_times: Mapped[List[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list, nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("status IN ('ACTIVE', 'PAUSED', 'COMPLETED')", name="chk_reminder_plan_status"),
        default="ACTIVE",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    events: Mapped[List[ReminderEvent]] = relationship(
        "ReminderEvent", back_populates="plan", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_reminder_plans_user_status", "user_id", "status"),
        Index("idx_reminder_plans_analysis", "analysis_id"),
    )


class ReminderEvent(Base):
    __tablename__ = "reminder_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reminder_plans.id", name="fk_reminder_events_plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "status IN ('PENDING', 'SENT', 'TAKEN', 'SNOOZED', 'SKIPPED', 'MISSED')",
            name="chk_reminder_event_status"
        ),
        default="PENDING",
        nullable=False,
    )
    acted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    plan: Mapped[ReminderPlan] = relationship("ReminderPlan", back_populates="events")

    __table_args__ = (
        Index("idx_reminder_events_due_status", "due_at", "status"),
        Index("idx_reminder_events_plan_id", "plan_id"),
    )


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_push_sub_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    keys_p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    keys_auth: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        Index("idx_push_sub_user", "user_id"),
    )

