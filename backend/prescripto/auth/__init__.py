"""
Auth package exports.
"""
from prescripto.auth.crypto import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from prescripto.auth.service import AuthService
from prescripto.auth.dependencies import get_current_user, require_role, oauth2_scheme
from prescripto.auth.exceptions import (
    AuthException,
    InvalidCredentialsException,
    TokenExpiredException,
    TokenRevokedException,
    BlocklistUnavailableException,
    InsufficientRoleException,
    ForbiddenResourceAccessException,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "AuthService",
    "get_current_user",
    "require_role",
    "oauth2_scheme",
    "AuthException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    "TokenRevokedException",
    "BlocklistUnavailableException",
    "InsufficientRoleException",
    "ForbiddenResourceAccessException",
]
