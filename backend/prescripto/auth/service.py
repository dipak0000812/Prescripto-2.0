"""
Authentication Service: user credential verification, token issuance, and refresh with blocklist check.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from prescripto.db.models.users import User
from prescripto.db.models.retention import TokenBlocklist
from prescripto.auth.crypto import (
    verify_password, create_access_token, create_refresh_token, decode_token
)
from prescripto.auth.exceptions import (
    InvalidCredentialsException,
    TokenExpiredException,
    TokenRevokedException,
    BlocklistUnavailableException,
)


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User:
        user = db.query(User).filter(User.username == username, User.is_active == True).first()
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        return user

    @staticmethod
    def create_token_pair(user: User) -> Dict[str, Any]:
        access_token, expires_in = create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
        )
        refresh_token, jti, refresh_exp = create_refresh_token(user_id=user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }

    @staticmethod
    def refresh_session(db: Session, refresh_token_str: str) -> Dict[str, Any]:
        try:
            payload = decode_token(refresh_token_str)
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise InvalidCredentialsException("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise InvalidCredentialsException("Token is not a refresh token")

        user_id_str = payload.get("sub")
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not user_id_str or not jti:
            raise InvalidCredentialsException("Malformed refresh token payload")

        # Check PostgreSQL blocklist - FAILS CLOSED if database is unavailable
        try:
            is_revoked = db.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).first()
            if is_revoked:
                raise TokenRevokedException()
        except TokenRevokedException:
            raise
        except SQLAlchemyError as exc:
            # Mandatory failure closure per SECURITY.md
            raise BlocklistUnavailableException() from exc

        # Retrieve user
        user = db.query(User).filter(User.id == uuid.UUID(user_id_str), User.is_active == True).first()
        if not user:
            raise InvalidCredentialsException("User not found or inactive")

        # Revoke old refresh token by adding to blocklist
        try:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
            revoked_entry = TokenBlocklist(
                jti=jti,
                user_id=user.id,
                expires_at=expires_at,
            )
            db.add(revoked_entry)
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise BlocklistUnavailableException() from exc

        # Issue new token pair
        return AuthService.create_token_pair(user)
