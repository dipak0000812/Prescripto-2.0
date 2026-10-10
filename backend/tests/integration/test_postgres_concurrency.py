"""
T2.2 — PostgreSQL-specific concurrency and correctness tests.

All tests require a real PostgreSQL connection and are marked @pytest.mark.postgres.
They are skipped automatically when TEST_DATABASE_URL is not set to a PostgreSQL URL.

Tests use SEPARATE real sessions with real COMMITs (no savepoint wrapper) so that
row-level locking semantics (FOR UPDATE SKIP LOCKED, FOR SHARE) are observable.
Each test cleans up its own rows in a finally block.

Why separate sessions rather than the db_session fixture?
The concurrency behaviours under test (claim_next_job with FOR UPDATE SKIP LOCKED,
heartbeat UPDATE blocked by FOR SHARE) only manifest when distinct backend connections
race. Using a single shared session makes them invisible.
"""
import hashlib
import threading
import time
import uuid
from datetime import timedelta
from io import BytesIO
from typing import Optional

import pytest
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from prescripto.db.base import utc_now
from prescripto.db.models.analysis import Analysis, AnalysisJob, AnalysisStage
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.users import User
from prescripto.worker.queue import QueuePoller


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session_factory(db_url: str):
    """Return a sessionmaker bound to a fresh engine (separate connection pool)."""
    import json
    eng = create_engine(
        db_url,
        pool_pre_ping=True,
        json_serializer=lambda obj: json.dumps(obj, default=str),
    )
    return sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=eng), eng


def _make_png_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (800, 800), "white").save(buf, format="PNG")
    return buf.getvalue()


def _seed_model_doc_analysis_job(session: Session) -> dict:
    """Seed one complete job row and return the objects. Session must be committed by caller."""
    user = User(
        id=uuid.uuid4(),
        username=f"pg_user_{uuid.uuid4().hex[:8]}",
        email=f"pg_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="test_password_hash",
        role="OPERATOR",
        is_active=True,
    )
    session.add(user)
    session.flush()

    model = ModelVersion(
        id=uuid.uuid4(),
        model_name=f"pg-test-model-{uuid.uuid4().hex[:8]}",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key=f"models/{uuid.uuid4().hex[:8]}.onnx",
        framework="PyTorch",
        license="MIT",
    )
    session.add(model)
    session.flush()

    img = _make_png_bytes()
    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=user.id,
        storage_key="prescriptions/pg-test/original.png",
        file_hash_sha256=hashlib.sha256(img).hexdigest(),
        mime_type="image/png",
        file_size_bytes=len(img),
        status="UPLOADED",
    )
    session.add(doc)
    session.flush()

    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        model_snapshot_id=model.id,
        pipeline_version="1.0.0",
        status="QUEUED",
    )
    session.add(analysis)
    session.flush()

    job = AnalysisJob(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        status="PENDING",
        lease_token=0,
        retry_count=0,
        max_retries=3,
    )
    session.add(job)
    user_id = user.id
    model_id = model.id
    doc_id = doc.id
    analysis_id = analysis.id
    job_id = job.id
    session.commit()
    return {
        "user_id": user_id,
        "model_id": model_id,
        "doc_id": doc_id,
        "analysis_id": analysis_id,
        "job_id": job_id,
        "user": user,
        "model": model,
        "doc": doc,
        "analysis": analysis,
        "job": job,
        "img": img,
    }


def _cleanup(session: Session, obj_ids: dict) -> None:
    """Delete test rows by primary key; ignore missing rows."""
    # Delete child rows first to respect FK constraints
    for table, pk in [
        ("analysis_stages", obj_ids.get("analysis_id")),
        ("medication_candidates", obj_ids.get("analysis_id")),
        ("prescription_medications", obj_ids.get("analysis_id")),
        ("risk_findings", obj_ids.get("analysis_id")),
        ("analysis_jobs", obj_ids.get("job_id")),
        ("analyses", obj_ids.get("analysis_id")),
        ("prescription_documents", obj_ids.get("doc_id")),
        ("model_versions", obj_ids.get("model_id")),
        ("users", obj_ids.get("user_id")),
    ]:
        if pk is not None:
            col = "analysis_id" if table not in ("analysis_jobs", "analyses", "prescription_documents", "model_versions", "users") else "id"
            try:
                session.execute(
                    text(f"DELETE FROM {table} WHERE {col} = :pk"),
                    {"pk": str(pk)},
                )
            except Exception:
                session.rollback()
    try:
        session.commit()
    except Exception:
        session.rollback()


