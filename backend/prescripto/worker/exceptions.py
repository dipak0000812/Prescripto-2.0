"""
Worker Exceptions for Fenced Queue Execution.
"""

class WorkerFencedError(Exception):
    """
    Raised when an atomic commit or operation fails because the worker's lease
    has expired or another worker claimed the job and incremented the generation token.
    Per docs/ERROR-CONTRACT.md:
    This is a coordination event, NOT an execution failure.
    Retry count must NOT be incremented.
    """
    pass


class WorkerJobLostError(Exception):
    """Raised when a job in-flight is no longer valid or deleted."""
    pass
