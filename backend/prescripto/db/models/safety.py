"""
Risk Finding Model with Safety Check Invariants.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Float, DateTime, CheckConstraint, ForeignKey,
    UniqueConstraint, JSON, ARRAY
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from prescripto.db.base import Base, utc_now


class RiskFinding(Base):
    __tablename__ = "risk_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_type: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "check_type IN ('DUPLICATE_MEDICATION', 'EVIDENCE_LOOKUP', 'ADVERSE_EFFECT')",
            name="chk_finding_check_type",
        ),
        nullable=False,
    )
    finding_key: Mapped[str] = mapped_column(String(255), nullable=False)
    finding_status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "finding_status IN ('CONFIRMED_BY_SOURCE', 'POTENTIAL', 'INSUFFICIENT_EVIDENCE', 'NOT_EVALUATED', 'REQUIRES_REVIEW')",
            name="chk_finding_status",
        ),
        nullable=False,
    )
    medication_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)).with_variant(JSON, "sqlite"), default=list, nullable=False
    )
    evidence_text: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_version: Mapped[str] = mapped_column(String(50), nullable=False)
    knowledge_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_snapshots.id"), nullable=True
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    check_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    not_evaluated_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    analysis = relationship("Analysis", backref="risk_findings")
    knowledge_snapshot = relationship("KnowledgeSnapshot")

    __table_args__ = (
        CheckConstraint(
            "finding_status != 'NOT_EVALUATED' OR not_evaluated_reason IS NOT NULL",
            name="chk_not_evaluated_reason",
        ),
        UniqueConstraint(
            "analysis_id", "check_type", "source_name", "finding_key",
            name="uq_finding_identity"
        ),
    )
