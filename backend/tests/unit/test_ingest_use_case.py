"""Unit tests for upload image validation and IngestPrescription."""
import io

import pytest
from PIL import Image

from prescripto.application.use_cases.ingest_prescription import (
    detect_file_format_and_validate,
)
from prescripto.application.exceptions import (
    UnsupportedMediaTypeException,
    FileTooLargeException,
    MalformedRequestException,
)


def make_image_bytes(image_format: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format=image_format)
    return buffer.getvalue()


def test_magic_bytes_detection_jpeg():
    raw_jpeg = make_image_bytes("JPEG")
    mime, ext = detect_file_format_and_validate(raw_jpeg)
    assert mime == "image/jpeg"
    assert ext == "jpg"


def test_magic_bytes_detection_png():
    raw_png = make_image_bytes("PNG")
    mime, ext = detect_file_format_and_validate(raw_png)
    assert mime == "image/png"
    assert ext == "png"


def test_magic_bytes_detection_tiff_little_endian():
    raw_tiff = make_image_bytes("TIFF")
    assert raw_tiff.startswith(b"II*\x00")
    mime, ext = detect_file_format_and_validate(raw_tiff)
    assert mime == "image/tiff"
    assert ext == "tiff"


def test_magic_bytes_detection_tiff_big_endian():
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="TIFF", byteorder=">")
    raw_tiff = buffer.getvalue()
    mime, ext = detect_file_format_and_validate(raw_tiff)
    assert mime == "image/tiff"
    assert ext == "tiff"


@pytest.mark.parametrize(
    "pdf_bytes",
    [
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj",
        b"%PDF-1.4\n<< /S /JavaScript /JS (app.alert('pwned');) >>",
        b"%PDF-1.4\n<< /S /Launch /F (cmd.exe) >>",
    ],
)
def test_pdf_uploads_rejected_as_unsupported(pdf_bytes):
    with pytest.raises(UnsupportedMediaTypeException):
        detect_file_format_and_validate(pdf_bytes)


def test_magic_bytes_detection_unsupported():
    text_data = b"Hello, this is just a plain text prescription note."
    with pytest.raises(UnsupportedMediaTypeException):
        detect_file_format_and_validate(text_data)


def test_empty_file_rejected():
    with pytest.raises(MalformedRequestException):
        detect_file_format_and_validate(b"")


def test_invalid_image_with_jpeg_signature_is_rejected():
    with pytest.raises(MalformedRequestException, match="valid, readable"):
        detect_file_format_and_validate(b"\xFF\xD8\xFFnot-a-real-jpeg")


def test_oversized_file_rejected():
    oversized = b"\xFF\xD8\xFF" + b"\x00" * (20 * 1024 * 1024 + 1)
    with pytest.raises(FileTooLargeException):
        detect_file_format_and_validate(oversized)
