"""
Cryptographic Utilities: Password Hashing (bcrypt) and RS256 JWT Signing/Verification.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import bcrypt
import jwt
from prescripto.config.settings import settings


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(
    user_id: uuid.UUID,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, int]:
    """Issues an RS256 signed JWT access token."""
    now = datetime.now(timezone.utc)
    ttl_seconds = int(expires_delta.total_seconds()) if expires_delta else settings.JWT_ACCESS_TTL
    expires_at = now + timedelta(seconds=ttl_seconds)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm="RS256")
    return token, ttl_seconds


def create_refresh_token(
    user_id: uuid.UUID,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, str, datetime]:
    """Issues an RS256 signed JWT refresh token with a unique jti."""
    now = datetime.now(timezone.utc)
    ttl_seconds = int(expires_delta.total_seconds()) if expires_delta else settings.JWT_REFRESH_TTL
    expires_at = now + timedelta(seconds=ttl_seconds)
    jti = str(uuid.uuid4())

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm="RS256")
    return token, jti, expires_at


def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates an RS256 JWT using the public key."""
    try:
        return jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=["RS256"],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise
