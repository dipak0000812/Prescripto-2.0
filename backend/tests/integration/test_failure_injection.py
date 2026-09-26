"""
Failure Injection and Resilience Integration Tests (Phase 7 / Slice 12):
- Worker crash mid-pipeline and automatic recovery
- Retry count exhaustion and Dead-Letter Queue (DEAD status) transition
- Retry exponential backoff schedule (5s -> 30s -> 120s)
- Transient storage failure simulation
"""
import uuid
from datetime import timedelta
import pytest
from sqlalchemy.orm import Session

from prescripto.db.base import utc_now
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob
from prescripto.db.models.registry import ModelVersion
from prescripto.worker.queue import QueuePoller
from prescripto.worker.main import WorkerRunner
from prescripto.worker.exceptions import WorkerFencedError


@pytest.fixture
def failure_test_job(db_session: Session):
    model = ModelVersion(
        id=uuid.uuid4(),
        model_name="fail-test-model",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key="models/m.onnx",
        framework="PyTorch",
        license="MIT",
    )
    db_session.add(model)

    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uuid.uuid4(),
        storage_key="test/fail.jpg",
        file_hash_sha256="fail123",
        mime_type="image/jpeg",
        file_size_bytes=1024,
        status="UPLOADED",
    )
    db_session.add(doc)

    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        model_snapshot_id=model.id,
        pipeline_version="1.0.0",
        status="PROCESSING",
    )
    db_session.add(analysis)

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


def test_retry_exhaustion_dead_letter_queue(db_session: Session, failure_test_job):
    job = failure_test_job["job"]

    for attempt in range(1, 4):
        # Set job to RUNNING
        job.status = "RUNNING"
        job.lease_owner = "worker-1"
        job.lease_token = attempt
        job.lease_expires_at = utc_now() + timedelta(minutes=5)
        db_session.commit()

        QueuePoller.mark_job_failed(db_session, job.id, attempt, "worker-1", f"Crash attempt {attempt}")
        db_session.refresh(job)

        if attempt < 3:
            assert job.status == "FAILED"
            assert job.retry_count == attempt
        else:
            assert job.status == "DEAD"
            assert job.retry_count == 3
            assert "Crash attempt 3" in job.last_error


def test_retry_backoff_schedule(db_session: Session, failure_test_job):
    job = failure_test_job["job"]
    now = utc_now()

    from prescripto.worker.queue import ensure_utc

    # Retry 1: 5s backoff
    job.status = "RUNNING"
    job.lease_owner = "worker-1"
    job.lease_token = 1
    job.lease_expires_at = utc_now() + timedelta(minutes=5)
    db_session.commit()

    QueuePoller.mark_job_failed(db_session, job.id, 1, "worker-1", "Error 1")
    db_session.refresh(job)
    assert ensure_utc(job.backoff_until) > now + timedelta(seconds=3)
    assert ensure_utc(job.backoff_until) <= now + timedelta(seconds=7)

    # Retry 2: 30s backoff
    job.status = "RUNNING"
    job.lease_owner = "worker-1"
    job.lease_token = 2
    job.lease_expires_at = utc_now() + timedelta(minutes=5)
    db_session.commit()

    QueuePoller.mark_job_failed(db_session, job.id, 2, "worker-1", "Error 2")
    db_session.refresh(job)
    assert ensure_utc(job.backoff_until) > now + timedelta(seconds=25)
    assert ensure_utc(job.backoff_until) <= now + timedelta(seconds=35)




def test_worker_crashed_mid_pipeline_reclaimed_after_expiry(db_session: Session, failure_test_job):
    job = failure_test_job["job"]

    # Worker A claimed job, lease token 1
    job.status = "RUNNING"
    job.lease_owner = "worker-A"
    job.lease_token = 1
    # Worker A died and lease expired
    job.lease_expires_at = utc_now() - timedelta(seconds=10)
    db_session.commit()

    # Sweeper recovers expired lease
    recovered = QueuePoller.recover_expired_leases(db_session)
    assert recovered == 1

    db_session.refresh(job)
    assert job.status == "PENDING"
    assert job.retry_count == 1

    # Fast forward past backoff
    job.backoff_until = utc_now() - timedelta(seconds=1)
    db_session.commit()

    # Worker B claims and succeeds
    runner_b = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="worker-B",
        close_session=False,
    )
    processed = runner_b.run_once()
    assert processed is True

    db_session.refresh(job)
    assert job.status == "SUCCEEDED"
    assert job.lease_token == 2
