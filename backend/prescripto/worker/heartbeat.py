"""
Worker Lease Heartbeat Mechanism.
Periodically extends lease expiration and heartbeat timestamp during stage processing.
Detects lease expiration and worker fencing asynchronously.
"""
import threading
import time
from datetime import timedelta
from typing import Callable, Optional
from sqlalchemy.orm import Session

from prescripto.worker.queue import JobClaim, QueuePoller
from prescripto.worker.exceptions import WorkerFencedError
from prescripto.audit.logger import get_logger

logger = get_logger("prescripto.worker.heartbeat")


class HeartbeatManager:
    """
    Context manager and background thread that pulses lease renewals on active jobs.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        claim: JobClaim,
        interval_seconds: float = 30.0,
        lease_duration_seconds: int = 600,
        close_session: bool = True,
    ) -> None:
        self.session_factory = session_factory
        self.claim = claim
        self.interval_seconds = interval_seconds
        self.lease_duration = timedelta(seconds=lease_duration_seconds)
        self.close_session = close_session
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.is_fenced: bool = False
        self.last_heartbeat_time: float = 0.0

    def pulse(self) -> bool:
        """Executes a single synchronous heartbeat renewal."""
        db: Session = self.session_factory()
        try:
            success = QueuePoller.renew_lease(
                db=db,
                job_id=self.claim.job_id,
                lease_token=self.claim.lease_token,
                worker_id=self.claim.lease_owner,
                lease_duration=self.lease_duration,
            )
            if success:
                self.last_heartbeat_time = time.time()
            else:
                self.is_fenced = True
                logger.warning(
                    "heartbeat_detected_fencing",
                    job_id=str(self.claim.job_id),
                    lease_token=self.claim.lease_token,
                    worker_id=self.claim.lease_owner,
                )
            return success
        except Exception as e:
            logger.error("heartbeat_error", error=str(e))
            return False
        finally:
            if self.close_session:
                db.close()

    def _run_loop(self) -> None:
        """Background loop executing heartbeats at regular intervals."""
        while not self._stop_event.wait(self.interval_seconds):
            if self._stop_event.is_set():
                break
            success = self.pulse()
            if not success:
                self.is_fenced = True
                break

    def start(self) -> "HeartbeatManager":
        """Starts the background heartbeat thread."""
        self._stop_event.clear()
        self.is_fenced = False
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"Heartbeat-{self.claim.job_id}",
            daemon=True,
        )
        self._thread.start()
        logger.debug("heartbeat_started", job_id=str(self.claim.job_id))
        return self

    def stop(self) -> None:
        """Stops the heartbeat thread."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.debug("heartbeat_stopped", job_id=str(self.claim.job_id))

    def check_fence(self) -> None:
        """Raises WorkerFencedError if the heartbeat detected lease loss."""
        if self.is_fenced:
            raise WorkerFencedError(
                f"Worker '{self.claim.lease_owner}' with token {self.claim.lease_token} lost its lease."
            )

    def __enter__(self) -> "HeartbeatManager":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