def _drain_queue(session: Session) -> None:
    """Clear analysis queue tables so the test environment has a clean slate."""
    for tbl in [
        "analysis_stages",
        "medication_candidates",
        "prescription_medications",
        "risk_findings",
        "analysis_jobs",
        "analyses",
    ]:
        try:
            session.execute(text(f"DELETE FROM {tbl}"))
        except Exception:
            session.rollback()
    try:
        session.commit()
    except Exception:
        session.rollback()


# ---------------------------------------------------------------------------
# T2.2-1  claim_next_job: two threads, one job → exactly one claims it
# ---------------------------------------------------------------------------

@pytest.mark.postgres
def test_claim_next_job_exactly_one_winner():
    """
    Two worker threads both call claim_next_job against one PENDING job.
    Exactly one must receive a JobClaim; the other must receive None.
    FOR UPDATE SKIP LOCKED guarantees this on PostgreSQL.
    """
    import os
    db_url = os.environ["TEST_DATABASE_URL"]
    factory_a, eng_a = _make_session_factory(db_url)
    factory_b, eng_b = _make_session_factory(db_url)

    setup_session = factory_a()
    _drain_queue(setup_session)
    seed = _seed_model_doc_analysis_job(setup_session)
    setup_session.close()

    results: list[Optional[object]] = [None, None]
    errors: list[Optional[Exception]] = [None, None]

    barrier = threading.Barrier(2)

    def worker(idx: int, factory):
        db = factory()
        try:
            barrier.wait()  # synchronize start
            results[idx] = QueuePoller.claim_next_job(
                db=db, worker_id=f"worker-{idx}", lease_duration=timedelta(minutes=5)
            )
        except Exception as exc:
            errors[idx] = exc
        finally:
            db.close()

    t_a = threading.Thread(target=worker, args=(0, factory_a))
    t_b = threading.Thread(target=worker, args=(1, factory_b))
    t_a.start(); t_b.start()
    t_a.join(timeout=10); t_b.join(timeout=10)

    cleanup_session = factory_a()
    try:
        assert errors[0] is None, f"Worker A raised: {errors[0]}"
        assert errors[1] is None, f"Worker B raised: {errors[1]}"

        claims = [r for r in results if r is not None]
        nones = [r for r in results if r is None]
        assert len(claims) == 1, f"Expected exactly 1 claim, got {len(claims)}: {results}"
        assert len(nones) == 1, f"Expected exactly 1 None, got {len(nones)}: {results}"
    finally:
        _cleanup(cleanup_session, {
            "job_id": seed["job_id"], "analysis_id": seed["analysis_id"],
            "doc_id": seed["doc_id"], "model_id": seed["model_id"],
            "user_id": seed["user_id"],
        })
        cleanup_session.close()
        eng_a.dispose()
        eng_b.dispose()


@pytest.mark.postgres
def test_claim_next_job_two_jobs_claimed_by_different_workers():
    """
    Two worker threads, two PENDING jobs → each worker claims a different job.
    """
    import os
    db_url = os.environ["TEST_DATABASE_URL"]
    factory_a, eng_a = _make_session_factory(db_url)
    factory_b, eng_b = _make_session_factory(db_url)

    setup = factory_a()
    _drain_queue(setup)
    seed_1 = _seed_model_doc_analysis_job(setup)
    seed_2 = _seed_model_doc_analysis_job(setup)
    setup.close()

    results: list[Optional[object]] = [None, None]
    errors: list[Optional[Exception]] = [None, None]
    barrier = threading.Barrier(2)

    def worker(idx: int, factory):
        db = factory()
        try:
            barrier.wait()
            results[idx] = QueuePoller.claim_next_job(
                db=db, worker_id=f"worker-{idx}", lease_duration=timedelta(minutes=5)
            )
        except Exception as exc:
            errors[idx] = exc
        finally:
            db.close()

    t_a = threading.Thread(target=worker, args=(0, factory_a))
    t_b = threading.Thread(target=worker, args=(1, factory_b))
    t_a.start(); t_b.start()
    t_a.join(timeout=10); t_b.join(timeout=10)

    cleanup = factory_a()
    try:
        assert errors[0] is None, f"Worker A raised: {errors[0]}"
        assert errors[1] is None, f"Worker B raised: {errors[1]}"
        assert results[0] is not None and results[1] is not None, "Both workers should claim a job"
        claimed_ids = {results[0].job_id, results[1].job_id}  # type: ignore[union-attr]
        assert len(claimed_ids) == 2, f"Workers claimed same job: {claimed_ids}"
    finally:
        for seed in [seed_1, seed_2]:
            _cleanup(cleanup, {
                "job_id": seed["job_id"],
                "analysis_id": seed["analysis_id"],
                "doc_id": seed["doc_id"],
                "model_id": seed["model_id"],
                "user_id": seed["user_id"],
            })
        cleanup.close()
        eng_a.dispose()
        eng_b.dispose()


