"""
Prescripto AI 2.0 — Analysis Worker Engine & Entrypoint.
Executes fenced pipeline processor, heartbeat lease renewal, and retry backoff.
"""
import os
import signal
import sys
import time
import uuid
from typing import Callable, Optional
from sqlalchemy.orm import Session

from prescripto.config.settings import settings
from prescripto.audit.logger import configure_logging, get_logger
from prescripto.db.session import SessionLocal
from prescripto.worker.queue import QueuePoller, JobClaim
from prescripto.worker.heartbeat import HeartbeatManager
from prescripto.worker.coordinator import PipelineCoordinator
from prescripto.worker.exceptions import WorkerFencedError

configure_logging(settings.LOG_LEVEL)
logger = get_logger("prescripto.worker")


class WorkerRunner:
    """
    Worker engine polling for queued analysis jobs and orchestrating pipeline stages.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session] = SessionLocal,
        worker_id: Optional[str] = None,
        poll_interval: Optional[float] = None,
        lease_seconds: Optional[int] = None,
        heartbeat_seconds: Optional[int] = None,
        close_session: bool = True,
    ) -> None:
        self.session_factory = session_factory
        self.worker_id = worker_id or settings.WORKER_ID or f"worker-{os.getpid()}-{uuid.uuid4().hex[:6]}"
        self.poll_interval = poll_interval if poll_interval is not None else settings.WORKER_POLL_INTERVAL
        self.lease_seconds = lease_seconds if lease_seconds is not None else settings.WORKER_LEASE_SECONDS
        self.heartbeat_seconds = heartbeat_seconds if heartbeat_seconds is not None else settings.WORKER_HEARTBEAT_SECONDS
        self.close_session = close_session
        self._running = False

    def run_once(self) -> bool:
        """
        Polls for a single job and processes it.
        Returns True if a job was found and processed, False otherwise.
        """
        db: Session = self.session_factory()
        claim: Optional[JobClaim] = None
        try:
            from datetime import timedelta
            claim = QueuePoller.claim_next_job(
                db=db,
                worker_id=self.worker_id,
                lease_duration=timedelta(seconds=self.lease_seconds),
            )

            if not claim:
                return False

            logger.info(
                "job_processing_started",
                job_id=str(claim.job_id),
                analysis_id=str(claim.analysis_id),
                lease_token=claim.lease_token,
                worker_id=self.worker_id,
            )

            # Process job wrapped in heartbeat manager
            with HeartbeatManager(
                session_factory=self.session_factory,
                claim=claim,
                interval_seconds=self.heartbeat_seconds,
                lease_duration_seconds=self.lease_seconds,
                close_session=self.close_session,
            ) as hb:
                coordinator = PipelineCoordinator(db=db, claim=claim)
                coordinator.execute(heartbeat=hb)

            logger.info(
                "job_processing_completed",
                job_id=str(claim.job_id),
                analysis_id=str(claim.analysis_id),
                lease_token=claim.lease_token,
            )
            return True

        except WorkerFencedError as fence_err:
            logger.warning(
                "worker_fenced_execution_halted",
                job_id=str(claim.job_id) if claim else None,
                error=str(fence_err),
            )
            if claim:
                # Per docs/ERROR-CONTRACT.md: do NOT increment retry_count
                QueuePoller.release_fenced_job(db=db, job_id=claim.job_id, worker_id=self.worker_id)
            return True

        except Exception as e:
            logger.error(
                "job_execution_failed",
                job_id=str(claim.job_id) if claim else None,
                error=str(e),
            )
            if claim:
                QueuePoller.mark_job_failed(
                    db=db,
                    job_id=claim.job_id,
                    lease_token=claim.lease_token,
                    worker_id=self.worker_id,
                    error_message=str(e),
                )
            return True

        finally:
            if self.close_session:
                db.close()

    def start(self) -> None:
        """Starts continuous polling worker loop."""
        self._running = True
        logger.info(
            "worker_started",
            worker_id=self.worker_id,
            poll_interval=self.poll_interval,
            lease_seconds=self.lease_seconds,
        )

        while self._running:
            try:
                processed = self.run_once()
                if not processed:
                    time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                logger.info("worker_interrupted_by_user")
                break
            except Exception as e:
                logger.error("worker_loop_exception", error=str(e))
                time.sleep(self.poll_interval)

        logger.info("worker_stopped", worker_id=self.worker_id)

    def stop(self) -> None:
        """Signals worker to stop gracefully."""
        self._running = False


def main() -> None:
    runner = WorkerRunner()

    def handle_signal(sig, frame):
        logger.info("worker_signal_received", signal=sig)
        runner.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    runner.start()


if __name__ == "__main__":
    main()
