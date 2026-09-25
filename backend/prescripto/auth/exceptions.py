"""
Auth Domain Exceptions matching docs/ERROR-CONTRACT.md.
"""
from fastapi import HTTPException, status


class AuthException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
        self.code = code
        self.message = message


class InvalidCredentialsException(AuthException):
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", message)


class TokenExpiredException(AuthException):
    def __init__(self, message: str = "Token has expired"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "TOKEN_EXPIRED", message)


class TokenRevokedException(AuthException):
    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "TOKEN_REVOKED", message)


class BlocklistUnavailableException(AuthException):
    def __init__(self, message: str = "Token blocklist unavailable — failing closed"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "BLOCKLIST_UNAVAILABLE", message)


class InsufficientRoleException(AuthException):
    def __init__(self, message: str = "Caller lacks sufficient role permissions"):
        super().__init__(status.HTTP_403_FORBIDDEN, "INSUFFICIENT_ROLE", message)


class ForbiddenResourceAccessException(AuthException):
    def __init__(self, message: str = "Access to requested resource is forbidden"):
        super().__init__(status.HTTP_403_FORBIDDEN, "FORBIDDEN_RESOURCE_ACCESS", message)
