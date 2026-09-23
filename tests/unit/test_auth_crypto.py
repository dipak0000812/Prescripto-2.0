"""
Unit tests for password hashing and RS256 token operations.
"""
import uuid
import time
from datetime import timedelta
import pytest
import jwt
from prescripto.auth.crypto import (
    hash_password, verify_password, create_access_token, create_refresh_token, decode_token
)


def test_password_hashing():
    pw = "SuperSecurePassword123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_access_token_creation_and_decode():
    user_id = uuid.uuid4()
    token, ttl = create_access_token(user_id=user_id, username="dr_sharma", role="REVIEWER")
    assert isinstance(token, str)
    assert ttl == 900

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["username"] == "dr_sharma"
    assert payload["role"] == "REVIEWER"
    assert payload["type"] == "access"


def test_refresh_token_creation_and_jti():
    user_id = uuid.uuid4()
    token, jti, exp = create_refresh_token(user_id=user_id)
    assert isinstance(token, str)
    assert isinstance(jti, str)

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["jti"] == jti
    assert payload["type"] == "refresh"


def test_expired_token_raises_error():
    user_id = uuid.uuid4()
    token, _ = create_access_token(
        user_id=user_id,
        username="expired_user",
        role="OPERATOR",
        expires_delta=timedelta(seconds=-10),  # expired 10s ago
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)
