"""
Deletion Jobs and Token Blocklist Models.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Boolean, Integer, DateTime, CheckConstraint, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from prescripto.db.base import Base, utc_now


class DeletionJob(Base):
    __tablename__ = "deletion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prescription_documents.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "status IN ('REQUESTED', 'DB_TOMBSTONED', 'STORAGE_DELETING', 'VERIFYING', 'COMPLETE', 'PARTIAL_FAILURE')",
            name="chk_deletion_job_status",
        ),
        default="REQUESTED",
        nullable=False,
        index=True,
    )
    manifest_written: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_detail: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    document = relationship("PrescriptionDocument")


class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    jti: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    user = relationship("User")

    __table_args__ = (
        Index("idx_token_blocklist_expiry", "expires_at"),
    )
