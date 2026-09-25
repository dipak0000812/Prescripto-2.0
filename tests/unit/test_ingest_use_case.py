"""
Unit tests for IngestPrescription Use Case and file validation.
"""
import pytest

from prescripto.application.use_cases.ingest_prescription import (
    detect_file_format_and_validate,
)
from prescripto.application.exceptions import (
    UnsupportedMediaTypeException,
    FileTooLargeException,
    PdfActiveContentRejectedException,
    MalformedRequestException,
)


def test_magic_bytes_detection_jpeg():
    raw_jpeg = b"\xFF\xD8\xFF\xE0" + b"\x00" * 50
    mime, ext = detect_file_format_and_validate(raw_jpeg)
    assert mime == "image/jpeg"
    assert ext == "jpg"


def test_magic_bytes_detection_png():
    raw_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    mime, ext = detect_file_format_and_validate(raw_png)
    assert mime == "image/png"
    assert ext == "png"


def test_magic_bytes_detection_tiff_little_endian():
    raw_tiff = b"II*\x00" + b"\x00" * 50
    mime, ext = detect_file_format_and_validate(raw_tiff)
    assert mime == "image/tiff"
    assert ext == "tiff"


def test_magic_bytes_detection_tiff_big_endian():
    raw_tiff = b"MM\x00*" + b"\x00" * 50
    mime, ext = detect_file_format_and_validate(raw_tiff)
    assert mime == "image/tiff"
    assert ext == "tiff"


def test_magic_bytes_detection_clean_pdf():
    raw_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj"
    mime, ext = detect_file_format_and_validate(raw_pdf)
    assert mime == "application/pdf"
    assert ext == "pdf"


def test_magic_bytes_detection_unsupported():
    text_data = b"Hello, this is just a plain text prescription note."
    with pytest.raises(UnsupportedMediaTypeException):
        detect_file_format_and_validate(text_data)


def test_empty_file_rejected():
    with pytest.raises(MalformedRequestException):
        detect_file_format_and_validate(b"")


def test_oversized_file_rejected():
    oversized = b"\xFF\xD8\xFF" + b"\x00" * (20 * 1024 * 1024 + 1)
    with pytest.raises(FileTooLargeException):
        detect_file_format_and_validate(oversized)


def test_pdf_active_content_javascript_rejected():
    dangerous_pdf = b"%PDF-1.4\n<< /S /JavaScript /JS (app.alert('pwned');) >>"
    with pytest.raises(PdfActiveContentRejectedException):
        detect_file_format_and_validate(dangerous_pdf)


def test_pdf_active_content_launch_rejected():
    dangerous_pdf = b"%PDF-1.4\n<< /S /Launch /F (cmd.exe) >>"
    with pytest.raises(PdfActiveContentRejectedException):
        detect_file_format_and_validate(dangerous_pdf)
