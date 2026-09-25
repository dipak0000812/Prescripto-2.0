"""
Unit tests for Atomic Generation Fencing and Stage Result Persistence.
"""
import uuid
from datetime import timedelta
import pytest
from sqlalchemy.orm import Session

from prescripto.db.base import utc_now
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob, AnalysisStage
from prescripto.db.models.registry import ModelVersion
from prescripto.worker.fence import commit_stage_result
from prescripto.worker.exceptions import WorkerFencedError


@pytest.fixture
def sample_analysis_job(db_session: Session):
    model = ModelVersion(
        id=uuid.uuid4(),
        model_name="test-model",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key="test/model.onnx",
        framework="PyTorch",
        license="Apache-2.0",
    )
    db_session.add(model)
    db_session.flush()

    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uuid.uuid4(),
        storage_key="test/original.jpg",
        file_hash_sha256="abc123hash",
        mime_type="image/jpeg",
        file_size_bytes=1024,
        status="UPLOADED",
    )
    db_session.add(doc)
    db_session.flush()

    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="PROCESSING",
        pipeline_version="1.0.0",
        model_snapshot_id=model.id,
    )
    db_session.add(analysis)
    db_session.flush()

    job = AnalysisJob(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        status="RUNNING",
        lease_owner="worker-alpha",
        lease_token=10,
        lease_expires_at=utc_now() + timedelta(minutes=10),
        heartbeat_at=utc_now(),
        retry_count=0,
        max_retries=3,
    )
    db_session.add(job)
    db_session.commit()

    return {"doc": doc, "analysis": analysis, "job": job}


def test_commit_stage_result_success(db_session: Session, sample_analysis_job):
    analysis = sample_analysis_job["analysis"]
    output = {"confidence": 0.95, "lines": ["Paracetamol 500mg"]}

    stage = commit_stage_result(
        db=db_session,
        analysis_id=analysis.id,
        stage_name="OCR_RECOGNITION",
        lease_token=10,
        lease_owner="worker-alpha",
        output=output,
    )
    db_session.commit()

    assert stage.id is not None
    assert stage.stage_name == "OCR_RECOGNITION"
    assert stage.lease_token == 10
    assert stage.status == "COMPLETED"
    assert stage.output_json == output

    # Verify persisted in database
    db_stage = (
        db_session.query(AnalysisStage)
        .filter(AnalysisStage.analysis_id == analysis.id, AnalysisStage.stage_name == "OCR_RECOGNITION")
        .first()
    )
    assert db_stage is not None
    assert db_stage.output_json == output


def test_commit_stage_result_rejects_expired_lease(db_session: Session, sample_analysis_job):
    analysis = sample_analysis_job["analysis"]
    job = sample_analysis_job["job"]

    # Expire the lease
    job.lease_expires_at = utc_now() - timedelta(seconds=1)
    db_session.commit()

    with pytest.raises(WorkerFencedError) as exc_info:
        commit_stage_result(
            db=db_session,
            analysis_id=analysis.id,
            stage_name="OCR_RECOGNITION",
            lease_token=10,
            lease_owner="worker-alpha",
            output={"data": "test"},
        )
    assert "lease expired" in str(exc_info.value)


def test_commit_stage_result_rejects_owner_mismatch(db_session: Session, sample_analysis_job):
    analysis = sample_analysis_job["analysis"]

    with pytest.raises(WorkerFencedError) as exc_info:
        commit_stage_result(
            db=db_session,
            analysis_id=analysis.id,
            stage_name="OCR_RECOGNITION",
            lease_token=10,
            lease_owner="worker-imposter",
            output={"data": "test"},
        )
    assert "no active RUNNING lease" in str(exc_info.value)


def test_commit_stage_result_rejects_token_mismatch(db_session: Session, sample_analysis_job):
    analysis = sample_analysis_job["analysis"]

    with pytest.raises(WorkerFencedError) as exc_info:
        commit_stage_result(
            db=db_session,
            analysis_id=analysis.id,
            stage_name="OCR_RECOGNITION",
            lease_token=9,  # Stale token
            lease_owner="worker-alpha",
            output={"data": "test"},
        )
    assert "no active RUNNING lease" in str(exc_info.value)


def test_commit_stage_result_rejects_stale_generation_on_existing_stage(
    db_session: Session, sample_analysis_job
):
    analysis = sample_analysis_job["analysis"]

    # Stage already committed by generation 12
    prior_stage = AnalysisStage(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        stage_name="QUALITY_CHECK",
        lease_token=12,
        status="COMPLETED",
        output_json={"dpi": 300},
    )
    db_session.add(prior_stage)
    db_session.commit()

    # Worker with token 10 attempts to write to the same stage
    with pytest.raises(WorkerFencedError) as exc_info:
        commit_stage_result(
            db=db_session,
            analysis_id=analysis.id,
            stage_name="QUALITY_CHECK",
            lease_token=10,
            lease_owner="worker-alpha",
            output={"dpi": 200},
        )
    assert "newer stage generation already committed" in str(exc_info.value)
