"""
Prescripto AI 2.0 — Object Storage Service (MinIO / S3).
Manages deterministic object keys, ephemeral presigned URLs, and zero-PHI operations.
"""
import uuid
from typing import Optional, Union
import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from prescripto.config.settings import settings
from prescripto.audit.logger import get_logger
from prescripto.storage.exceptions import (
    StorageException,
    StorageUnavailableException,
    StorageObjectNotFoundException,
)

logger = get_logger("prescripto.storage")


class StorageClient:
    """S3-compatible client for prescription document storage and retrieval."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: Optional[str] = None,
        default_bucket: Optional[str] = None,
        s3_client: Optional[BaseClient] = None,
    ) -> None:
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT
        self.access_key = access_key or settings.S3_ACCESS_KEY
        self.secret_key = secret_key or settings.S3_SECRET_KEY
        self.region = region or settings.S3_REGION
        self.default_bucket = default_bucket or settings.S3_BUCKET

        if s3_client is not None:
            self._client = s3_client
        else:
            config = Config(
                connect_timeout=2.0,
                read_timeout=5.0,
                retries={"max_attempts": 2},
                s3={"addressing_style": "path"},
            )
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=config,
            )

    @staticmethod
    def generate_prescription_key(document_id: Union[uuid.UUID, str], extension: str) -> str:
        """
        Generates deterministic key per docs/DATA-SPECIFICATION.md:
        prescriptions/{document_id}/original.{ext}
        """
        clean_ext = extension.lstrip(".").lower()
        if not clean_ext:
            clean_ext = "bin"
        return f"prescriptions/{document_id}/original.{clean_ext}"

    def ensure_bucket_exists(self, bucket_name: Optional[str] = None) -> None:
        """Idempotently ensures that the target bucket exists."""
        bucket = bucket_name or self.default_bucket
        try:
            self._client.head_bucket(Bucket=bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                try:
                    if self.region == "us-east-1":
                        self._client.create_bucket(Bucket=bucket)
                    else:
                        self._client.create_bucket(
                            Bucket=bucket,
                            CreateBucketConfiguration={"LocationConstraint": self.region},
                        )
                    logger.info("storage_bucket_created", status="SUCCESS")
                except Exception as create_err:
                    logger.error("storage_bucket_create_failed", error_code="STORAGE_UNAVAILABLE")
                    raise StorageUnavailableException(f"Failed to create bucket {bucket}: {create_err}") from create_err
            else:
                logger.error("storage_bucket_head_failed", error_code="STORAGE_UNAVAILABLE")
                raise StorageUnavailableException(f"Failed to reach storage bucket {bucket}: {e}") from e
        except (BotoCoreError, Exception) as e:
            logger.error("storage_connection_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(f"Storage connection failed: {e}") from e

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str,
        bucket_name: Optional[str] = None,
    ) -> None:
        """Uploads binary data to object storage."""
        bucket = bucket_name or self.default_bucket
        try:
            self._client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            logger.info("storage_put_success", status="SUCCESS")
        except (BotoCoreError, ClientError) as e:
            logger.error("storage_put_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(f"Failed to write object to storage: {e}") from e

    def get_object(self, key: str, bucket_name: Optional[str] = None) -> bytes:
        """Retrieves binary data of an object from storage."""
        bucket = bucket_name or self.default_bucket
        try:
            response = self._client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("NoSuchKey", "404"):
                raise StorageObjectNotFoundException(f"Object {key} not found") from e
            logger.error("storage_get_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(f"Storage get error: {e}") from e
        except BotoCoreError as e:
            logger.error("storage_get_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(f"Storage connection error: {e}") from e

    def delete_object(self, key: str, bucket_name: Optional[str] = None) -> None:
        """Deletes an object from storage."""
        bucket = bucket_name or self.default_bucket
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
            logger.info("storage_delete_success", status="SUCCESS")
        except (BotoCoreError, ClientError) as e:
            logger.error("storage_delete_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(f"Storage delete error: {e}") from e

    def object_exists(self, key: str, bucket_name: Optional[str] = None) -> bool:
        """Checks if an object exists in storage."""
        bucket = bucket_name or self.default_bucket
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                return False
            raise StorageUnavailableException(f"Storage check error: {e}") from e
        except BotoCoreError as e:
            raise StorageUnavailableException(f"Storage connection error: {e}") from e

    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 60,
        bucket_name: Optional[str] = None,
    ) -> str:
        """
        Generates an ephemeral presigned GET URL (default 60s TTL).
        Per security guidelines: bearer capability, NEVER persisted or logged.
        """
        bucket = bucket_name or self.default_bucket
        try:
            url = self._client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except (BotoCoreError, ClientError) as e:
            logger.error("presigned_url_generation_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(f"Failed to generate presigned URL: {e}") from e


# Singleton instance for dependency injection
_storage_client: Optional[StorageClient] = None


def get_storage_client() -> StorageClient:
    """FastAPI and Application dependency returning the configured StorageClient."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
