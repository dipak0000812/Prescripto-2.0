"""
Prescripto AI 2.0 — Pure Domain Prescription Exceptions.
Strict Layering: Zero external dependencies (pure Python).
"""


class DomainException(Exception):
    """Base exception for all domain business rule violations."""
    pass


class UnsupportedMediaFormatException(DomainException):
    """Raised when document magic bytes do not match permitted MIME types."""
    pass


class FileSizeExceededException(DomainException):
    """Raised when file size exceeds the upper limit (20MB)."""
    pass


class ActiveContentDetectedException(DomainException):
    """Raised when an uploaded PDF contains executable active content (e.g. JavaScript)."""
    pass


class InvalidDocumentStateException(DomainException):
    """Raised when a state transition is not allowed for the prescription document."""
    pass