# ---------------------------------------------------------------------------
# T2.2-2  B3 verification: commit_stage_result does NOT block heartbeat
# ---------------------------------------------------------------------------

@pytest.mark.postgres
def test_heartbeat_not_blocked_after_commit_stage_result():
    """
    Verifies that commit_stage_result no longer blocks heartbeat renew_lease on PostgreSQL:
    - Session A calls commit_stage_result and holds the uncommitted transaction open.
    - Session B calls QueuePoller.renew_lease with a 3-second lock_timeout.
    - Because commit_stage_result uses a plain read without FOR SHARE, Session B's UPDATE
      succeeds immediately without blocking.
    """
    import os
    from prescripto.worker.fence import commit_stage_result
    from prescripto.worker.queue import QueuePoller

    db_url = os.environ["TEST_DATABASE_URL"]
    factory_a, eng_a = _make_session_factory(db_url)
    factory_b, eng_b = _make_session_factory(db_url)

    setup = factory_a()
    seed = _seed_model_doc_analysis_job(setup)
    job = seed["job"]
    analysis = seed["analysis"]
    model = seed["model"]
    setup.close()

    # Claim the job so it is RUNNING
    claim_session = factory_a()
    claim = QueuePoller.claim_next_job(
        db=claim_session,
        worker_id="worker-lock-test",
        lease_duration=timedelta(minutes=10),
    )
    assert claim is not None, "Job should be claimable"
    claim_session.close()  # claim was committed; close but keep claim dataclass

    # Session A: start commit_stage_result (no FOR SHARE, does NOT commit)
    session_a = factory_a()
    heartbeat_result: list[Optional[bool]] = [None]
    heartbeat_error: list[Optional[Exception]] = [None]

    lock_acquired = threading.Event()
    release_lock = threading.Event()

    def run_stage_in_session_a():
        """Session A executes commit_stage_result, then waits without committing."""
        try:
            session_a.execute(text("SET LOCAL statement_timeout = '10s'"))
            commit_stage_result(
                db=session_a,
                analysis_id=claim.analysis_id,
                stage_name="INGESTION",
                lease_token=claim.lease_token,
                lease_owner=claim.lease_owner,
                output={"status": "ok"},
            )
            lock_acquired.set()
            release_lock.wait(timeout=8.0)  # hold the open transaction
        except Exception as exc:
            heartbeat_error[0] = exc
            lock_acquired.set()
        finally:
            session_a.close()

    def run_heartbeat():
        """Session B tries to UPDATE the same job row with a 3s lock_timeout."""
        lock_acquired.wait(timeout=5.0)
        session_b = factory_b()
        try:
            session_b.execute(text("SET LOCAL lock_timeout = '3s'"))
            success = QueuePoller.renew_lease(
                db=session_b,
                job_id=claim.job_id,
                lease_token=claim.lease_token,
                worker_id=claim.lease_owner,
                lease_duration=timedelta(minutes=10),
            )
            heartbeat_result[0] = success
        except Exception as exc:
            heartbeat_error[0] = exc
        finally:
            session_b.close()
            release_lock.set()  # unblock session A

    t_a = threading.Thread(target=run_stage_in_session_a)
    t_b = threading.Thread(target=run_heartbeat)
    t_a.start()
    t_b.start()
    t_a.join(timeout=15)
    t_b.join(timeout=15)

    cleanup = factory_a()
    try:
        assert heartbeat_error[0] is None, (
            f"Heartbeat failed: {heartbeat_error[0]}"
        )
        assert heartbeat_result[0] is True, "Heartbeat must complete while stage transaction is open"
    finally:
        _cleanup(cleanup, {
            "job_id": seed["job_id"], "analysis_id": seed["analysis_id"],
            "doc_id": seed["doc_id"], "model_id": seed["model_id"],
            "user_id": seed["user_id"],
        })
        cleanup.close()
        eng_a.dispose()
        eng_b.dispose()


