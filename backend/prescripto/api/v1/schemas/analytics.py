"""
Analytics & Dashboard Schemas for Clinical Workload & Safety Metrics.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class PrescriptionVolume(BaseModel):
    date: str
    count: int
    completed: int
    pending_review: int
    failed: int


class SafetyMetrics(BaseModel):
    total_findings: int
    confirmed_by_source: int
    potential: int
    requires_review: int
    insufficient_evidence: int
    not_evaluated: int
    top_check_types: List[dict]


class DoctorWorkload(BaseModel):
    doctor_id: str
    doctor_name: str
    assigned_patients: int
    pending_reviews: int
    completed_reviews: int
    avg_review_time_hours: float


class SystemHealthMetrics(BaseModel):
    api_uptime_pct: float
    avg_response_time_ms: float
    error_rate_pct: float
    active_workers: int
    queue_depth: int
    storage_used_gb: float


class AnalyticsDashboardResponse(BaseModel):
    prescription_volume: List[PrescriptionVolume]
    safety_metrics: SafetyMetrics
    doctor_workload: List[DoctorWorkload]
    system_health: SystemHealthMetrics
    generated_at: str


class DateRangeParams(BaseModel):
    start_date: Optional[str] = Field(default=None, description="ISO date string (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="ISO date string (YYYY-MM-DD)")
    granularity: str = Field(default="day", description="day | week | month")