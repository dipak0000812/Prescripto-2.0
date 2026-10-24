"""
Prescripto AI 2.0 — Pure Domain Prescription Models.
Strict Layering: Zero external dependencies (no FastAPI, no SQLAlchemy, no Boto3).
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from prescripto.domain.prescription.exceptions import (
    FileSizeExceededException,
    InvalidDocumentStateException,
    UnsupportedMediaFormatException,
)

MAX_PRESCRIPTION_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


class DocumentStatus(str, Enum):
    UPLOAD_PENDING = "UPLOAD_PENDING"
    UPLOADED = "UPLOADED"
    DELETION_REQUESTED = "DELETION_REQUESTED"
    DELETION_IN_PROGRESS = "DELETION_IN_PROGRESS"
    DELETED = "DELETED"


class AllowedMimeType(str, Enum):
    JPEG = "image/jpeg"
    PNG = "image/png"
    TIFF = "image/tiff"
    PDF = "application/pdf"


@dataclass
class PrescriptionDocument:
    """Pure domain entity representing a prescription document."""
    id: uuid.UUID
    uploader_id: uuid.UUID
    file_hash_sha256: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus = DocumentStatus.UPLOAD_PENDING
    storage_key: Optional[str] = None
    patient_ref: Optional[str] = None
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Enforces domain invariants on prescription documents."""
        if self.file_size_bytes <= 0:
            raise FileSizeExceededException("File size must be greater than zero bytes.")
        if self.file_size_bytes > MAX_PRESCRIPTION_FILE_SIZE_BYTES:
            raise FileSizeExceededException(
                f"File size {self.file_size_bytes} exceeds maximum allowable size {MAX_PRESCRIPTION_FILE_SIZE_BYTES}."
            )
        allowed_mimes = {m.value for m in AllowedMimeType}
        if self.mime_type not in allowed_mimes:
            raise UnsupportedMediaFormatException(
                f"MIME type '{self.mime_type}' is not supported. Permitted: {', '.join(allowed_mimes)}"
            )

    def mark_uploaded(self, storage_key: str) -> None:
        """Transition from UPLOAD_PENDING to UPLOADED once storage write confirms."""
        if self.status != DocumentStatus.UPLOAD_PENDING:
            raise InvalidDocumentStateException(
                f"Cannot mark uploaded from status '{self.status.value}'"
            )
        if not storage_key:
            raise ValueError("storage_key cannot be empty when marking uploaded.")
        self.storage_key = storage_key
        self.status = DocumentStatus.UPLOADED

    def request_deletion(self) -> None:
        """Transition to DELETION_REQUESTED for DPDPA tombstoning."""
        if self.status in (DocumentStatus.DELETED, DocumentStatus.DELETION_IN_PROGRESS):
            raise InvalidDocumentStateException(
                f"Document is already in deletion state: '{self.status.value}'"
            )
        self.status = DocumentStatus.DELETION_REQUESTED

    @property
    def can_generate_presigned_url(self) -> bool:
        """Determines if an ephemeral presigned GET URL may be generated for this document."""
        return (
            self.status == DocumentStatus.UPLOADED
            and self.storage_key is not None
            and self.deleted_at is None
        )
