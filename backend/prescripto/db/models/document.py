"""
Prescription Document Model.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, BigInteger, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from prescripto.db.base import Base, utc_now


class PrescriptionDocument(Base):
    __tablename__ = "prescription_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    patient_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "mime_type IN ('image/jpeg', 'image/png', 'image/tiff', 'application/pdf')",
            name="chk_prescription_mime_type",
        ),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 20971520",
            name="chk_prescription_file_size",
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "status IN ('UPLOAD_PENDING', 'UPLOADED', 'DELETION_REQUESTED', 'DELETION_IN_PROGRESS', 'DELETED')",
            name="chk_prescription_status",
        ),
        default="UPLOAD_PENDING",
        nullable=False,
        index=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    uploader = relationship("User", backref="prescriptions")