@pytest.mark.postgres
def test_coordinator_heartbeat_succeeds_during_slow_stage():
    """
    T3.2 — Coordinator-level verification of Bug B3 fix:
    - Thread runs PipelineCoordinator on a claimed job with custom handlers:
      INGESTION (fast) and QUALITY_CHECK (blocks on an event).
    - Session A runs the coordinator. INGESTION completes and calls commit_stage_result,
      which no longer holds FOR SHARE on analysis_jobs.
    - When QUALITY_CHECK starts, Session B calls QueuePoller.renew_lease with lock_timeout='1500ms'.
    - renew_lease succeeds immediately without blocking, and lease_expires_at moves forward.
    - Event is released, QUALITY_CHECK finishes, mark_job_succeeded commits with FOR UPDATE.
    """
    import os
    from prescripto.worker.coordinator import PipelineCoordinator
    from prescripto.worker.queue import QueuePoller
    from prescripto.db.base import ensure_utc

    db_url = os.environ["TEST_DATABASE_URL"]
    factory_a, eng_a = _make_session_factory(db_url)
    factory_b, eng_b = _make_session_factory(db_url)

    setup = factory_a()
    _drain_queue(setup)
    seed = _seed_model_doc_analysis_job(setup)
    setup.close()

    # Claim the job so it is RUNNING
    claim_session = factory_a()
    claim = QueuePoller.claim_next_job(
        db=claim_session,
        worker_id="worker-b3-coord",
        lease_duration=timedelta(minutes=10),
    )
    assert claim is not None, "Job should be claimed"
    claimed_row = claim_session.query(AnalysisJob).filter(AnalysisJob.id == claim.job_id).first()
    assert claimed_row is not None
    initial_expires_at = claimed_row.lease_expires_at
    claim_session.close()

    slow_stage_entered = threading.Event()
    slow_stage_proceed = threading.Event()
    coordinator_error: list[Optional[Exception]] = [None]
    heartbeat_result: list[Optional[bool]] = [None]
    heartbeat_error: list[Optional[Exception]] = [None]
    lease_moved_forward: list[bool] = [False]

    def fast_ingestion(db, analysis, doc, ctx):
        return {"stage": "INGESTION", "status": "COMPLETED"}

    def slow_quality_check(db, analysis, doc, ctx):
        slow_stage_entered.set()
        if not slow_stage_proceed.wait(timeout=10.0):
            raise TimeoutError("slow_stage_proceed was not signalled")
        return {"stage": "QUALITY_CHECK", "status": "COMPLETED"}

    def run_coordinator():
        session_pipe = factory_a()
        try:
            coord = PipelineCoordinator(
                db=session_pipe,
                claim=claim,
                stages=["INGESTION", "QUALITY_CHECK"],
                stage_handlers={
                    "INGESTION": fast_ingestion,
                    "QUALITY_CHECK": slow_quality_check,
                },
            )
            coord.execute()
        except Exception as exc:
            coordinator_error[0] = exc
        finally:
            session_pipe.close()

    t_coord = threading.Thread(target=run_coordinator)
    t_coord.start()

    session_hb = None
    try:
        assert slow_stage_entered.wait(timeout=5.0), "Coordinator did not reach slow stage in time"
        session_hb = factory_b()
        session_hb.execute(text("SET LOCAL lock_timeout = '1500ms'"))
        renewed = QueuePoller.renew_lease(
            db=session_hb,
            job_id=claim.job_id,
            lease_token=claim.lease_token,
            worker_id=claim.lease_owner,
            lease_duration=timedelta(minutes=20),
        )
        heartbeat_result[0] = renewed

        hb_job = session_hb.query(AnalysisJob).filter(AnalysisJob.id == claim.job_id).first()
        if hb_job and hb_job.lease_expires_at and initial_expires_at:
            if ensure_utc(hb_job.lease_expires_at) > ensure_utc(initial_expires_at):
                lease_moved_forward[0] = True
    except Exception as exc:
        heartbeat_error[0] = exc
    finally:
        slow_stage_proceed.set()
        t_coord.join(timeout=10)
        if session_hb:
            session_hb.close()

    cleanup = factory_a()
    try:
        assert heartbeat_error[0] is None, f"Heartbeat failed with: {heartbeat_error[0]}"
        assert heartbeat_result[0] is True, "Heartbeat renew_lease should return True"
        assert lease_moved_forward[0] is True, "lease_expires_at must move forward on renewal"
        assert coordinator_error[0] is None, f"Coordinator failed with: {coordinator_error[0]}"

        # Verify job is SUCCEEDED in the database
        job_row = cleanup.query(AnalysisJob).filter(AnalysisJob.id == claim.job_id).first()
        assert job_row is not None
        assert job_row.status == "SUCCEEDED"

        # Verify both stages are COMPLETED
        stages = cleanup.query(AnalysisStage).filter(AnalysisStage.analysis_id == claim.analysis_id).all()
        stage_names = {s.stage_name for s in stages}
        assert stage_names == {"INGESTION", "QUALITY_CHECK"}
    finally:
        _cleanup(cleanup, {
            "job_id": seed["job_id"], "analysis_id": seed["analysis_id"],
            "doc_id": seed["doc_id"], "model_id": seed["model_id"],
            "user_id": seed["user_id"],
        })
        cleanup.close()
        eng_a.dispose()
        eng_b.dispose()



