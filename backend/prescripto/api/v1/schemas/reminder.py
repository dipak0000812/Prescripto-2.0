"""
Prescripto AI 2.0 — Medicine Reminders API Schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class CreatePlanItem(BaseModel):
    medication_line_id: Optional[uuid.UUID] = None
    medicine_name: str
    dosage_text: Optional[str] = None
    local_times: List[str] = Field(default_factory=list, description="HH:MM in 24h format")
    duration_days: Optional[int] = None


class CreatePlansRequest(BaseModel):
    analysis_id: uuid.UUID
    timezone: str = "Asia/Kolkata"
    medications: List[CreatePlanItem]


class ReminderPlanOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None
    analysis_id: uuid.UUID
    prescription_med_id: Optional[uuid.UUID] = None
    medicine_name: str
    dosage_text: Optional[str] = None
    local_times: List[str]
    start_date: datetime
    end_date: Optional[datetime] = None
    timezone: str
    status: str
    created_at: datetime


class ReminderEventOut(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    medicine_name: str
    dosage_text: Optional[str] = None
    due_at: datetime
    status: str
    acted_at: Optional[datetime] = None


class UpdateEventRequest(BaseModel):
    action: Literal["TAKEN", "SNOOZE", "SKIP"]


class UpdatePlanRequest(BaseModel):
    local_times: Optional[List[str]] = None
    status: Optional[Literal["ACTIVE", "PAUSED"]] = None


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys_p256dh: str
    keys_auth: str
    user_agent: Optional[str] = None


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


class VapidPublicKeyResponse(BaseModel):
    public_key: str


class TodayRemindersResponse(BaseModel):
    today_date: str
    total_due: int
    taken_count: int
    pending_count: int
    upcoming: List[ReminderEventOut]
    overdue: List[ReminderEventOut]
    completed: List[ReminderEventOut]


class AdherenceItem(BaseModel):
    medicine_name: str
    plan_id: uuid.UUID
    total_doses: int
    taken: int
    missed: int
    skipped: int
    adherence_rate: float


class AdherenceReportResponse(BaseModel):
    overall_adherence_rate: float
    items: List[AdherenceItem]

