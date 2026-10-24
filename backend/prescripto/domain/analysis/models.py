"""
Prescripto AI 2.0 — Pure Domain Analysis Models.
Strict Layering: Zero external dependencies (no FastAPI, no SQLAlchemy, no Boto3).
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class AnalysisStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    REVIEWING = "REVIEWING"
    REVIEWED_COMPLETE = "REVIEWED_COMPLETE"
    REVIEWED_ESCALATED = "REVIEWED_ESCALATED"
    FAILED = "FAILED"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEAD = "DEAD"
    CANCELLED = "CANCELLED"


@dataclass
class Analysis:
    """Pure domain entity representing an analysis run on a prescription document."""
    id: uuid.UUID
    document_id: uuid.UUID
    model_snapshot_id: uuid.UUID
    pipeline_version: str = "1.0.0"
    status: AnalysisStatus = AnalysisStatus.QUEUED
    review_required: bool = False
    review_reasons: List[str] = field(default_factory=list)
    error_detail: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_finished(self) -> bool:
        return self.status in (
            AnalysisStatus.COMPLETED,
            AnalysisStatus.REQUIRES_REVIEW,
            AnalysisStatus.REVIEWED_COMPLETE,
            AnalysisStatus.REVIEWED_ESCALATED,
            AnalysisStatus.FAILED,
        )

    def is_reviewable(self) -> bool:
        return self.status == AnalysisStatus.REQUIRES_REVIEW
