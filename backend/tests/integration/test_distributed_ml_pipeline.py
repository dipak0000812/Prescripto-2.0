"""
End-to-End Distributed Pipeline and Failure Mode Tests:
Backend <-> RemoteMLClient <-> ML Service (FastAPI :8001).

Validates the full distributed workflow:
  Real Image
     ↓
  Backend upload (POST /api/v1/prescriptions)
     ↓
  Job creation (AnalysisJob PENDING, Analysis QUEUED)
     ↓
  Worker (WorkerRunner)
     ↓
  RemoteMLClient
     ↓
  ML service (POST /v1/ocr/recognize)
     ↓
  Quality check + OCR + Calibration + Extraction
     ↓
  OCRLine response
     ↓
  Backend extraction / normalization
     ↓
  Database persistence (AnalysisStage, PrescriptionMedication)
     ↓
  API response (GET /api/v1/analyses/{id}/result)

Plus all 8 distributed failure modes:
  1. ML service unavailable (ConnectError)
  2. ML service returns HTTP 4xx/5xx (e.g. 502 Bad Gateway)
  3. ML request timeout (TimeoutException)
  4. Malformed ML response (invalid JSON / schema)
  5. Blank image (quality gate triggers clinical review)
  6. Unsupported / corrupt image (processing halted, job marked FAILED)
  7. Worker retry after ML failure (exponential backoff & recovery)
  8. Worker lease / fencing race condition around ML calls (stale worker rejected)
"""
import io
import sys
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import hashlib
import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

# Ensure repository root (containing ml/) is on sys.path
_REPO_ROOT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import ml.app.main as ml_main
from ml.tests.test_api import MockOCRRuntime

from prescripto.auth.crypto import create_access_token
from prescripto.db.base import utc_now
from prescripto.db.models.analysis import Analysis, AnalysisJob, AnalysisStage
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.medication import PrescriptionMedication
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.users import User
from prescripto.ml.runtime import RemoteMLClient
from prescripto.worker.coordinator import CANONICAL_STAGES
from prescripto.worker.exceptions import WorkerFencedError
from prescripto.worker.fence import commit_stage_result
from prescripto.worker.main import WorkerRunner
from prescripto.worker.queue import QueuePoller


# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------

