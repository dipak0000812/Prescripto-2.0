"""
Prescripto AI 2.0 — Application Exceptions.
Standard error codes mapped directly to docs/ERROR-CONTRACT.md.
"""


class ApplicationException(Exception):
    """Base application exception carrying machine-readable code and HTTP status code."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class MissingIdempotencyKeyException(ApplicationException):
    def __init__(self, message: str = "Idempotency-Key header is required on upload") -> None:
        super().__init__(code="MISSING_IDEMPOTENCY_KEY", message=message, status_code=400)


class IdempotencyKeyConflictException(ApplicationException):
    def __init__(
        self,
        message: str = "Idempotency-Key reused with a different file hash",
    ) -> None:
        super().__init__(code="IDEMPOTENCY_KEY_CONFLICT", message=message, status_code=409)


class UnsupportedMediaTypeException(ApplicationException):
    def __init__(
        self,
        message: str = "Uploaded file magic bytes do not match supported formats (JPEG, PNG, TIFF, PDF)",
    ) -> None:
        super().__init__(code="UNSUPPORTED_MEDIA_TYPE", message=message, status_code=415)


class FileTooLargeException(ApplicationException):
    def __init__(self, message: str = "Uploaded file exceeds maximum limit of 20MB") -> None:
        super().__init__(code="FILE_TOO_LARGE", message=message, status_code=413)


class PdfActiveContentRejectedException(ApplicationException):
    def __init__(
        self,
        message: str = "PDF contains active or executable content (e.g. JavaScript, Launch action)",
    ) -> None:
        super().__init__(code="PDF_ACTIVE_CONTENT_REJECTED", message=message, status_code=422)


class StorageUnavailableException(ApplicationException):
    def __init__(self, message: str = "Object storage service is temporarily unavailable") -> None:
        super().__init__(code="STORAGE_UNAVAILABLE", message=message, status_code=503)


class ResourceNotFoundException(ApplicationException):
    def __init__(self, message: str = "Requested resource not found") -> None:
        super().__init__(code="RESOURCE_NOT_FOUND", message=message, status_code=404)


class DeletionInProgressException(ApplicationException):
    def __init__(
        self,
        message: str = "Operation cannot be performed on a document undergoing deletion",
    ) -> None:
        super().__init__(code="DELETION_IN_PROGRESS", message=message, status_code=409)


class MalformedRequestException(ApplicationException):
    def __init__(self, message: str = "Malformed request payload") -> None:
        super().__init__(code="MALFORMED_REQUEST", message=message, status_code=400)


class AnalysisNotReadyException(ApplicationException):
    def __init__(self, message: str = "Analysis result is not ready or has failed") -> None:
        super().__init__(code="ANALYSIS_NOT_READY", message=message, status_code=404)


class AnalysisNotReviewableException(ApplicationException):
    def __init__(self, message: str = "Analysis is not in a reviewable state") -> None:
        super().__init__(code="ANALYSIS_NOT_REVIEWABLE", message=message, status_code=409)


class ForbiddenResourceAccessException(ApplicationException):
    def __init__(self, message: str = "Access to the requested resource is forbidden") -> None:
        super().__init__(code="FORBIDDEN_RESOURCE_ACCESS", message=message, status_code=403)

