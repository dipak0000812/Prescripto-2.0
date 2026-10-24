"""
Unit tests for pure domain prescription and analysis models.
Ensures zero external dependencies and enforces domain invariants.
"""
import uuid
from datetime import datetime, timezone
import pytest

from prescripto.domain.prescription.models import (
    PrescriptionDocument,
    DocumentStatus,
    AllowedMimeType,
    MAX_PRESCRIPTION_FILE_SIZE_BYTES,
)
from prescripto.domain.prescription.exceptions import (
    FileSizeExceededException,
    UnsupportedMediaFormatException,
    InvalidDocumentStateException,
)
from prescripto.domain.analysis.models import (
    Analysis,
    AnalysisStatus,
    JobStatus,
)


def test_prescription_document_creation_valid():
    doc_id = uuid.uuid4()
    uploader_id = uuid.uuid4()
    doc = PrescriptionDocument(
        id=doc_id,
        uploader_id=uploader_id,
        file_hash_sha256="a" * 64,
        mime_type="image/jpeg",
        file_size_bytes=1024,
    )
    assert doc.id == doc_id
    assert doc.status == DocumentStatus.UPLOAD_PENDING
    assert doc.storage_key is None
    assert not doc.can_generate_presigned_url


def test_prescription_document_mark_uploaded():
    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uuid.uuid4(),
        file_hash_sha256="b" * 64,
        mime_type="image/png",
        file_size_bytes=2048,
    )
    doc.mark_uploaded("prescriptions/test/original.png")
    assert doc.status == DocumentStatus.UPLOADED
    assert doc.storage_key == "prescriptions/test/original.png"
    assert doc.can_generate_presigned_url

    # Attempting to mark uploaded again must fail
    with pytest.raises(InvalidDocumentStateException):
        doc.mark_uploaded("another_key")


def test_prescription_document_file_size_exceeded():
    with pytest.raises(FileSizeExceededException):
        PrescriptionDocument(
            id=uuid.uuid4(),
            uploader_id=uuid.uuid4(),
            file_hash_sha256="c" * 64,
            mime_type="image/jpeg",
            file_size_bytes=MAX_PRESCRIPTION_FILE_SIZE_BYTES + 1,
        )


def test_prescription_document_zero_file_size():
    with pytest.raises(FileSizeExceededException):
        PrescriptionDocument(
            id=uuid.uuid4(),
            uploader_id=uuid.uuid4(),
            file_hash_sha256="d" * 64,
            mime_type="image/jpeg",
            file_size_bytes=0,
        )


def test_prescription_document_unsupported_mime():
    with pytest.raises(UnsupportedMediaFormatException):
        PrescriptionDocument(
            id=uuid.uuid4(),
            uploader_id=uuid.uuid4(),
            file_hash_sha256="e" * 64,
            mime_type="application/octet-stream",
            file_size_bytes=1024,
        )


def test_prescription_document_deletion_lifecycle():
    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uuid.uuid4(),
        file_hash_sha256="f" * 64,
        mime_type="image/tiff",
        file_size_bytes=4096,
    )
    doc.mark_uploaded("key")
    assert doc.can_generate_presigned_url

    doc.request_deletion()
    assert doc.status == DocumentStatus.DELETION_REQUESTED
    # Once deletion requested or in progress, presigned URL should be denied
    assert not doc.can_generate_presigned_url


def test_analysis_domain_model():
    analysis_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    model_id = uuid.uuid4()

    analysis = Analysis(
        id=analysis_id,
        document_id=doc_id,
        model_snapshot_id=model_id,
        pipeline_version="1.0.0",
    )
    assert analysis.status == AnalysisStatus.QUEUED
    assert not analysis.is_finished()
    assert not analysis.is_reviewable()

    analysis.status = AnalysisStatus.REQUIRES_REVIEW
    assert analysis.is_finished()
    assert analysis.is_reviewable()

    analysis.status = AnalysisStatus.COMPLETED
    assert analysis.is_finished()
    assert not analysis.is_reviewable()
