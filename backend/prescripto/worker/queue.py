"""
PostgreSQL Transactional Queue Poller with Monotonic Lease Tokens.
Implements FOR UPDATE SKIP LOCKED job claiming, lease renewals, and backoff retries.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from prescripto.db.base import utc_now, ensure_utc
from prescripto.db.models.analysis import Analysis, AnalysisJob
from prescripto.worker.exceptions import WorkerFencedError
from prescripto.audit.logger import get_logger

logger = get_logger("prescripto.worker.queue")

# Backoff schedule: 5s -> 30s -> 2m
BACKOFF_SCHEDULE = [
    timedelta(seconds=5),
    timedelta(seconds=30),
    timedelta(minutes=2),
]


def compute_backoff_delay(retry_count: int) -> timedelta:
    """Returns backoff duration based on retry attempt index."""
    if retry_count < 0:
        return BACKOFF_SCHEDULE[0]
    if retry_count < len(BACKOFF_SCHEDULE):
        return BACKOFF_SCHEDULE[retry_count]
    return BACKOFF_SCHEDULE[-1]


@dataclass
class JobClaim:
    """Represents a claimed analysis job with monotonic lease token."""
    job_id: uuid.UUID
    analysis_id: uuid.UUID
    lease_token: int
    lease_owner: str
    lease_expires_at: datetime
    retry_count: int
    max_retries: int


class QueuePoller:
    """Handles job claiming, lease renewal, backoff, and terminal state transitions."""

    @staticmethod
    def recover_expired_leases(db: Session) -> int:
        """
        Sweeper pass detecting abandoned or timed-out jobs where status IN ('CLAIMED', 'RUNNING')
        and lease_expires_at < now().
        Transitions to DEAD if max_retries reached, otherwise back to PENDING with backoff.
        """
        now = utc_now()
        candidates = (
            db.query(AnalysisJob)
            .filter(
                AnalysisJob.status.in_(["CLAIMED", "RUNNING"]),
                AnalysisJob.lease_expires_at.isnot(None),
            )
            .all()
        )
        expired_jobs = [j for j in candidates if ensure_utc(j.lease_expires_at) and ensure_utc(j.lease_expires_at) < now]

        recovered_count = 0
        for job in expired_jobs:
            recovered_count += 1
            new_retry_count = job.retry_count + 1
            job.retry_count = new_retry_count
            job.lease_owner = None
            job.lease_expires_at = None
            job.heartbeat_at = None
            job.last_error = "Lease expired due to worker timeout or crash"
            job.updated_at = now

            if new_retry_count >= job.max_retries:
                job.status = "DEAD"
                # Update analysis
                analysis = db.query(Analysis).filter(Analysis.id == job.analysis_id).first()
                if analysis:
                    analysis.status = "FAILED"
                    analysis.error_detail = "Analysis failed: lease expired and max retries exceeded"
                    analysis.completed_at = now
                logger.error(
                    "alert_job_dead",
                    job_id=str(job.id),
                    analysis_id=str(job.analysis_id),
                    retry_count=new_retry_count,
                    reason="lease_timeout_max_retries",
                )
            else:
                job.status = "PENDING"
                delay = compute_backoff_delay(new_retry_count - 1)
                job.backoff_until = now + delay
                logger.warning(
                    "job_lease_expired_recovered",
                    job_id=str(job.id),
                    analysis_id=str(job.analysis_id),
                    retry_count=new_retry_count,
                    backoff_seconds=delay.total_seconds(),
                )

        if recovered_count > 0:
            db.commit()

        return recovered_count

    @staticmethod
    def claim_next_job(
        db: Session,
        worker_id: str,
        lease_duration: timedelta = timedelta(minutes=10),
    ) -> Optional[JobClaim]:
        """
        Claims the next claimable job using FOR UPDATE SKIP LOCKED.
        Targets PENDING rows or claimable FAILED rows with backoff expired.
        Increments lease_token monotonically.
        """
        now = utc_now()

        # Run sweep pass first
        QueuePoller.recover_expired_leases(db)

        # Select candidate
        query = (
            db.query(AnalysisJob)
            .filter(
                or_(
                    AnalysisJob.status == "PENDING",
                    and_(
                        AnalysisJob.status == "FAILED",
                        AnalysisJob.retry_count < AnalysisJob.max_retries,
                    ),
                ),
                or_(
                    AnalysisJob.backoff_until.is_(None),
                    AnalysisJob.backoff_until <= now,
                ),
            )
            .order_by(AnalysisJob.created_at.asc())
        )

        if db.bind and db.bind.dialect.name == "postgresql":
            query = query.with_for_update(skip_locked=True)

        job = query.first()
        if not job:
            return None

        # Monotonically increment lease_token
        new_token = (job.lease_token or 0) + 1
        lease_expires = now + lease_duration

        job.status = "RUNNING"
        job.lease_owner = worker_id
        job.lease_token = new_token
        job.lease_expires_at = lease_expires
        job.heartbeat_at = now
        job.updated_at = now

        # Update Analysis status to PROCESSING if QUEUED
        analysis = db.query(Analysis).filter(Analysis.id == job.analysis_id).first()
        if analysis and analysis.status == "QUEUED":
            analysis.status = "PROCESSING"
            analysis.started_at = now

        db.commit()

        logger.info(
            "job_claimed",
            job_id=str(job.id),
            analysis_id=str(job.analysis_id),
            worker_id=worker_id,
            lease_token=new_token,
            expires_at=lease_expires.isoformat(),
        )

        return JobClaim(
            job_id=job.id,
            analysis_id=job.analysis_id,
            lease_token=new_token,
            lease_owner=worker_id,
            lease_expires_at=lease_expires,
            retry_count=job.retry_count,
            max_retries=job.max_retries,
        )

    @staticmethod
    def renew_lease(
        db: Session,
        job_id: uuid.UUID,
        lease_token: int,
        worker_id: str,
        lease_duration: timedelta = timedelta(minutes=10),
    ) -> bool:
        """
        Extends lease expiration and heartbeat timestamp.
        Returns True if successful, False if fenced or expired.
        """
        now = utc_now()
        job = (
            db.query(AnalysisJob)
            .filter(
                AnalysisJob.id == job_id,
                AnalysisJob.lease_token == lease_token,
                AnalysisJob.lease_owner == worker_id,
                AnalysisJob.status == "RUNNING",
            )
            .first()
        )

        if not job:
            logger.warning(
                "lease_renewal_rejected_fenced",
                job_id=str(job_id),
                worker_id=worker_id,
                lease_token=lease_token,
            )
            return False

        lease_exp = ensure_utc(job.lease_expires_at)
        if lease_exp and lease_exp < now:
            logger.warning(
                "lease_renewal_rejected_expired",
                job_id=str(job_id),
                worker_id=worker_id,
                lease_token=lease_token,
            )
            return False

        job.lease_expires_at = now + lease_duration
        job.heartbeat_at = now
        job.updated_at = now
        db.commit()

        logger.debug(
            "lease_renewed",
            job_id=str(job_id),
            worker_id=worker_id,
            lease_token=lease_token,
        )
        return True

    @staticmethod
    def mark_job_succeeded(
        db: Session,
        job_id: uuid.UUID,
        lease_token: int,
        worker_id: str,
    ) -> None:
        """
        Transitions job to SUCCEEDED and updates Analysis to COMPLETED or REQUIRES_REVIEW.
        """
        now = utc_now()
        job = (
            db.query(AnalysisJob)
            .filter(
                AnalysisJob.id == job_id,
                AnalysisJob.lease_token == lease_token,
                AnalysisJob.lease_owner == worker_id,
                AnalysisJob.status == "RUNNING",
            )
            .first()
        )

        lease_exp = ensure_utc(job.lease_expires_at) if job else None
        if not job or (lease_exp and lease_exp < now):
            raise WorkerFencedError(
                f"Cannot mark job {job_id} succeeded: lease is fenced or expired."
            )

        job.status = "SUCCEEDED"
        job.lease_owner = None
        job.lease_expires_at = None
        job.updated_at = now

        analysis = db.query(Analysis).filter(Analysis.id == job.analysis_id).first()
        if analysis:
            if analysis.review_required:
                analysis.status = "REQUIRES_REVIEW"
            else:
                analysis.status = "COMPLETED"
            analysis.completed_at = now

        db.commit()
        logger.info(
            "job_succeeded",
            job_id=str(job_id),
            analysis_id=str(job.analysis_id),
            status=job.status,
        )

    @staticmethod
    def mark_job_failed(
        db: Session,
        job_id: uuid.UUID,
        lease_token: int,
        worker_id: str,
        error_message: str,
    ) -> None:
        """
        Increments retry_count, computes exponential backoff, or transitions to DEAD.
        """
        now = utc_now()
        job = (
            db.query(AnalysisJob)
            .filter(
                AnalysisJob.id == job_id,
                AnalysisJob.lease_token == lease_token,
                AnalysisJob.lease_owner == worker_id,
                AnalysisJob.status == "RUNNING",
            )
            .first()
        )

        lease_exp = ensure_utc(job.lease_expires_at) if job else None
        if not job or (lease_exp and lease_exp < now):
            # Worker is fenced — per ERROR-CONTRACT.md, do not increment retry_count!
            logger.warning(
                "mark_failed_skipped_worker_fenced",
                job_id=str(job_id),
                worker_id=worker_id,
            )
            raise WorkerFencedError(f"Job {job_id} was already fenced or expired.")

        new_retry_count = job.retry_count + 1
        job.retry_count = new_retry_count
        job.last_error = error_message[:1000]
        job.lease_owner = None
        job.lease_expires_at = None
        job.heartbeat_at = None
        job.updated_at = now

        analysis = db.query(Analysis).filter(Analysis.id == job.analysis_id).first()

        if new_retry_count >= job.max_retries:
            job.status = "DEAD"
            job.backoff_until = None
            if analysis:
                analysis.status = "FAILED"
                analysis.error_detail = error_message[:1000]
                analysis.completed_at = now
            logger.error(
                "alert_job_dead",
                job_id=str(job_id),
                analysis_id=str(job.analysis_id),
                retry_count=new_retry_count,
                error=error_message[:200],
            )
        else:
            job.status = "FAILED"
            delay = compute_backoff_delay(new_retry_count - 1)
            job.backoff_until = now + delay
            logger.warning(
                "job_failed_backoff_scheduled",
                job_id=str(job_id),
                analysis_id=str(job.analysis_id),
                retry_count=new_retry_count,
                backoff_seconds=delay.total_seconds(),
            )

        db.commit()

    @staticmethod
    def release_fenced_job(
        db: Session,
        job_id: uuid.UUID,
        worker_id: str,
    ) -> None:
        """
        Releases a job after a WorkerFencedError.
        Per docs/ERROR-CONTRACT.md:
        retry_count is NOT incremented (fencing is a coordination event, not execution failure).
        """
        job = (
            db.query(AnalysisJob)
            .filter(
                AnalysisJob.id == job_id,
                AnalysisJob.lease_owner == worker_id,
            )
            .first()
        )

        if job:
            job.status = "PENDING"
            job.lease_owner = None
            job.lease_expires_at = None
            job.heartbeat_at = None
            job.updated_at = utc_now()
            db.commit()

        logger.info(
            "worker_fenced_job_released",
            job_id=str(job_id),
            worker_id=worker_id,
        )