def _make_prescription_image(
    text: str = "Augmentin 625 Duo 1 tab BD after food 5 days",
    width: int = 800,
    height: int = 600,
) -> bytes:
    """Creates a synthetic but valid PNG prescription image with text."""
    img = Image.new("RGB", (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.text((50, 100), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_blank_image(width: int = 800, height: int = 800) -> bytes:
    """All-white PNG image — triggers blank image quality gate."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def auth_header(seeded_users):
    token, _ = create_access_token(
        user_id=seeded_users["operator"].id,
        username=seeded_users["operator"].username,
        role=seeded_users["operator"].role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ml_service_client():
    """Provides a TestClient for the ML service with MockOCRRuntime injected."""
    ml_main._ocr_runtime = MockOCRRuntime()
    ml_main._startup_error = None
    with TestClient(ml_main.app, raise_server_exceptions=False) as tc:
        yield tc


def _create_ml_bridge(ml_client: TestClient):
    """
    Returns a mock function for httpx.post that forwards requests to
    the in-process ML service FastAPI app.
    """
    def mock_post(url, *args, **kwargs):
        if "/v1/ocr/recognize" in str(url):
            return ml_client.post("/v1/ocr/recognize", files=kwargs.get("files"))
        raise RuntimeError(f"Unexpected HTTP call to: {url}")
    return mock_post


def _seed_test_environment(
    db_session: Session,
    mock_storage,
    image_bytes: bytes,
    job_status: str = "PENDING",
    lease_owner: str | None = None,
    lease_token: int = 0,
    lease_expires_at = None,
) -> dict:
    """Helper to seed User, ModelVersion, PrescriptionDocument, Analysis, and AnalysisJob."""
    user = User(
        id=uuid.uuid4(),
        username=f"user_{uuid.uuid4().hex[:8]}",
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hashed_pw",
        role="OPERATOR",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    doc_id = uuid.uuid4()
    analysis_id = uuid.uuid4()
    job_id = uuid.uuid4()
    storage_key = f"prescriptions/{doc_id}/original.png"

    mock_storage.put_object(storage_key, image_bytes, "image/png")

    file_hash = hashlib.sha256(image_bytes).hexdigest()
    doc = PrescriptionDocument(
        id=doc_id,
        uploader_id=user.id,
        storage_key=storage_key,
        file_hash_sha256=file_hash,
        mime_type="image/png",
        file_size_bytes=len(image_bytes),
        status="UPLOADED",
    )
    model = ModelVersion(
        id=uuid.uuid4(),
        model_name="PP-OCRv6",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key=f"models/PP-OCRv6/1.0.0/model.onnx",
        framework="PyTorch",
        license="Apache-2.0",
    )
    analysis = Analysis(
        id=analysis_id,
        document_id=doc.id,
        status="QUEUED",
        pipeline_version="1.0.0",
        model_snapshot_id=model.id,
    )
    job = AnalysisJob(
        id=job_id,
        analysis_id=analysis.id,
        status=job_status,
        lease_owner=lease_owner,
        lease_token=lease_token,
        lease_expires_at=lease_expires_at,
        retry_count=0,
        max_retries=3,
    )
    db_session.add_all([doc, model, analysis, job])
    db_session.commit()

    return {
        "doc": doc,
        "model": model,
        "analysis": analysis,
        "job": job,
    }


# ---------------------------------------------------------------------------
# Happy Path: End-to-End Distributed Workflow
# ---------------------------------------------------------------------------

def test_e2e_distributed_pipeline_happy_path(
    client: TestClient,
    db_session: Session,
    mock_storage,
    auth_header,
    ml_service_client,
):
    """
    Happy Path:
    Real Image -> Upload -> Job Queued -> Worker -> RemoteMLClient ->
    ML Service (:8001) -> OCRLine -> Extraction & Normalization ->
    DB Persistence -> API Result Response
    """
    # 1. Upload prescription image via Backend API
    image_bytes = _make_prescription_image()
    headers = dict(auth_header)
    headers["Idempotency-Key"] = f"e2e-key-{uuid.uuid4()}"

    upload_resp = client.post(
        "/api/v1/prescriptions",
        headers=headers,
        files={"file": ("prescription.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert upload_resp.status_code == 202, f"Upload failed: {upload_resp.text}"
    upload_data = upload_resp.json()
    prescription_id = uuid.UUID(upload_data["prescription_id"])
    analysis_id = uuid.UUID(upload_data["analysis_id"])

    # 2. Verify initial database state (Analysis QUEUED, Job PENDING)
    analysis = db_session.query(Analysis).filter(Analysis.id == analysis_id).first()
    assert analysis is not None
    assert analysis.status == "QUEUED"

    job = db_session.query(AnalysisJob).filter(AnalysisJob.analysis_id == analysis_id).first()
    assert job is not None
    assert job.status == "PENDING"

    # 3. Instantiate RemoteMLClient pointed at ML service
    remote_ml_client = RemoteMLClient(ml_service_url="http://ml-service:8001")
    ml_bridge = _create_ml_bridge(ml_service_client)

    # 4. Worker executes the job using RemoteMLClient
    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="distributed-e2e-worker",
        poll_interval=0.1,
        lease_seconds=600,
        heartbeat_seconds=60,
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_ml_client,
    )

    with patch("httpx.post", side_effect=ml_bridge):
        processed = runner.run_once()

    assert processed is True

    # 5. Verify Job & Analysis state in DB
    db_session.refresh(job)
    db_session.refresh(analysis)
    assert job.status == "SUCCEEDED"
    assert job.lease_token == 1
    assert job.retry_count == 0
    assert analysis.status in ["COMPLETED", "REQUIRES_REVIEW"]
    assert analysis.completed_at is not None

    # 6. Verify all 8 stages were committed
    committed_stages = (
        db_session.query(AnalysisStage)
        .filter(AnalysisStage.analysis_id == analysis_id)
        .all()
    )
    assert len(committed_stages) == len(CANONICAL_STAGES)
    stage_names = {s.stage_name for s in committed_stages}
    for expected in CANONICAL_STAGES:
        assert expected in stage_names

    # 7. Verify extracted medications persisted
    meds = (
        db_session.query(PrescriptionMedication)
        .filter(PrescriptionMedication.analysis_id == analysis_id)
        .all()
    )
    assert len(meds) >= 1
    first_med = meds[0]
    assert "Augmentin" in (first_med.name_raw or "")
    assert first_med.line_index == 0

    # 8. Verify Result API returns 200 OK with analysis payload
    result_resp = client.get(
        f"/api/v1/analyses/{analysis_id}/result",
        headers=auth_header,
    )
    assert result_resp.status_code == 200
    res_data = result_resp.json()
    assert res_data["analysis_id"] == str(analysis_id)
    assert len(res_data["medications"]) >= 1
    assert "Augmentin" in res_data["medications"][0]["name"]["value"]


# ---------------------------------------------------------------------------
# Failure Case 1: ML Service Unavailable
# ---------------------------------------------------------------------------

def test_failure_ml_service_unavailable(
    db_session: Session,
    mock_storage,
):
    """
    ML Service is down / unreachable (ConnectError).
    Worker must catch error, roll back uncommitted stages, and mark job FAILED.
    """
    image_bytes = _make_prescription_image()
    env = _seed_test_environment(db_session, mock_storage, image_bytes)
    job = env["job"]
    analysis = env["analysis"]

    remote_client = RemoteMLClient(ml_service_url="http://unreachable-ml-service:8001")
    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="unavail-worker",
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_client,
    )

    with patch("httpx.post", side_effect=httpx.ConnectError("Connection refused")):
        processed = runner.run_once()

    assert processed is True
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 1

    # Verify zero partial stages were committed
    stages = db_session.query(AnalysisStage).filter(AnalysisStage.analysis_id == analysis.id).all()
    assert len(stages) == 0


# ---------------------------------------------------------------------------
# Failure Case 2: ML Service Returns HTTP 4xx/5xx
# ---------------------------------------------------------------------------

def test_failure_ml_service_http_502(
    db_session: Session,
    mock_storage,
):
    """
    ML Service returns HTTP 502 (e.g. OCR inference crash / OOM).
    Worker must catch error, mark job FAILED, and increment retry count.
    """
    image_bytes = _make_prescription_image()
    env = _seed_test_environment(db_session, mock_storage, image_bytes)
    job = env["job"]

    mock_resp = httpx.Response(status_code=502, text="Bad Gateway: GPU worker crashed")
    remote_client = RemoteMLClient(ml_service_url="http://ml-service:8001")
    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="http-err-worker",
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_client,
    )

    with patch("httpx.post", return_value=mock_resp):
        processed = runner.run_once()

    assert processed is True
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 1


# ---------------------------------------------------------------------------
# Failure Case 3: ML Request Timeout
# ---------------------------------------------------------------------------

def test_failure_ml_service_timeout(
    db_session: Session,
    mock_storage,
):
    """
    ML service hangs and exceeds request timeout.
    RemoteMLClient raises timeout RuntimeError; worker rolls back and marks job FAILED.
    """
    image_bytes = _make_prescription_image()
    env = _seed_test_environment(db_session, mock_storage, image_bytes)
    job = env["job"]

    remote_client = RemoteMLClient(ml_service_url="http://ml-service:8001", timeout=5.0)
    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="timeout-worker",
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_client,
    )

    with patch("httpx.post", side_effect=httpx.ReadTimeout("Request timed out after 5.0s")):
        processed = runner.run_once()

    assert processed is True
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 1


# ---------------------------------------------------------------------------
# Failure Case 4: Malformed ML Response
# ---------------------------------------------------------------------------

def test_failure_malformed_ml_response(
    db_session: Session,
    mock_storage,
):
    """
    ML service returns 200 OK but with non-JSON or invalid schema body.
    RemoteMLClient raises RuntimeError; worker marks job FAILED and rolls back.
    """
    image_bytes = _make_prescription_image()
    env = _seed_test_environment(db_session, mock_storage, image_bytes)
    job = env["job"]

    mock_resp = httpx.Response(status_code=200, text="<html<body>Gateway OK</body></html>")
    remote_client = RemoteMLClient(ml_service_url="http://ml-service:8001")
    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="malformed-worker",
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_client,
    )

    with patch("httpx.post", return_value=mock_resp):
        processed = runner.run_once()

    assert processed is True
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 1


# ---------------------------------------------------------------------------
# Failure Case 5: Blank Image
# ---------------------------------------------------------------------------

def test_failure_blank_image_requires_review(
    db_session: Session,
    mock_storage,
    ml_service_client,
):
    """
    An all-white blank image is processed through the distributed pipeline.
    Quality check must detect blank image, flagging QUALITY_TOO_LOW.
    Pipeline safely finishes in REQUIRES_REVIEW state without crash.
    """
    blank_bytes = _make_blank_image()
    env = _seed_test_environment(db_session, mock_storage, blank_bytes)
    job = env["job"]
    analysis = env["analysis"]

    remote_ml_client = RemoteMLClient(ml_service_url="http://ml-service:8001")
    ml_bridge = _create_ml_bridge(ml_service_client)

    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="blank-worker",
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_ml_client,
    )

    with patch("httpx.post", side_effect=ml_bridge):
        processed = runner.run_once()

    assert processed is True
    db_session.refresh(job)
    db_session.refresh(analysis)
    assert job.status == "SUCCEEDED"
    assert analysis.status == "REQUIRES_REVIEW"
    assert analysis.review_required is True
    assert any("QUALITY_TOO_LOW" in r for r in (analysis.review_reasons or []))


# ---------------------------------------------------------------------------
# Failure Case 6: Unsupported / Corrupt Image
# ---------------------------------------------------------------------------

def test_failure_corrupt_image(
    db_session: Session,
    mock_storage,
):
    """
    Corrupt image data in storage fails during pipeline quality check.
    Pipeline halts cleanly and marks job FAILED.
    """
    corrupt_bytes = b"\x89PNG\r\n\x1a\ncorrupted_garbage_bytes_here"
    env = _seed_test_environment(db_session, mock_storage, corrupt_bytes)
    job = env["job"]

    remote_ml_client = RemoteMLClient(ml_service_url="http://ml-service:8001")
    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="corrupt-worker",
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_ml_client,
    )

    processed = runner.run_once()
    assert processed is True
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 1


# ---------------------------------------------------------------------------
# Failure Case 7: Worker Retry After ML Failure
# ---------------------------------------------------------------------------

def test_failure_worker_retry_after_ml_failure(
    db_session: Session,
    mock_storage,
    ml_service_client,
):
    """
    Simulates transient ML outage followed by recovery:
      1. Job fails on attempt 1 due to ML service 503.
      2. Job retry_count = 1, backoff scheduled.
      3. Backoff expires, ML service recovers.
      4. Worker claims job on attempt 2 (lease_token=2) and SUCCEEDS.
    """
    image_bytes = _make_prescription_image()
    env = _seed_test_environment(db_session, mock_storage, image_bytes)
    job = env["job"]

    remote_ml_client = RemoteMLClient(ml_service_url="http://ml-service:8001")
    runner = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="retry-worker",
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_ml_client,
    )

    # Attempt 1: ML service returns 503
    with patch("httpx.post", return_value=httpx.Response(status_code=503, text="Service Unavailable")):
        runner.run_once()

    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 1
    assert job.backoff_until is not None

    # Fast-forward past backoff schedule
    job.backoff_until = utc_now() - timedelta(seconds=1)
    db_session.commit()

    # Attempt 2: ML service recovers (bridge to working ML service)
    ml_bridge = _create_ml_bridge(ml_service_client)
    with patch("httpx.post", side_effect=ml_bridge):
        runner.run_once()

    db_session.refresh(job)
    assert job.status == "SUCCEEDED"
    assert job.lease_token == 2
    assert job.retry_count == 1


# ---------------------------------------------------------------------------
# Failure Case 8: Worker Lease / Fencing Behavior Around ML Calls
# ---------------------------------------------------------------------------

def test_failure_worker_fencing_during_ml_call(
    db_session: Session,
    mock_storage,
    ml_service_client,
):
    """
    Worker A claims the job with lease_token=1.
    While Worker A is executing a slow ML request, Worker A's lease expires.
    QueuePoller recovers the job, and Worker B claims it with lease_token=2.
    Worker B completes the job successfully.
    When Worker A finally finishes its ML call and tries to commit a stage,
    commit_stage_result rejects the write with WorkerFencedError.
    """
    image_bytes = _make_prescription_image()
    env = _seed_test_environment(
        db_session,
        mock_storage,
        image_bytes,
        job_status="RUNNING",
        lease_owner="worker-A",
        lease_token=1,
        lease_expires_at=utc_now() - timedelta(seconds=1),  # Expired
    )
    job = env["job"]
    analysis = env["analysis"]

    # 1. Lease recovery detects expired lease from Worker A
    recovered = QueuePoller.recover_expired_leases(db_session)
    assert recovered == 1
    db_session.refresh(job)
    assert job.status == "PENDING"
    assert job.retry_count == 1

    # Fast forward past backoff so Worker B can claim
    job.backoff_until = utc_now() - timedelta(seconds=1)
    db_session.commit()

    # 2. Worker B claims job with token 2 and completes it
    remote_ml_client = RemoteMLClient(ml_service_url="http://ml-service:8001")
    ml_bridge = _create_ml_bridge(ml_service_client)
    runner_b = WorkerRunner(
        session_factory=lambda: db_session,
        worker_id="worker-B",
        close_session=False,
        storage_client=mock_storage,
        ocr_runtime=remote_ml_client,
    )
    with patch("httpx.post", side_effect=ml_bridge):
        runner_b.run_once()

    db_session.refresh(job)
    assert job.status == "SUCCEEDED"
    assert job.lease_token == 2

    # 3. Worker A (stale lease_token=1) attempts to commit a stage after delayed ML call
    with pytest.raises(WorkerFencedError):
        commit_stage_result(
            db=db_session,
            analysis_id=analysis.id,
            stage_name="TEXT_DETECTION",
            lease_token=1,  # Stale token from Worker A
            lease_owner="worker-A",
            output={"regions_detected_count": 1},
        )
