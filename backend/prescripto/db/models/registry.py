"""
Model Versions, Calibration Snapshots, and Knowledge Snapshots.
"""
import uuid
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import String, Float, Integer, DateTime, CheckConstraint, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from prescripto.db.base import Base, utc_now


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    checkpoint_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    license: Mapped[str] = mapped_column(String(100), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("model_name", "model_version", name="uq_model_name_version"),
    )


class CalibrationSnapshot(Base):
    __tablename__ = "calibration_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False, index=True
    )
    calibration_dataset_ver: Mapped[str] = mapped_column(String(100), nullable=False)
    review_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    calibration_curve_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    model_version = relationship("ModelVersion", backref="calibration_snapshots")


class KnowledgeSnapshot(Base):
    __tablename__ = "knowledge_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_version: Mapped[str] = mapped_column(String(50), nullable=False)
    license_mode: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "license_mode IN ('COMMERCIAL_PERMISSIVE', 'RESEARCH_ONLY', 'PUBLIC_DOMAIN')",
            name="chk_knowledge_license_mode",
        ),
        nullable=False,
    )
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
