"""
Unit tests for Worker Lease Heartbeat Mechanism.
"""
import uuid
import time
from datetime import timedelta
import pytest
from sqlalchemy.orm import Session, sessionmaker

from prescripto.db.base import utc_now, ensure_utc
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob
from prescripto.db.models.registry import ModelVersion
from prescripto.worker.queue import JobClaim
from prescripto.worker.heartbeat import HeartbeatManager
from prescripto.worker.exceptions import WorkerFencedError


@pytest.fixture
def heartbeat_claim(db_session: Session):
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
        lease_owner="worker-hb-test",
        lease_token=25,
        lease_expires_at=utc_now() + timedelta(minutes=5),
        heartbeat_at=utc_now(),
        retry_count=0,
        max_retries=3,
    )
    db_session.add(job)
    db_session.commit()

    claim = JobClaim(
        job_id=job.id,
        analysis_id=analysis.id,
        lease_token=25,
        lease_owner="worker-hb-test",
        lease_expires_at=job.lease_expires_at,
        retry_count=0,
        max_retries=3,
    )
    return {"job": job, "claim": claim}


def test_heartbeat_pulse_extends_lease(db_session: Session, heartbeat_claim):
    claim = heartbeat_claim["claim"]
    job = heartbeat_claim["job"]

    session_factory = lambda: db_session

    hb = HeartbeatManager(
        session_factory=session_factory,
        claim=claim,
        interval_seconds=10.0,
        lease_duration_seconds=900,
        close_session=False,
    )

    success = hb.pulse()
    assert success is True
    assert hb.is_fenced is False
    assert hb.last_heartbeat_time > 0

    db_session.refresh(job)
    assert ensure_utc(job.lease_expires_at) > utc_now() + timedelta(seconds=800)


def test_heartbeat_pulse_detects_fencing(db_session: Session, heartbeat_claim):
    claim = heartbeat_claim["claim"]
    job = heartbeat_claim["job"]

    # Invalidate lease by changing owner
    job.lease_owner = "another-worker"
    db_session.commit()

    session_factory = lambda: db_session

    hb = HeartbeatManager(
        session_factory=session_factory,
        claim=claim,
        interval_seconds=10.0,
        close_session=False,
    )

    success = hb.pulse()
    assert success is False
    assert hb.is_fenced is True

    with pytest.raises(WorkerFencedError):
        hb.check_fence()


def test_heartbeat_context_manager_lifecycle(db_session: Session, heartbeat_claim):
    claim = heartbeat_claim["claim"]
    session_factory = lambda: db_session

    with HeartbeatManager(
        session_factory=session_factory,
        claim=claim,
        interval_seconds=0.1,
        close_session=False,
    ) as hb:
        assert hb._thread is not None
        assert hb._thread.is_alive()
        time.sleep(0.2)
        assert hb.last_heartbeat_time > 0

    # After exit, thread should stop
    assert not hb._thread.is_alive()
