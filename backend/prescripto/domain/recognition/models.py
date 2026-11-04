"""
Prescripto AI 2.0 — Structured Document Recognition Domain Models.
Distinguishes clinical entity types and enforces zero false medication classification.
"""
from __future__ import annotations

import enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DocumentFieldType(str, enum.Enum):
    HOSPITAL_DETAILS = "HOSPITAL_DETAILS"
    PATIENT_DETAILS = "PATIENT_DETAILS"
    DATE = "DATE"
    SYMPTOMS_COMPLAINTS = "SYMPTOMS_COMPLAINTS"
    DIAGNOSIS = "DIAGNOSIS"
    VITAL_SIGNS = "VITAL_SIGNS"
    MEDICATION_ORDER = "MEDICATION_ORDER"
    NON_MEDICATION_TREATMENT = "NON_MEDICATION_TREATMENT"
    GENERAL_ADVICE = "GENERAL_ADVICE"
    UNCERTAIN_UNREADABLE = "UNCERTAIN_UNREADABLE"


class DocumentItem(BaseModel):
    """
    Extracted clinical document element preserving original recognized text,
    interpreted clinical meaning, and uncertainty state.
    """
    field_type: DocumentFieldType
    original_text: str
    interpreted_text: str
    confidence: Optional[float] = None
    confidence_is_calibrated: bool = False
    needs_review: bool = False
    uncertainty_reason: Optional[str] = None
    line_index: Optional[int] = None
    box: Optional[List[int]] = None

    # Medication-specific fields (populated only when field_type == MEDICATION_ORDER)
    name: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentRecognitionResult(BaseModel):
    """
    Aggregated document recognition and entity classification output.
    Separates genuine medication orders from clinical context (vitals, symptoms, advice).
    """
    items: List[DocumentItem] = Field(default_factory=list)
    hospital_details: List[str] = Field(default_factory=list)
    patient_details: Dict[str, Any] = Field(default_factory=dict)
    date: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    diagnosis: List[str] = Field(default_factory=list)
    vitals: List[str] = Field(default_factory=list)
    medications: List[DocumentItem] = Field(default_factory=list)
    non_medication_treatments: List[DocumentItem] = Field(default_factory=list)
    general_advice: List[str] = Field(default_factory=list)
    uncertain_items: List[DocumentItem] = Field(default_factory=list)

    provider_used: str = "rapidocr"
    model_used: Optional[str] = None
    attempts: int = 1
    fallback_occurred: bool = False
    fallback_reason: Optional[str] = None
    source_type: str = "ocr_transcription_unverified"
    processing_status: str = "needs_review"
    warnings: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @property
    def provider_name(self) -> str:
        return self.provider_used

    @property
    def fallback_used(self) -> bool:
        return self.fallback_occurred
