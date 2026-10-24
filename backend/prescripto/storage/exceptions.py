"""
Prescripto AI 2.0 — Storage Exceptions.
"""


class StorageException(Exception):
    """Base exception for storage operations."""
    pass


class StorageUnavailableException(StorageException):
    """Raised when object storage (MinIO / S3) is unreachable."""
    pass


class StorageObjectNotFoundException(StorageException):
    """Raised when an object key is not found in storage."""
    pass
