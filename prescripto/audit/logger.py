"""
Prescripto AI 2.0 — Zero-PHI Structured Logging.
Strict whitelist-based logging processor per docs/SECURITY.md and docs/Architecture.md.
Drops any field not explicitly on the permitted whitelist to guarantee zero PHI in operational logs.
"""
import logging
import sys
from typing import Any, Dict, MutableMapping
import structlog

# Strictly permitted keys in operational logs per docs/SECURITY.md
PERMITTED_LOG_KEYS = {
    "event",
    "level",
    "timestamp",
    "logger",
    "logger_name",
    "request_id",
    "analysis_id",
    "document_id",
    "pipeline_stage",
    "model_version_id",
    "status",
    "duration_ms",
    "error_code",
    "actor_id",
    "http_method",
    "http_path",
    "http_status_code",
}


def phi_whitelist_filter(
    logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """
    Strips any key not in PERMITTED_LOG_KEYS to prevent accidental PHI logging.
    Increments a metric counter or records stripped count if unlisted fields are detected.
    """
    keys_to_remove = [k for k in event_dict.keys() if k not in PERMITTED_LOG_KEYS]
    if keys_to_remove:
        event_dict["_dropped_unwhitelisted_keys_count"] = len(keys_to_remove)
        for k in keys_to_remove:
            del event_dict[k]
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configures structlog and standard logging with the PHI whitelist filter."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        phi_whitelist_filter,
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))


def get_logger(name: str = "prescripto") -> structlog.stdlib.BoundLogger:
    """Returns a structlog bound logger configured with PHI safety filters."""
    return structlog.get_logger(name)
