"""
Unit test reproducing Bug 6: Scan Error Retry Endpoint.
Validates:
1. POST /analyses/{id}/retry on a FAILED analysis resets status to QUEUED, clears error_detail,
   resets/creates an AnalysisJob with status PENDING, and returns updated status.
2. POST /analyses/{id}/retry on a non-failed analysis (e.g. COMPLETED or PROCESSING) returns 409 Conflict.
3. User-friendly error message mapping in GetAnalysisStatusUseCase._user_facing_error.
"""
import uuid
import pytest
from fastapi import HTTPException

from prescripto.db.models.users import User
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.enums import Role
from prescripto.application.use_cases.get_analysis import GetAnalysisStatusUseCase
from prescripto.api.v1.routers.analyses import retry_analysis


@pytest.fixture
def default_model_version(db_session):
    mv = ModelVersion(
        id=uuid.uuid4(),
        model_name="extraction_model_retry",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key="models/extraction_model/1.0.0.onnx",
        framework="ONNX",
        license="MIT",
    )
    db_session.add(mv)
    db_session.commit()
    return mv


def test_user_facing_error_mapping():
    """Verify detailed technical failures map to patient-friendly explanations."""
    err_fn = GetAnalysisStatusUseCase._user_facing_error

    assert err_fn("Uploaded image cannot be decoded") == (
        "The uploaded file could not be decoded as a valid image. Please ensure you upload a clear JPEG, PNG, or WebP photo."
    )
    assert err_fn('Storage connection error: Connect timeout on endpoint URL: "http://localhost:9000/..."') == (
        "Storage service is temporarily unavailable. Click 'Try again' to retry processing."
    )
    assert err_fn("Analysis failed: lease expired and max retries exceeded") == (
        "Processing took longer than expected and timed out. Click 'Try again' to re-analyze."
    )


def test_retry_failed_analysis(db_session, default_model_version):
    """A failed analysis can be retried, which resets it to QUEUED and queues a job."""
    uploader = User(
        id=uuid.uuid4(),
        username="retry_user",
        email="retry@example.com",
        hashed_password="fakehash",
        role=Role.OPERATOR.value,
        is_active=True,
    )
    db_session.add(uploader)
    db_session.commit()

    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uploader.id,
        file_hash_sha256="223344556677889900aabbccddeeff11223344556677889900aabbccddeeff11",
        mime_type="image/jpeg",
        file_size_bytes=1024,
        status="UPLOADED",
    )
    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="FAILED",
        pipeline_version="1.0.0",
        model_snapshot_id=default_model_version.id,
        error_detail="Uploaded image cannot be decoded",
    )
    job = AnalysisJob(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        status="FAILED",
        retry_count=3,
        last_error="Image corrupted",
    )
    db_session.add_all([doc, analysis, job])
    db_session.commit()

    # Call retry endpoint
    status_res = retry_analysis(
        id=analysis.id,
        current_user=uploader,
        db=db_session,
    )

    assert status_res.status == "QUEUED"
    assert status_res.error_message is None

    # Verify DB state
    db_session.refresh(analysis)
    assert analysis.status == "QUEUED"
    assert analysis.error_detail is None

    db_session.refresh(job)
    assert job.status == "PENDING"
    assert job.retry_count == 0


def test_retry_non_failed_analysis_returns_409(db_session, default_model_version):
    """An analysis that is not FAILED (e.g. COMPLETED or PROCESSING) cannot be retried."""
    uploader = User(
        id=uuid.uuid4(),
        username="retry_user_2",
        email="retry2@example.com",
        hashed_password="fakehash",
        role=Role.OPERATOR.value,
        is_active=True,
    )
    db_session.add(uploader)
    db_session.commit()

    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uploader.id,
        file_hash_sha256="3344556677889900aabbccddeeff11223344556677889900aabbccddeeff1122",
        mime_type="image/jpeg",
        file_size_bytes=1024,
        status="UPLOADED",
    )
    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="PROCESSING",
        pipeline_version="1.0.0",
        model_snapshot_id=default_model_version.id,
    )
    db_session.add_all([doc, analysis])
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        retry_analysis(
            id=analysis.id,
            current_user=uploader,
            db=db_session,
        )
    assert exc_info.value.status_code == 409

