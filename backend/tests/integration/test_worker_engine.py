"""
Integration tests for Worker Engine, Pipeline Coordinator, and End-to-End Execution.
"""
import uuid
from datetime import timedelta
import pytest
from sqlalchemy.orm import Session

from prescripto.db.base import utc_now
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob, AnalysisStage
from prescripto.db.models.registry import ModelVersion
from prescripto.worker.main import WorkerRunner
from prescripto.worker.coordinator import CANONICAL_STAGES
from prescripto.worker.exceptions import WorkerFencedError
from prescripto.worker.fence import commit_stage_result


@pytest.fixture
def seeded_worker_env(db_session: Session):
    model = ModelVersion(
        id=uuid.uuid4(),
        model_name="trocr-handwritten-v1",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key="models/model.onnx",
        framework="PyTorch",
        license="Apache-2.0",
    )
    db_session.add(model)
    db_session.flush()

    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uuid.uuid4(),
        storage_key="prescriptions/doc-1/original.jpg",
        file_hash_sha256="hashsha256demo",
        mime_type="image/jpeg",
        file_size_bytes=2048,
        status="UPLOADED",
    )
    db_session.add(doc)
    db_session.flush()

    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="QUEUED",
        pipeline_version="1.0.0",
        model_snapshot_id=model.id,
    )
    db_session.add(analysis)
    db_session.flush()

    job = AnalysisJob(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        status="PENDING",
        lease_token=0,
        retry_count=0,
        max_retries=3,
    )
    db_session.add(job)
    db_session.commit()

    return {"doc": doc, "analysis": analysis, "job": job}


from prescripto.worker.queue import QueuePoller

def test_worker_full_pipeline_success(db_session: Session, seeded_worker_env):
    analysis = seeded_worker_env["analysis"]
    job = seeded_worker_env["job"]

    session_factory = lambda: db_session

    runner = WorkerRunner(
        session_factory=session_factory,
        worker_id="integration-worker-1",
        poll_interval=0.1,
        lease_seconds=600,
        heartbeat_seconds=60,
        close_session=False,
    )

    processed = runner.run_once()
    assert processed is True

    # Verify job succeeded
    db_session.refresh(job)
    assert job.status == "SUCCEEDED"
    assert job.lease_token == 1
    assert job.retry_count == 0

    # Verify analysis completed
    db_session.refresh(analysis)
    assert analysis.status == "COMPLETED"
    assert analysis.started_at is not None
    assert analysis.completed_at is not None

    # Verify all 8 stages were committed
    stages = (
        db_session.query(AnalysisStage)
        .filter(AnalysisStage.analysis_id == analysis.id)
        .all()
    )
    assert len(stages) == len(CANONICAL_STAGES)
    stage_names = [s.stage_name for s in stages]
    for expected_stage in CANONICAL_STAGES:
        assert expected_stage in stage_names


def test_worker_fencing_race_condition(db_session: Session, seeded_worker_env):
    analysis = seeded_worker_env["analysis"]
    job = seeded_worker_env["job"]

    # Simulate Worker A claiming the job with token 1
    job.status = "RUNNING"
    job.lease_owner = "worker-A"
    job.lease_token = 1
    job.lease_expires_at = utc_now() - timedelta(seconds=1)  # expired
    db_session.commit()

    # Recover expired lease (sweeper)
    recovered = QueuePoller.recover_expired_leases(db_session)
    assert recovered == 1
    db_session.refresh(job)
    assert job.status == "PENDING"
    assert job.retry_count == 1

    # Fast forward past backoff so Worker B can claim it immediately
    job.backoff_until = utc_now() - timedelta(seconds=1)
    db_session.commit()

    # Worker B claims expired job with token 2
    session_factory = lambda: db_session
    runner_b = WorkerRunner(
        session_factory=session_factory,
        worker_id="worker-B",
        close_session=False,
    )
    processed_b = runner_b.run_once()
    assert processed_b is True

    # Verify Worker B completed the job with token 2
    db_session.refresh(job)
    assert job.lease_token == 2
    assert job.status == "SUCCEEDED"

    # Now if Worker A attempts to commit a stage with stale token 1, it must be rejected
    with pytest.raises(WorkerFencedError):
        commit_stage_result(
            db=db_session,
            analysis_id=analysis.id,
            stage_name="REPORT_ASSEMBLY",
            lease_token=1,  # Stale token from Worker A
            lease_owner="worker-A",
            output={"fake": "data"},
        )
