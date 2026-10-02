"""
Pydantic Schemas for Analysis Status, Result, and Review.
Strictly matches OPENAPI.yaml canonical contracts.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AnalysisStageOut(BaseModel):
    stage_name: str
    status: str
    error_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisStatus(BaseModel):
    analysis_id: uuid.UUID
    status: str
    stages: List[AnalysisStageOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FieldValue(BaseModel):
    value: Optional[str] = None
    state: str
    confidence: float = Field(ge=0.0, le=1.0)

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


class AnalysisResult(BaseModel):
    analysis_id: uuid.UUID
    status: str
    analysis_timestamp: datetime
    model_versions: List[str] = Field(default_factory=list)
    knowledge_snapshots: List[str] = Field(default_factory=list)
    medications: List[MedicationLine] = Field(default_factory=list)
    findings: List[RiskFindingOut] = Field(default_factory=list)
    not_evaluated: List[NotEvaluatedItem] = Field(default_factory=list)
    coverage_disclaimer: str

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
