"""
Unit tests for MinIO / S3 Storage Client.
"""
import time
import uuid
from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError, BotoCoreError

from prescripto.storage.client import StorageClient
from prescripto.storage.exceptions import (
    StorageUnavailableException,
    StorageObjectNotFoundException,
)


def test_deterministic_prescription_key_generation():
    doc_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    key = StorageClient.generate_prescription_key(doc_id, "jpg")
    assert key == "prescriptions/11111111-2222-3333-4444-555555555555/original.jpg"

    key_dot = StorageClient.generate_prescription_key(doc_id, ".PNG")
    assert key_dot == "prescriptions/11111111-2222-3333-4444-555555555555/original.png"


def test_storage_put_and_get_success():
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"prescription-image-data")}

    client = StorageClient(s3_client=mock_s3, default_bucket="test-bucket")
    client.put_object("key/test.jpg", b"prescription-image-data", "image/jpeg")
    mock_s3.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="key/test.jpg",
        Body=b"prescription-image-data",
        ContentType="image/jpeg",
    )

    data = client.get_object("key/test.jpg")
    assert data == b"prescription-image-data"


def test_storage_object_not_found():
    mock_s3 = MagicMock()
    mock_s3.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "GetObject",
    )

    client = StorageClient(s3_client=mock_s3, default_bucket="test-bucket")
    with pytest.raises(StorageObjectNotFoundException):
        client.get_object("missing/key.jpg")


def test_storage_put_unavailable_error():
    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = BotoCoreError()

    client = StorageClient(s3_client=mock_s3, default_bucket="test-bucket")
    with pytest.raises(StorageUnavailableException):
        client.put_object("key/test.jpg", b"data", "image/jpeg")


def test_presigned_url_generation():
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://minio.local/prescripto/key?sig=xyz"

    client = StorageClient(s3_client=mock_s3, default_bucket="test-bucket")
    url = client.generate_presigned_url("prescriptions/id/original.jpg", expires_in=60)
    assert url == "https://minio.local/prescripto/key?sig=xyz"
    mock_s3.generate_presigned_url.assert_called_once_with(
        ClientMethod="get_object",
        Params={"Bucket": "test-bucket", "Key": "prescriptions/id/original.jpg"},
        ExpiresIn=60,
    )


def test_presigned_url_generation_failure():
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.side_effect = ClientError(
        {"Error": {"Code": "InternalError", "Message": "Internal Error"}},
        "generate_presigned_url",
    )

    client = StorageClient(s3_client=mock_s3, default_bucket="test-bucket")
    with pytest.raises(StorageUnavailableException):
        client.generate_presigned_url("some-key")


def test_path_traversal_detection_in_storage_client():
    """Test 5a: Path traversal attempts raise StorageObjectNotFoundException."""
    client = StorageClient(s3_client=MagicMock(), default_bucket="test-bucket")
    traversal_keys = [
        "../../../etc/passwd",
        "..\\..\\windows\\win.ini",
        "prescriptions/../../secret.txt",
    ]
    for key in traversal_keys:
        with pytest.raises(StorageObjectNotFoundException, match="Path traversal detected"):
            client._resolve_safe_path(key)


def test_hmac_signed_storage_url_generation_and_verification():
    """Test 5b: StorageClient creates HMAC-signed URLs and verifies signatures/expiry."""
    import time
    from urllib.parse import urlparse, parse_qs

    client = StorageClient(s3_client=MagicMock(), default_bucket="test-bucket")
    key = "prescriptions/test-id/original.jpg"
    url = client.generate_signed_storage_url(key, expires_in=60)
    assert url.startswith(f"/api/v1/storage/{key}?expires=")

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    expires = int(qs["expires"][0])
    signature = qs["signature"][0]

    # Valid signature
    assert client.verify_storage_signature(key, expires, signature) is True

    # Invalid signature
    assert client.verify_storage_signature(key, expires, "tampered_signature") is False

    # Expired timestamp
    expired_time = int(time.time()) - 10
    expired_sig = client.sign_storage_key(key, expired_time)
    assert client.verify_storage_signature(key, expired_time, expired_sig) is False


def test_storage_endpoint_rejects_missing_or_invalid_signature(client):
    """Test 5c: /api/v1/storage rejects unauthenticated or invalidly signed requests with 403."""
    tc = client
    key = "prescriptions/test-id/original.jpg"

    # Missing signature and expires -> 403 FORBIDDEN_RESOURCE_ACCESS
    res_none = tc.get(f"/api/v1/storage/{key}")
    assert res_none.status_code == 403
    assert res_none.json()["error"]["code"] == "FORBIDDEN_RESOURCE_ACCESS"

    # Invalid signature -> 403 FORBIDDEN_RESOURCE_ACCESS
    res_bad = tc.get(f"/api/v1/storage/{key}?expires=9999999999&signature=invalidsig")
    assert res_bad.status_code == 403
    assert res_bad.json()["error"]["code"] == "FORBIDDEN_RESOURCE_ACCESS"

    # Expired signature -> 403 FORBIDDEN_RESOURCE_ACCESS
    expired_time = 1000000000
    expired_sig = StorageClient.sign_storage_key(key, expired_time)
    res_exp = tc.get(f"/api/v1/storage/{key}?expires={expired_time}&signature={expired_sig}")
    assert res_exp.status_code == 403
    assert res_exp.json()["error"]["code"] == "FORBIDDEN_RESOURCE_ACCESS"

    # Valid signature -> passed auth check, returns 404 (because mock key not on disk), NOT 403!
    valid_sig = StorageClient.sign_storage_key(key, int(time.time()) + 60)
    valid_url = f"/api/v1/storage/{key}?expires={int(time.time()) + 60}&signature={valid_sig}"
    res_valid = tc.get(valid_url)
    assert res_valid.status_code == 404
    assert res_valid.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
