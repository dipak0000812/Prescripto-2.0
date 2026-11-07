"""
Pydantic Schemas for Analysis Status, Result, and Review.
Strictly matches OPENAPI.yaml canonical contracts.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AnalysisStageOut(BaseModel):
    stage_name: str
    status: str
    error_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisStatus(BaseModel):
    analysis_id: uuid.UUID
    status: str
    stages: List[AnalysisStageOut] = Field(default_factory=list)
    error_message: Optional[str] = None
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    attempts: Optional[int] = None
    fallback_reason: Optional[str] = None
    recognition_fallback_used: bool = False
    recognition_fallback_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FieldValue(BaseModel):
    value: Optional[str] = None
    state: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class MedicationLine(BaseModel):
    line_index: int
    name: FieldValue
    strength: FieldValue
    dose: FieldValue
    unit: FieldValue
    frequency: FieldValue
    route: FieldValue
    duration: FieldValue
    instructions: FieldValue
    resolved_medication_id: Optional[uuid.UUID] = None
    resolution_status: str
    is_edited: bool = False
    original_name_raw: Optional[str] = None
    edited_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RiskFindingOut(BaseModel):
    finding_id: uuid.UUID
    finding_status: str
    check_type: str
    medication_ids: List[uuid.UUID] = Field(default_factory=list)
    evidence_text: Optional[str] = None
    source_name: str
    source_version: str
    confidence_score: Optional[float] = None
    check_timestamp: datetime
    not_evaluated_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NotEvaluatedItem(BaseModel):
    medication_ids: List[uuid.UUID] = Field(default_factory=list)
    reason: str

    model_config = ConfigDict(from_attributes=True)


class ExtractedMedicationOrder(BaseModel):
    original_text: str
    name: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    needs_review: bool = True


class PrescriptionExtractionOut(BaseModel):
    processing_status: str = "needs_review"
    source_type: str = "ocr_transcription_unverified"
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    attempts: Optional[int] = None
    fallback_reason: Optional[str] = None
    recognition_fallback_used: bool = False
    recognition_fallback_reason: Optional[str] = None
    hospital_details: List[str] = Field(default_factory=list)
    patient_details: Dict[str, Any] = Field(default_factory=dict)
    date: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    diagnosis: List[str] = Field(default_factory=list)
    vitals: List[str] = Field(default_factory=list)
    medication_orders: List[ExtractedMedicationOrder] = Field(default_factory=list)
    non_medication_treatments: List[str] = Field(default_factory=list)
    general_advice: List[str] = Field(default_factory=list)
    uncertain_items: List[Dict[str, Optional[str]]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    analysis_id: uuid.UUID
    status: str
    analysis_timestamp: datetime
    model_versions: List[str] = Field(default_factory=list)
    knowledge_snapshots: List[str] = Field(default_factory=list)
    medications: List[MedicationLine] = Field(default_factory=list)
    document_extraction: Optional[PrescriptionExtractionOut] = None
    findings: List[RiskFindingOut] = Field(default_factory=list)
    not_evaluated: List[NotEvaluatedItem] = Field(default_factory=list)
    coverage_disclaimer: str
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    attempts: Optional[int] = None
    fallback_reason: Optional[str] = None
    recognition_fallback_used: bool = False
    recognition_fallback_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewDecision(BaseModel):
    finding_id: uuid.UUID
    action: str = Field(pattern="^(APPROVED|FLAGGED|ESCALATED)$")
    notes: Optional[str] = None


class ReviewSubmission(BaseModel):
    decisions: List[ReviewDecision]


class ReviewRecord(BaseModel):
    review_id: uuid.UUID
    analysis_id: uuid.UUID
    reviewer_id: uuid.UUID
    submitted_at: datetime
    overall_status: str

    model_config = ConfigDict(from_attributes=True)


class MedicationUpdateItem(BaseModel):
    line_index: int
    name: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Medicine name cannot be empty.")
            return v_stripped
        return v

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_stripped = v.strip()
            if not v_stripped:
                return None
            if v_stripped.lower() in ("as needed", "sos", "prn"):
                return v_stripped
            import re
            m = re.match(r"^(\d+)\s*(days?|weeks?|months?|d)?$", v_stripped, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                if count <= 0:
                    raise ValueError("Duration must be a positive number of days or 'as needed'.")
                return v_stripped
            raise ValueError("Duration must be a positive number of days (e.g. '5 days') or 'as needed'.")
        return v


class MedicationUpdateRequest(BaseModel):
    medications: List[MedicationUpdateItem]
