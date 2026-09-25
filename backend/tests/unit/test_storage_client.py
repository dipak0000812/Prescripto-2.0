"""
Unit tests for MinIO / S3 Storage Client.
"""
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
