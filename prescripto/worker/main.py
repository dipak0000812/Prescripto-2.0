"""
Prescripto AI 2.0 — Analysis Worker Entrypoint.
Runs the fenced pipeline processor (Phase 3 / Slice 2).
"""
import sys
import time
from prescripto.config.settings import settings
from prescripto.audit.logger import configure_logging, get_logger

configure_logging(settings.LOG_LEVEL)
logger = get_logger("prescripto.worker")


def main() -> None:
    logger.info(
        "worker_started",
        model_version_id=f"{settings.OCR_MODEL_NAME}:{settings.OCR_MODEL_VERSION}",
        status="RUNNING",
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("worker_stopped", status="STOPPED")
        sys.exit(0)


if __name__ == "__main__":
    main()