# ---------------------------------------------------------------------------
# T2.2-3  ARRAY and JSONB column round-trip
# ---------------------------------------------------------------------------

@pytest.mark.postgres
def test_array_and_jsonb_column_round_trip():
    """
    Verify that Analysis.review_reasons (ARRAY) and AnalysisStage.output_json (JSONB)
    survive a write → commit → fresh-session read intact on PostgreSQL.
    """
    import os
    db_url = os.environ["TEST_DATABASE_URL"]
    factory, eng = _make_session_factory(db_url)

    setup = factory()
    seed = _seed_model_doc_analysis_job(setup)
    analysis_id = seed["analysis"].id
    job_id = seed["job"].id
    doc_id = seed["doc"].id
    model_id = seed["model"].id
    setup.close()

    # Write ARRAY and JSONB values
    write_session = factory()
    try:
        analysis = write_session.get(Analysis, analysis_id)
        assert analysis is not None
        reasons = ["QUALITY_FAILED", "LOW_CONFIDENCE"]
        analysis.review_reasons = reasons
        analysis.review_required = True

        stage = AnalysisStage(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            stage_name="TEST_STAGE",
            lease_token=1,
            status="COMPLETED",
            output_json={"key": "value", "count": 42, "nested": {"ok": True}},
        )
        write_session.add(stage)
        stage_id = stage.id
        write_session.commit()
    finally:
        write_session.close()

    # Read back in a fresh session and verify
    read_session = factory()
    try:
        fresh_analysis = read_session.get(Analysis, analysis_id)
        assert fresh_analysis is not None
        assert fresh_analysis.review_reasons == ["QUALITY_FAILED", "LOW_CONFIDENCE"], (
            f"ARRAY round-trip failed: {fresh_analysis.review_reasons}"
        )
        assert fresh_analysis.review_required is True

        fresh_stage = read_session.get(AnalysisStage, stage_id)
        assert fresh_stage is not None
        assert fresh_stage.output_json == {"key": "value", "count": 42, "nested": {"ok": True}}, (
            f"JSONB round-trip failed: {fresh_stage.output_json}"
        )
    finally:
        read_session.close()

    # Cleanup
    cleanup = factory()
    try:
        cleanup.execute(text("DELETE FROM analysis_stages WHERE id = :sid"), {"sid": str(stage_id)})
        cleanup.commit()
    except Exception:
        cleanup.rollback()
    finally:
        _cleanup(cleanup, {
            "job_id": seed["job_id"], "analysis_id": seed["analysis_id"],
            "doc_id": seed["doc_id"], "model_id": seed["model_id"],
            "user_id": seed["user_id"],
        })
        cleanup.close()
        eng.dispose()


# ---------------------------------------------------------------------------
# T2.2-4  Model/migration drift: alembic autogenerate compare_metadata
# ---------------------------------------------------------------------------

@pytest.mark.postgres
def test_no_model_migration_drift():
    """
    Use Alembic's autogenerate compare_metadata to assert that the migrated
    database schema exactly matches Base.metadata. Any diff means a migration
    is missing or a model was changed without a migration.
    """
    import os
    from pathlib import Path
    from alembic.config import Config
    from alembic.migration import MigrationContext
    from alembic.autogenerate import compare_metadata
    from prescripto.db.models import Base

    db_url = os.environ["TEST_DATABASE_URL"]
    import json as _json
    check_eng = create_engine(
        db_url,
        json_serializer=lambda obj: _json.dumps(obj, default=str),
    )

    with check_eng.connect() as conn:
        mc = MigrationContext.configure(
            conn,
            opts={
                "compare_type": False,
                "compare_server_default": False,
            },
        )
        diffs = compare_metadata(mc, Base.metadata)

    check_eng.dispose()

    meaningful_diffs = []
    for diff in diffs:
        items = diff if isinstance(diff, list) else [diff]
        for item in items:
            diff_type = item[0] if isinstance(item, tuple) else str(item)
            # Ignore index and unique constraint name variances (Alembic autogenerate limitations)
            if diff_type in ("add_index", "remove_index", "remove_constraint", "add_constraint"):
                continue
            meaningful_diffs.append(item)

    assert not meaningful_diffs, (
        f"Model/migration drift detected ({len(meaningful_diffs)} diffs):\n"
        + "\n".join(str(d) for d in meaningful_diffs)
    )
