"""
Integration tests for Worker Engine, Pipeline Coordinator, and End-to-End Execution.
"""
import uuid
from io import BytesIO
from datetime import timedelta
import pytest
from sqlalchemy.orm import Session
from PIL import Image

from prescripto.db.base import utc_now
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob, AnalysisStage
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.users import User
from prescripto.worker.main import WorkerRunner
from prescripto.worker.coordinator import CANONICAL_STAGES
from prescripto.worker.exceptions import WorkerFencedError
from prescripto.worker.fence import commit_stage_result
from prescripto.ml.runtime import MockModelRuntime


@pytest.fixture
def seeded_worker_env(db_session: Session):
    user = User(
        id=uuid.uuid4(),
        username=f"we_{uuid.uuid4().hex[:8]}",
        email=f"we_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="test_password_hash",
        role="OPERATOR",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

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
        uploader_id=user.id,
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


class FakeStorage:
    def __init__(self, image_bytes: bytes):
        self.image_bytes = image_bytes

    def get_object(self, key: str) -> bytes:
        return self.image_bytes


def make_image_bytes() -> bytes:
    stream = BytesIO()
    img = Image.new("RGB", (800, 800), "white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((50, 100), "Augmentin 625 Duo 1 tab BD", fill="black")
    img.save(stream, format="PNG")
    return stream.getvalue()


from prescripto.worker.queue import QueuePoller

def test_worker_full_pipeline_success(db_session: Session, seeded_worker_env):
    analysis = seeded_worker_env["analysis"]
    job = seeded_worker_env["job"]

    image_bytes = make_image_bytes()
    seeded_worker_env["doc"].file_hash_sha256 = __import__("hashlib").sha256(image_bytes).hexdigest()
    session_factory = lambda: db_session

    runner = WorkerRunner(
        session_factory=session_factory,
        worker_id="integration-worker-1",
        poll_interval=0.1,
        lease_seconds=600,
        heartbeat_seconds=60,
        close_session=False,
        storage_client=FakeStorage(image_bytes),
        ocr_runtime=MockModelRuntime(model_version_id=analysis.model_snapshot_id),
    )

    processed = runner.run_once()
    assert processed is True

    # Verify job succeeded
    db_session.refresh(job)
    assert job.status == "SUCCEEDED"
    assert job.lease_token == 1
    assert job.retry_count == 0

    # Verify analysis finished in a terminal review state
    db_session.refresh(analysis)
    assert analysis.status in ["COMPLETED", "REQUIRES_REVIEW"]
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
    image_bytes = make_image_bytes()
    seeded_worker_env["doc"].file_hash_sha256 = __import__("hashlib").sha256(image_bytes).hexdigest()
    session_factory = lambda: db_session
    runner_b = WorkerRunner(
        session_factory=session_factory,
        worker_id="worker-B",
        close_session=False,
        storage_client=FakeStorage(image_bytes),
        ocr_runtime=MockModelRuntime(model_version_id=analysis.model_snapshot_id),
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


def test_failed_job_rolls_back_partial_stages(db_session: Session, seeded_worker_env):
    """
    B2 Regression Test:
    When a pipeline stage fails (e.g. OCR runtime crashes), any stages that
    were flushed prior to the failure (e.g. INGESTION, QUALITY_CHECK) must be
    rolled back by run_once(). Zero stage rows should persist for the failed attempt.
    """
    analysis = seeded_worker_env["analysis"]
    job = seeded_worker_env["job"]

    image_bytes = make_image_bytes()
    seeded_worker_env["doc"].file_hash_sha256 = __import__("hashlib").sha256(image_bytes).hexdigest()

    # Faulty OCR runtime that raises an exception mid-pipeline
    class CrashingOCRRuntime:
        def detect_and_recognize(self, image):
            raise RuntimeError("ocr model crashed mid-pipeline")

    session_factory = lambda: db_session

    runner = WorkerRunner(
        session_factory=session_factory,
        worker_id="crash-worker-1",
        poll_interval=0.1,
        lease_seconds=600,
        heartbeat_seconds=60,
        close_session=False,
        storage_client=FakeStorage(image_bytes),
        ocr_runtime=CrashingOCRRuntime(),
    )

    processed = runner.run_once()
    assert processed is True

    # Verify job was marked FAILED with retry_count incremented
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 1

    # B2 Guarantee: No half-finished stage rows must be committed!
    stages = (
        db_session.query(AnalysisStage)
        .filter(AnalysisStage.analysis_id == analysis.id)
        .all()
    )
    assert len(stages) == 0, f"Expected 0 persisted stages after mid-pipeline crash, got {len(stages)}"


def test_blank_image_requires_review(db_session: Session, seeded_worker_env):
    """
    T8.1: A blank image must fail the quality check and require clinical review.
    """
    analysis = seeded_worker_env["analysis"]
    job = seeded_worker_env["job"]

    blank_stream = BytesIO()
    Image.new("RGB", (800, 800), "white").save(blank_stream, format="PNG")
    blank_bytes = blank_stream.getvalue()

    seeded_worker_env["doc"].file_hash_sha256 = __import__("hashlib").sha256(blank_bytes).hexdigest()

    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="blank-test-worker",
        close_session=False,
        storage_client=FakeStorage(blank_bytes),
        ocr_runtime=MockModelRuntime(model_version_id=analysis.model_snapshot_id),
    )

    processed = runner.run_once()
    assert processed is True

    db_session.refresh(job)
    assert job.status == "SUCCEEDED"

    db_session.refresh(analysis)
    assert analysis.status == "REQUIRES_REVIEW"
    assert analysis.review_required is True
    assert any("QUALITY_TOO_LOW" in r for r in analysis.review_reasons)

