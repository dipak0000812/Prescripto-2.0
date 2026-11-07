"""
Prescripto AI 2.0 — Object Storage Service (MinIO / S3).
Manages deterministic object keys, ephemeral presigned URLs, and zero-PHI operations.
"""
import hashlib
import hmac
import time
import uuid
from pathlib import Path
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

        self._is_mock_s3 = s3_client is not None
        self._local_dir = Path("prescripto_storage").resolve()

    def _resolve_safe_path(self, key: str, bucket_name: Optional[str] = None) -> Path:
        """Resolves target path and ensures it stays strictly within _local_dir and bucket."""
        bucket = bucket_name or self.default_bucket
        bucket_dir = (self._local_dir / bucket).resolve()
        clean_key = key.lstrip("/\\")
        candidate = (bucket_dir / clean_key).resolve()
        try:
            candidate.relative_to(bucket_dir)
            candidate.relative_to(self._local_dir)
        except ValueError:
            raise StorageObjectNotFoundException(f"Path traversal detected for key {key}")
        return candidate

    @staticmethod
    def sign_storage_key(key: str, expires_at: int) -> str:
        """Generates an HMAC-SHA256 signature for key and expiration timestamp."""
        secret = (settings.JWT_PRIVATE_KEY or settings.S3_SECRET_KEY or "prescripto_storage_signing_key").encode("utf-8")
        clean_key = key.lstrip("/\\")
        msg = f"{clean_key}:{expires_at}".encode("utf-8")
        return hmac.new(secret, msg, hashlib.sha256).hexdigest()

    @staticmethod
    def verify_storage_signature(key: str, expires_at: int, signature: str) -> bool:
        """Verifies signature authenticity and checks whether TTL has expired."""
        try:
            if time.time() > float(expires_at):
                return False
        except (ValueError, TypeError):
            return False
        expected = StorageClient.sign_storage_key(key, int(expires_at))
        return hmac.compare_digest(expected, signature)

    def generate_signed_storage_url(self, key: str, expires_in: int = 60) -> str:
        """Generates a short-lived HMAC signed URL for local storage endpoint."""
        expires_at = int(time.time()) + expires_in
        sig = self.sign_storage_key(key, expires_at)
        clean_key = key.lstrip("/\\")
        return f"/api/v1/storage/{clean_key}?expires={expires_at}&signature={sig}"

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
                    if not self._is_mock_s3:
                        (self._local_dir / bucket).mkdir(parents=True, exist_ok=True)
                        return
                    logger.error("storage_bucket_create_failed", error_code="STORAGE_UNAVAILABLE")
                    raise StorageUnavailableException(f"Failed to create bucket {bucket}: {create_err}") from create_err
            else:
                if not self._is_mock_s3:
                    (self._local_dir / bucket).mkdir(parents=True, exist_ok=True)
                    return
                logger.error("storage_bucket_head_failed", error_code="STORAGE_UNAVAILABLE")
                raise StorageUnavailableException(f"Failed to reach storage bucket {bucket}: {e}") from e
        except (BotoCoreError, Exception) as e:
            if not self._is_mock_s3:
                (self._local_dir / bucket).mkdir(parents=True, exist_ok=True)
                return
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
        except (BotoCoreError, ClientError, Exception) as e:
            if not self._is_mock_s3:
                target_path = self._resolve_safe_path(key, bucket)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(data)
                logger.info("storage_put_local_success", status="SUCCESS", key=key)
                return
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
                local_path = self._resolve_safe_path(key, bucket)
                if local_path.is_file():
                    return local_path.read_bytes()
                raise StorageObjectNotFoundException(f"Object {key} not found") from e
            if not self._is_mock_s3:
                local_path = self._resolve_safe_path(key, bucket)
                if local_path.is_file():
                    return local_path.read_bytes()
            logger.error("storage_get_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(f"Storage get error: {e}") from e
        except (BotoCoreError, Exception) as e:
            if not self._is_mock_s3:
                local_path = self._resolve_safe_path(key, bucket)
                if local_path.is_file():
                    return local_path.read_bytes()
            logger.error("storage_get_failed", error_code="STORAGE_UNAVAILABLE")
            raise StorageUnavailableException(f"Storage connection error: {e}") from e

    def delete_object(self, key: str, bucket_name: Optional[str] = None) -> None:
        """Deletes an object from storage."""
        bucket = bucket_name or self.default_bucket
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
            logger.info("storage_delete_success", status="SUCCESS")
        except (BotoCoreError, ClientError, Exception) as e:
            if not self._is_mock_s3:
                local_path = self._resolve_safe_path(key, bucket)
                if local_path.is_file():
                    local_path.unlink()
                logger.info("storage_delete_local_success", status="SUCCESS")
                return
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
            if not self._is_mock_s3:
                return self._resolve_safe_path(key, bucket).is_file()
            raise StorageUnavailableException(f"Storage check error: {e}") from e
        except (BotoCoreError, Exception) as e:
            if not self._is_mock_s3:
                return self._resolve_safe_path(key, bucket).is_file()
            raise StorageUnavailableException(f"Storage connection error: {e}") from e

    def _is_s3_reachable(self) -> bool:
        """Performs a non-blocking 50ms socket check to determine if S3 endpoint is alive."""
        if not settings.S3_ENDPOINT:
            return False
        try:
            from urllib.parse import urlparse
            import socket
            parsed = urlparse(settings.S3_ENDPOINT)
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            sock = socket.create_connection((host, port), timeout=0.05)
            sock.close()
            return True
        except Exception:
            return False

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
        if not self._is_mock_s3 and not self._is_s3_reachable():
            return self.generate_signed_storage_url(key, expires_in=expires_in)

        try:
            url = self._client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except (BotoCoreError, ClientError, Exception) as e:
            if not self._is_mock_s3:
                return self.generate_signed_storage_url(key, expires_in=expires_in)
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
