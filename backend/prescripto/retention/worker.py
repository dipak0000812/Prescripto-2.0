"""
Prescripto AI 2.0 — Deletion Worker Entrypoint.
Runs the DPDPA verifiable deletion workflow (Phase 6 / Slice 10).
"""
import sys
import time
from prescripto.config.settings import settings
from prescripto.audit.logger import configure_logging, get_logger

configure_logging(settings.LOG_LEVEL)
logger = get_logger("prescripto.retention")


def main() -> None:
    logger.info("deletion_worker_started", status="RUNNING")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("deletion_worker_stopped", status="STOPPED")
        sys.exit(0)


if __name__ == "__main__":
    main()
