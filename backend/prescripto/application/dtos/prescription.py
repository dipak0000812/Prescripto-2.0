"""
Prescripto AI 2.0 — Prescription Application DTOs.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class IngestPrescriptionInput:
    file_bytes: bytes
    uploader_id: uuid.UUID
    idempotency_key: str
    patient_external_id: Optional[str] = None


@dataclass
class IngestPrescriptionOutput:
    prescription_id: uuid.UUID
    analysis_id: uuid.UUID
    is_replay: bool = False


@dataclass
class PrescriptionSummaryDTO:
    prescription_id: uuid.UUID
    uploaded_at: datetime
    status: str
    latest_analysis_status: Optional[str] = None


@dataclass
class AnalysisSummaryDTO:
    analysis_id: uuid.UUID
    status: str
    created_at: datetime


@dataclass
class PrescriptionDetailDTO:
    prescription_id: uuid.UUID
    status: str
    uploaded_at: datetime
    mime_type: str
    file_size_bytes: int
    patient_ref: Optional[str] = None
    image_url: Optional[str] = None
    analyses: List[AnalysisSummaryDTO] = field(default_factory=list)
