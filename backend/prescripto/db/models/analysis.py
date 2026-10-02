"""
Analysis, AnalysisJob, and AnalysisStage Models.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    String, Boolean, Integer, BigInteger, DateTime, CheckConstraint,
    ForeignKey, UniqueConstraint, Index, JSON, ARRAY
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from prescripto.db.base import Base, utc_now


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prescription_documents.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'REQUIRES_REVIEW', "
            "'REVIEWING', 'REVIEWED_COMPLETE', 'REVIEWED_ESCALATED', 'FAILED')",
            name="chk_analysis_status",
        ),
        default="QUEUED",
        nullable=False,
        index=True,
    )
    pipeline_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False, index=True
    )
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_reasons: Mapped[List[str]] = mapped_column(
        ARRAY(String).with_variant(JSON, "sqlite"), default=list, nullable=False
    )
    error_detail: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    document = relationship("PrescriptionDocument", backref="analyses")
    model_version = relationship("ModelVersion")

    __table_args__ = (
        Index("idx_analyses_doc_status", "document_id", "status"),
    )


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "status IN ('PENDING', 'CLAIMED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'DEAD', 'CANCELLED')",
            name="chk_job_status",
        ),
        default="PENDING",
        nullable=False,
        index=True,
    )
    lease_owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lease_token: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    lease_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    backoff_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    analysis = relationship("Analysis", backref="jobs")

    __table_args__ = (
        Index(
            "idx_analysis_jobs_claimable",
            "status",
            "backoff_until",
            "created_at",
            postgresql_where="status IN ('PENDING', 'FAILED')",
        ),
    )


class AnalysisStage(Base):
    __tablename__ = "analysis_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False, index=True
    )
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    lease_token: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "status IN ('RUNNING', 'COMPLETED', 'FAILED', 'SKIPPED')",
            name="chk_stage_status",
        ),
        default="RUNNING",
        nullable=False,
    )
    output_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    analysis = relationship("Analysis", backref="stages")

    __table_args__ = (
        UniqueConstraint("analysis_id", "stage_name", name="uq_analysis_stage"),
    )
