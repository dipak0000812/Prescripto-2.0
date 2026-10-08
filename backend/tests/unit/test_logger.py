"""
Unit tests for Zero-PHI Logging System.
"""
from prescripto.audit.logger import phi_whitelist_filter, PERMITTED_LOG_KEYS


def test_phi_whitelist_filter_strips_sensitive_data():
    event_dict = {
        "event": "prescription_scanned",
        "level": "info",
        "request_id": "123e4567-e89b-12d3-a456-426614174000",
        "patient_name": "Ramesh Kumar",  # Sensitive PHI
        "medication_name": "Paracetamol 500mg",  # Sensitive PHI
        "ocr_raw_buffer": "Rx: Take 1 tab daily",  # Sensitive OCR text
        "presigned_url": "https://s3.amazonaws.com/prescripto/secret-image",  # Bearer URL
    }

    filtered = phi_whitelist_filter(None, "info", event_dict)

    # Permitted fields must be preserved
    assert filtered["event"] == "prescription_scanned"
    assert filtered["level"] == "info"
    assert filtered["request_id"] == "123e4567-e89b-12d3-a456-426614174000"

    # PHI and sensitive fields must be dropped
    assert "patient_name" not in filtered
    assert "medication_name" not in filtered
    assert "ocr_raw_buffer" not in filtered
    assert "presigned_url" not in filtered

    # Warning count must reflect dropped keys
    assert filtered["_dropped_unwhitelisted_keys_count"] == 4


def test_permitted_keys_integrity():
    required_permitted = {
        "request_id",
        "analysis_id",
        "document_id",
        "error_code",
        "status",
        "job_id",
        "worker_id",
        "lease_token",
        "error_type",
    }
    assert required_permitted.issubset(PERMITTED_LOG_KEYS)


def test_stdlib_log_record_formatting_with_phi_filter():
    """
    Verify that:
    1. A whitelisted key is kept.
    2. patient_name='x' is dropped.
    3. Standard library LogRecord formatted via ProcessorFormatter does not raise KeyError: '_record'.
    """
    import logging
    from prescripto.audit.logger import configure_logging

    configure_logging("INFO")
    std_logger = logging.getLogger("prescripto.test_stdlib")

    # Logging via standard library logger with extra fields
    # Must not raise KeyError: '_record'
    std_logger.info("Test stdlib log", extra={"request_id": "req-123", "patient_name": "x"})

    # Direct processor check verifying exact structlog metadata preservation
    event_dict = {
        "event": "system_startup",
        "request_id": "req-456",
        "patient_name": "x",
        "_record": logging.LogRecord("test", logging.INFO, "test.py", 1, "msg", (), None),
        "_from_structlog": False,
    }
    filtered = phi_whitelist_filter(std_logger, "info", event_dict)
    assert filtered["request_id"] == "req-456"
    assert "patient_name" not in filtered
    assert "_record" in filtered
    assert "_from_structlog" in filtered

