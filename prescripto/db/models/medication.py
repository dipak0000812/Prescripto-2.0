"""
Medication Master, PrescriptionMedication (with C-3 Fix), and MedicationCandidate Models.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    String, Float, Integer, DateTime, CheckConstraint, ForeignKey,
    UniqueConstraint, Index, JSON, ARRAY
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from prescripto.db.base import Base, utc_now


FIELD_STATE_CHECK = "('CLEAR', 'AMBIGUOUS', 'UNREADABLE', 'NOT_PRESENT')"


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    generic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    active_ingredients: Mapped[List[str]] = mapped_column(
        ARRAY(String).with_variant(JSON, "sqlite"), nullable=False
    )
    strength: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dosage_form: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    route: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rxnorm_cui: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_class: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "source_class IN ('CDSCO_REGULATORY', 'RXNORM', 'MANUFACTURER_VERIFIED', 'RESEARCH_VOCABULARY', 'MANUAL_EXPERT')",
            name="chk_medication_source_class",
        ),
        nullable=False,
    )
    source_version: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "verification_status IN ('VERIFIED_AUTHORITY', 'PROVISIONAL', 'EXPERT_CONFIRMED', 'UNVERIFIED')",
            name="chk_medication_verification_status",
        ),
        default="UNVERIFIED",
        nullable=False,
    )
    provenance_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "brand_name", "generic_name", "strength", "dosage_form", "route",
            name="uq_medication_identity"
        ),
    )


class PrescriptionMedication(Base):
    __tablename__ = "prescription_medications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # 1. Name
    name_raw: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_state: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(f"name_state IN {FIELD_STATE_CHECK}", name="chk_name_state"),
        default="NOT_PRESENT",
        nullable=False,
    )
    name_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 2. Strength
    strength_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    strength_state: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(f"strength_state IN {FIELD_STATE_CHECK}", name="chk_strength_state"),
        default="NOT_PRESENT",
        nullable=False,
    )
    strength_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 3. Dose
    dose_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dose_state: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(f"dose_state IN {FIELD_STATE_CHECK}", name="chk_dose_state"),
        default="NOT_PRESENT",
        nullable=False,
    )
    dose_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 4. Unit (C-3 Fix)
    unit_raw: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    unit_state: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(f"unit_state IN {FIELD_STATE_CHECK}", name="chk_unit_state"),
        default="NOT_PRESENT",
        nullable=False,
    )
    unit_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 5. Frequency
    frequency_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency_state: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(f"frequency_state IN {FIELD_STATE_CHECK}", name="chk_frequency_state"),
        default="NOT_PRESENT",
        nullable=False,
    )
    frequency_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 6. Route
    route_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    route_state: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(f"route_state IN {FIELD_STATE_CHECK}", name="chk_route_state"),
        default="NOT_PRESENT",
        nullable=False,
    )
    route_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 7. Duration
    duration_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration_state: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(f"duration_state IN {FIELD_STATE_CHECK}", name="chk_duration_state"),
        default="NOT_PRESENT",
        nullable=False,
    )
    duration_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 8. Instructions (C-3 Fix)
    instructions_raw: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    instructions_state: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(f"instructions_state IN {FIELD_STATE_CHECK}", name="chk_instructions_state"),
        default="NOT_PRESENT",
        nullable=False,
    )
    instructions_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    analysis = relationship("Analysis", backref="prescription_medications")

    __table_args__ = (
        UniqueConstraint("analysis_id", "line_index", name="uq_prescription_med_line"),
    )


class MedicationCandidate(Base):
    __tablename__ = "medication_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prescription_med_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescription_medications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    extracted_text: Mapped[str] = mapped_column(String(255), nullable=False)
    matching_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    candidate_score: Mapped[float] = mapped_column(Float, nullable=False)
    source_vocabulary: Mapped[str] = mapped_column(String(100), nullable=False)
    resolved_medication_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medications.id"), nullable=True
    )
    resolution_status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "resolution_status IN ('RESOLVED', 'UNRESOLVED', 'AMBIGUOUS')",
            name="chk_candidate_resolution_status",
        ),
        nullable=False,
    )

    prescription_medication = relationship("PrescriptionMedication", backref="candidates")
    resolved_medication = relationship("Medication")

    __table_args__ = (
        UniqueConstraint(
            "prescription_med_id", "matching_strategy", "source_vocabulary",
            name="uq_candidate_strategy_vocab"
        ),
    )
