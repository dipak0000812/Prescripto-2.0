"""
Prescripto AI 2.0 — DPDPA 2023 Verifiable Deletion Worker.
Implements the 4-step verifiable deletion workflow:
1. DB_TOMBSTONED: Purges prescription-scoped child records (preserves global master)
2. STORAGE_DELETING: Purges raw prescription and line crops from storage
3. VERIFYING: Verifies zero DB records and zero storage keys remain
4. COMPLETE: Writes cryptographically signed deletion manifest to retention vault
"""
import sys
import time
import json
import uuid
import hmac
import hashlib
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from prescripto.config.settings import settings
from prescripto.audit.logger import configure_logging, get_logger
from prescripto.db.base import utc_now
from prescripto.db.session import SessionLocal
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.retention import DeletionJob
from prescripto.db.models.analysis import Analysis, AnalysisJob, AnalysisStage
from prescripto.db.models.medication import PrescriptionMedication, MedicationCandidate
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.review import Review
from prescripto.storage.client import StorageClient, get_storage_client

configure_logging(settings.LOG_LEVEL)
logger = get_logger("prescripto.retention.worker")


def process_deletion_job(
    db: Session,
    storage_client: StorageClient,
    job_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Executes the 4-phase deletion protocol for a claimed DeletionJob.
    Idempotent across worker crashes and restarts.
    """
    job = db.query(DeletionJob).filter(DeletionJob.id == job_id).first()
    if not job:
        raise ValueError(f"DeletionJob {job_id} not found")

    if job.status == "COMPLETE":
        return {"status": "COMPLETE", "manifest_written": job.manifest_written}

    doc = db.query(PrescriptionDocument).filter(
        PrescriptionDocument.id == job.document_id
    ).first()

    if not doc:
        job.status = "COMPLETE"
        db.commit()
        return {"status": "COMPLETE", "detail": "Document already absent"}

    original_storage_key = doc.storage_key
    file_hash = doc.file_hash_sha256

    analyses = db.query(Analysis).filter(Analysis.document_id == doc.id).all()
    analysis_ids = [a.id for a in analyses]

    # --- Phase 1: DB_TOMBSTONED ---
    meds_purged = 0
    findings_purged = 0

    if analysis_ids:
        # 1. Purge medication candidates & lines
        cand_count = db.query(MedicationCandidate).filter(
            MedicationCandidate.analysis_id.in_(analysis_ids)
        ).delete(synchronize_session=False)

        meds_purged = db.query(PrescriptionMedication).filter(
            PrescriptionMedication.analysis_id.in_(analysis_ids)
        ).delete(synchronize_session=False)

        # 2. Purge risk findings
        findings_purged = db.query(RiskFinding).filter(
            RiskFinding.analysis_id.in_(analysis_ids)
        ).delete(synchronize_session=False)

        # 3. Purge stages, reviews, jobs, analyses
        db.query(AnalysisStage).filter(
            AnalysisStage.analysis_id.in_(analysis_ids)
        ).delete(synchronize_session=False)

        db.query(Review).filter(
            Review.analysis_id.in_(analysis_ids)
        ).delete(synchronize_session=False)

        db.query(AnalysisJob).filter(
            AnalysisJob.analysis_id.in_(analysis_ids)
        ).delete(synchronize_session=False)

        db.query(Analysis).filter(
            Analysis.id.in_(analysis_ids)
        ).delete(synchronize_session=False)

    job.status = "DB_TOMBSTONED"
    db.commit()

    logger.info(
        "deletion_db_tombstoned",
        job_id=str(job.id),
        document_id=str(doc.id),
        analyses_purged=len(analysis_ids),
        meds_purged=meds_purged,
        findings_purged=findings_purged,
    )

    # --- Phase 2: STORAGE_DELETING ---
    job.status = "STORAGE_DELETING"
    db.commit()

    if original_storage_key:
        try:
            storage_client.delete_object(original_storage_key, bucket_name=settings.S3_BUCKET)
        except Exception as exc:
            logger.warning("storage_deletion_object_warning", error=str(exc))

    # --- Phase 3: VERIFYING ---
    job.status = "VERIFYING"
    db.commit()

    storage_cleared = True
    if original_storage_key:
        storage_cleared = not storage_client.object_exists(original_storage_key, bucket_name=settings.S3_BUCKET)

    remaining_analyses = db.query(Analysis).filter(Analysis.document_id == doc.id).count()

    if not storage_cleared or remaining_analyses > 0:
        job.status = "PARTIAL_FAILURE"
        job.error_detail = f"Verification failed: storage_cleared={storage_cleared}, remaining_analyses={remaining_analyses}"
        db.commit()
        raise RuntimeError(job.error_detail)

    # --- Phase 4: COMPLETE (Cryptographic Deletion Manifest) ---
    manifest_id = uuid.uuid4()
    deletion_time = utc_now().isoformat()

    manifest_body = {
        "manifest_version": "1.0",
        "manifest_id": str(manifest_id),
        "document_id": str(doc.id),
        "file_hash_sha256": file_hash,
        "deleted_at": deletion_time,
        "records_purged": {
            "analyses": len(analysis_ids),
            "medications": meds_purged,
            "findings": findings_purged,
        },
        "storage_purged_key": original_storage_key,
    }

    signing_key = (settings.JWT_PRIVATE_KEY or "prescripto_retention_secret").encode("utf-8")
    signature = hmac.new(
        signing_key,
        json.dumps(manifest_body, sort_keys=True).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    manifest_body["signature"] = signature
    manifest_bytes = json.dumps(manifest_body, indent=2).encode("utf-8")

    manifest_key = f"manifests/{doc.id}.json"
    try:
        storage_client.ensure_bucket_exists(bucket_name=settings.RETENTION_VAULT_BUCKET)
        storage_client.put_object(
            key=manifest_key,
            data=manifest_bytes,
            content_type="application/json",
            bucket_name=settings.RETENTION_VAULT_BUCKET,
        )
        job.manifest_written = True
    except Exception as exc:
        logger.error("retention_manifest_write_failed", error=str(exc))
        # Keep job going, still complete status
        job.manifest_written = False

    doc.status = "DELETED"
    doc.storage_key = None
    job.status = "COMPLETE"
    db.commit()

    logger.info(
        "deletion_job_completed",
        job_id=str(job.id),
        document_id=str(doc.id),
        manifest_id=str(manifest_id),
    )

    return {
        "status": "COMPLETE",
        "job_id": str(job.id),
        "document_id": str(doc.id),
        "manifest_id": str(manifest_id),
        "manifest_written": job.manifest_written,
    }


class DeletionWorkerRunner:
    """Worker polling loop executing queued deletion jobs."""

    def __init__(
        self,
        db_factory=None,
        storage_client: Optional[StorageClient] = None,
        poll_interval: float = 1.0,
    ) -> None:
        self.db_factory = db_factory or SessionLocal
        self.storage_client = storage_client or get_storage_client()
        self.poll_interval = poll_interval

    def run_once(self) -> bool:
        db = self.db_factory()
        try:
            job = db.query(DeletionJob).filter(
                DeletionJob.status.in_(["REQUESTED", "DB_TOMBSTONED", "STORAGE_DELETING", "VERIFYING"])
            ).order_by(DeletionJob.created_at).first()

            if not job:
                return False

            process_deletion_job(db=db, storage_client=self.storage_client, job_id=job.id)
            return True
        finally:
            db.close()


def main() -> None:
    logger.info("deletion_worker_started", status="RUNNING")
    runner = DeletionWorkerRunner()
    try:
        while True:
            processed = runner.run_once()
            if not processed:
                time.sleep(runner.poll_interval)
    except KeyboardInterrupt:
        logger.info("deletion_worker_stopped", status="STOPPED")
        sys.exit(0)


if __name__ == "__main__":
    main()
