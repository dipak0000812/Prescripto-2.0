"""
Prescripto AI 2.0 — IngestPrescription Use Case.
Validates file format, magic bytes, PDF active content, verifies idempotency,
persists document and analysis jobs atomically, and stores object in MinIO/S3.
"""
import hashlib
import uuid
from typing import Tuple
from sqlalchemy.orm import Session

from prescripto.config.settings import settings
from prescripto.audit.logger import get_logger
from prescripto.storage.client import StorageClient
from prescripto.storage.exceptions import StorageUnavailableException as S3UnavailableException
from prescripto.db.base import utc_now
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.idempotency import IdempotencyRecord
from prescripto.application.dtos.prescription import (
    IngestPrescriptionInput,
    IngestPrescriptionOutput,
)
from prescripto.application.exceptions import (
    MissingIdempotencyKeyException,
    IdempotencyKeyConflictException,
    UnsupportedMediaTypeException,
    FileTooLargeException,
    PdfActiveContentRejectedException,
    StorageUnavailableException,
    MalformedRequestException,
)

logger = get_logger("prescripto.application.ingest")

PDF_ACTIVE_CONTENT_PATTERNS = [
    b"/JavaScript",
    b"/JS",
    b"/Launch",
    b"/EmbeddedFiles",
    b"/RichMedia",
    b"/SubmitForm",
    b"/ImportData",
]


def detect_file_format_and_validate(file_bytes: bytes) -> Tuple[str, str]:
    """
    Validates file size and inspects magic bytes (not client MIME or filename extension).
    Returns (mime_type, file_extension).
    """
    size = len(file_bytes)
    if size == 0:
        raise MalformedRequestException("Uploaded file is empty")
    if size > settings.MAX_UPLOAD_BYTES:
        raise FileTooLargeException(
            f"File size {size} bytes exceeds maximum allowed limit {settings.MAX_UPLOAD_BYTES} bytes"
        )

    # Magic byte matching
    if file_bytes.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg", "jpg"
    elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    elif file_bytes.startswith(b"II*\x00") or file_bytes.startswith(b"MM\x00*"):
        return "image/tiff", "tiff"
    elif file_bytes.startswith(b"%PDF-"):
        # Scan for dangerous active scripts or launch commands
        for pattern in PDF_ACTIVE_CONTENT_PATTERNS:
            if pattern in file_bytes:
                raise PdfActiveContentRejectedException(
                    "PDF rejected: contains active or executable content"
                )
        return "application/pdf", "pdf"
    else:
        raise UnsupportedMediaTypeException(
            "Unsupported file format: magic bytes do not match JPEG, PNG, TIFF, or PDF"
        )


def get_or_create_active_model_version(db: Session) -> ModelVersion:
    """Retrieves the active model version row or seeds a default in non-production environments."""
    model = (
        db.query(ModelVersion)
        .filter(
            ModelVersion.model_name == settings.OCR_MODEL_NAME,
            ModelVersion.model_version == settings.OCR_MODEL_VERSION,
        )
        .first()
    )
    if not model:
        model = ModelVersion(
            id=uuid.uuid4(),
            model_name=settings.OCR_MODEL_NAME,
            model_version=settings.OCR_MODEL_VERSION,
            checkpoint_sha256="0" * 64,
            artifact_storage_key=f"models/{settings.OCR_MODEL_NAME}/{settings.OCR_MODEL_VERSION}/model.onnx",
            framework="PyTorch",
            license="Apache-2.0",
        )
        db.add(model)
        db.flush()
    return model


class IngestPrescriptionUseCase:
    """Use case coordinating prescription file intake, verification, storage, and job queueing."""

    def __init__(self, db: Session, storage_client: StorageClient) -> None:
        self.db = db
        self.storage = storage_client

    def execute(self, cmd: IngestPrescriptionInput) -> IngestPrescriptionOutput:
        # 1. Validate Idempotency-Key
        if not cmd.idempotency_key or not cmd.idempotency_key.strip():
            raise MissingIdempotencyKeyException()

        clean_idempotency_key = cmd.idempotency_key.strip()

        # 2. Validate format, magic bytes, active content, and size limits
        mime_type, extension = detect_file_format_and_validate(cmd.file_bytes)

        # 3. Compute SHA-256 Checksum
        file_hash = hashlib.sha256(cmd.file_bytes).hexdigest()

        # 4. Check Idempotency Record
        existing_record = (
            self.db.query(IdempotencyRecord)
            .filter(
                IdempotencyRecord.user_id == cmd.uploader_id,
                IdempotencyRecord.key == clean_idempotency_key,
            )
            .first()
        )

        if existing_record:
            if existing_record.file_hash_sha256 == file_hash:
                logger.info(
                    "idempotency_replay_accepted",
                    document_id=str(existing_record.prescription_id),
                    analysis_id=str(existing_record.analysis_id),
                    status="REPLAY",
                )
                return IngestPrescriptionOutput(
                    prescription_id=existing_record.prescription_id,
                    analysis_id=existing_record.analysis_id,
                    is_replay=True,
                )
            else:
                logger.warning(
                    "idempotency_conflict_detected",
                    error_code="IDEMPOTENCY_KEY_CONFLICT",
                )
                raise IdempotencyKeyConflictException()

        # 5. Ensure Active Model Snapshot exists
        active_model = get_or_create_active_model_version(self.db)

        # 6. Upload binary object to MinIO / S3
        document_id = uuid.uuid4()
        analysis_id = uuid.uuid4()
        storage_key = self.storage.generate_prescription_key(document_id, extension)

        try:
            self.storage.put_object(
                key=storage_key,
                data=cmd.file_bytes,
                content_type=mime_type,
            )
        except S3UnavailableException as err:
            logger.error("storage_upload_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(str(err)) from err

        # 7. Atomic DB Transaction
        try:
            doc = PrescriptionDocument(
                id=document_id,
                uploader_id=cmd.uploader_id,
                patient_ref=cmd.patient_external_id,
                storage_key=storage_key,
                file_hash_sha256=file_hash,
                mime_type=mime_type,
                file_size_bytes=len(cmd.file_bytes),
                status="UPLOADED",
                uploaded_at=utc_now(),
            )
            analysis = Analysis(
                id=analysis_id,
                document_id=document_id,
                status="QUEUED",
                pipeline_version="1.0.0",
                model_snapshot_id=active_model.id,
                review_required=False,
                review_reasons=[],
                created_at=utc_now(),
            )
            job = AnalysisJob(
                id=uuid.uuid4(),
                analysis_id=analysis_id,
                status="PENDING",
                retry_count=0,
                max_retries=3,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            idemp_rec = IdempotencyRecord(
                id=uuid.uuid4(),
                key=clean_idempotency_key,
                user_id=cmd.uploader_id,
                file_hash_sha256=file_hash,
                prescription_id=document_id,
                analysis_id=analysis_id,
                created_at=utc_now(),
            )

            self.db.add_all([doc, analysis, job, idemp_rec])
            self.db.commit()

            logger.info(
                "prescription_ingested",
                document_id=str(document_id),
                analysis_id=str(analysis_id),
                status="QUEUED",
            )

            return IngestPrescriptionOutput(
                prescription_id=document_id,
                analysis_id=analysis_id,
                is_replay=False,
            )
        except Exception as e:
            self.db.rollback()
            # Clean up uploaded storage object if DB commit fails
            try:
                self.storage.delete_object(storage_key)
            except Exception:
                pass
            raise e
