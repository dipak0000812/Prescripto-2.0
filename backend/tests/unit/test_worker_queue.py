"""
Unit tests for Transactional Queue Poller, Lease Tokens, and Retries.
"""
import uuid
from datetime import timedelta
import pytest
from sqlalchemy.orm import Session

from prescripto.db.base import utc_now
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob
from prescripto.db.models.registry import ModelVersion
from prescripto.worker.queue import QueuePoller, compute_backoff_delay
from prescripto.worker.exceptions import WorkerFencedError


@pytest.fixture
def queue_fixture(db_session: Session):
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
        storage_key="test/doc.jpg",
        file_hash_sha256="hash123",
        mime_type="image/jpeg",
        file_size_bytes=100,
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
        lease_token=5,
        retry_count=0,
        max_retries=3,
    )
    db_session.add(job)
    db_session.commit()

    return {"doc": doc, "analysis": analysis, "job": job}


def test_claim_next_job_success(db_session: Session, queue_fixture):
    job = queue_fixture["job"]
    analysis = queue_fixture["analysis"]

    claim = QueuePoller.claim_next_job(
        db=db_session,
        worker_id="worker-node-1",
        lease_duration=timedelta(minutes=10),
    )

    assert claim is not None
    assert claim.job_id == job.id
    assert claim.analysis_id == analysis.id
    assert claim.lease_owner == "worker-node-1"
    assert claim.lease_token == 6  # 5 + 1
    assert claim.lease_expires_at > utc_now()

    # Verify DB update
    db_session.refresh(job)
    assert job.status == "RUNNING"
    assert job.lease_owner == "worker-node-1"
    assert job.lease_token == 6

    db_session.refresh(analysis)
    assert analysis.status == "PROCESSING"


def test_claim_next_job_skips_when_no_jobs(db_session: Session):
    claim = QueuePoller.claim_next_job(db=db_session, worker_id="worker-empty")
    assert claim is None


def test_claim_next_job_respects_backoff(db_session: Session, queue_fixture):
    job = queue_fixture["job"]
    job.status = "FAILED"
    job.retry_count = 1
    job.backoff_until = utc_now() + timedelta(minutes=5)
    db_session.commit()

    claim = QueuePoller.claim_next_job(db=db_session, worker_id="worker-test")
    assert claim is None


def test_renew_lease_success_and_fenced(db_session: Session, queue_fixture):
    claim = QueuePoller.claim_next_job(db=db_session, worker_id="worker-renew")
    assert claim is not None

    # Valid renewal
    renewed = QueuePoller.renew_lease(
        db=db_session,
        job_id=claim.job_id,
        lease_token=claim.lease_token,
        worker_id=claim.lease_owner,
        lease_duration=timedelta(minutes=15),
    )
    assert renewed is True

    # Attempt with stale token
    renewed_stale = QueuePoller.renew_lease(
        db=db_session,
        job_id=claim.job_id,
        lease_token=claim.lease_token - 1,
        worker_id=claim.lease_owner,
    )
    assert renewed_stale is False


def test_recover_expired_leases(db_session: Session, queue_fixture):
    job = queue_fixture["job"]
    job.status = "RUNNING"
    job.lease_owner = "dead-worker"
    job.lease_token = 10
    job.lease_expires_at = utc_now() - timedelta(minutes=2)
    job.retry_count = 0
    db_session.commit()

    recovered = QueuePoller.recover_expired_leases(db_session)
    assert recovered == 1

    db_session.refresh(job)
    assert job.status == "PENDING"
    assert job.retry_count == 1
    assert job.lease_owner is None
    assert job.backoff_until is not None


def test_recover_expired_leases_dead_letter_queue(db_session: Session, queue_fixture):
    job = queue_fixture["job"]
    analysis = queue_fixture["analysis"]
    job.status = "RUNNING"
    job.lease_owner = "crashed-worker"
    job.lease_token = 10
    job.lease_expires_at = utc_now() - timedelta(seconds=10)
    job.retry_count = 2
    job.max_retries = 3
    db_session.commit()

    recovered = QueuePoller.recover_expired_leases(db_session)
    assert recovered == 1

    db_session.refresh(job)
    assert job.status == "DEAD"
    assert job.retry_count == 3

    db_session.refresh(analysis)
    assert analysis.status == "FAILED"


def test_mark_job_succeeded(db_session: Session, queue_fixture):
    claim = QueuePoller.claim_next_job(db=db_session, worker_id="worker-success")
    assert claim is not None

    QueuePoller.mark_job_succeeded(
        db=db_session,
        job_id=claim.job_id,
        lease_token=claim.lease_token,
        worker_id=claim.lease_owner,
    )

    job = queue_fixture["job"]
    analysis = queue_fixture["analysis"]
    db_session.refresh(job)
    db_session.refresh(analysis)

    assert job.status == "SUCCEEDED"
    assert job.lease_owner is None
    assert analysis.status == "COMPLETED"


def test_mark_job_failed_backoff_and_dead_letter(db_session: Session, queue_fixture):
    claim = QueuePoller.claim_next_job(db=db_session, worker_id="worker-fail")
    assert claim is not None

    # 1st failure -> FAILED with backoff
    QueuePoller.mark_job_failed(
        db=db_session,
        job_id=claim.job_id,
        lease_token=claim.lease_token,
        worker_id=claim.lease_owner,
        error_message="Transient network glitch",
    )

    job = queue_fixture["job"]
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 1
    assert job.last_error == "Transient network glitch"
    assert job.backoff_until is not None

    # Exhaust retries: set retry_count to max_retries - 1 and fail again
    job.retry_count = 2
    job.status = "RUNNING"
    job.lease_owner = "worker-fail"
    job.lease_expires_at = utc_now() + timedelta(minutes=5)
    db_session.commit()

    QueuePoller.mark_job_failed(
        db=db_session,
        job_id=claim.job_id,
        lease_token=claim.lease_token,
        worker_id=claim.lease_owner,
        error_message="Permanent hardware crash",
    )

    db_session.refresh(job)
    assert job.status == "DEAD"
    assert job.retry_count == 3


def test_release_fenced_job_does_not_increment_retries(db_session: Session, queue_fixture):
    claim = QueuePoller.claim_next_job(db=db_session, worker_id="worker-fenced")
    assert claim is not None

    initial_retries = claim.retry_count

    QueuePoller.release_fenced_job(
        db=db_session,
        job_id=claim.job_id,
        worker_id="worker-fenced",
    )

    job = queue_fixture["job"]
    db_session.refresh(job)
    assert job.status == "PENDING"
    assert job.retry_count == initial_retries  # MUST NOT increment retry_count
    assert job.lease_owner is None


def test_compute_backoff_delay():
    assert compute_backoff_delay(0) == timedelta(seconds=5)
    assert compute_backoff_delay(1) == timedelta(seconds=30)
    assert compute_backoff_delay(2) == timedelta(minutes=2)
    assert compute_backoff_delay(10) == timedelta(minutes=2)
