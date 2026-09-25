"""
Prescripto AI 2.0 — Pydantic Schemas for Prescription API.
Conforms strictly to OPENAPI.yaml components/schemas.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class UploadAccepted(BaseModel):
    analysis_id: uuid.UUID
    prescription_id: uuid.UUID


class PrescriptionSummary(BaseModel):
    prescription_id: uuid.UUID
    uploaded_at: datetime
    status: str
    latest_analysis_status: Optional[str] = None


class PrescriptionList(BaseModel):
    items: List[PrescriptionSummary]
    page: int
    page_size: int
    total: int


class AnalysisSummaryItem(BaseModel):
    analysis_id: uuid.UUID
    status: str
    created_at: datetime


class PrescriptionDetail(BaseModel):
    prescription_id: uuid.UUID
    status: str
    uploaded_at: datetime
    mime_type: str
    file_size_bytes: int
    patient_ref: Optional[str] = None
    image_url: Optional[str] = Field(
        default=None,
        description="Presigned GET, 60-second TTL. Never cache, log, or persist.",
    )
    analyses: List[AnalysisSummaryItem] = Field(default_factory=list)
