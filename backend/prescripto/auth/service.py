"""
Authentication Service: user credential verification, token issuance, and refresh with blocklist check.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
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


import re
import random
from prescripto.db.models.patient import Patient
from prescripto.auth.crypto import hash_password


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, identifier: str, password: str) -> User:
        """Authenticate user by either username or email with password verification."""
        user = db.query(User).filter(
            ((User.username == identifier) | (User.email == identifier)),
            User.is_active == True,
        ).first()
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        return user

    @staticmethod
    def create_token_pair(
        user: User, extra_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        access_token, expires_in = create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            extra_claims=extra_claims,
        )
        refresh_token, jti, refresh_exp = create_refresh_token(user_id=user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                **(extra_claims or {}),
            },
        }

    @staticmethod
    def send_patient_otp(phone_number: str) -> Dict[str, Any]:
        """
        Generates and sends an OTP to a patient's mobile number.
        For MVP demonstration, uses deterministic OTP '123456' with real-time response.
        """
        clean_phone = re.sub(r"[^\d]", "", phone_number)
        if len(clean_phone) < 10:
            raise InvalidCredentialsException("Please enter a valid 10-digit mobile number")

        return {
            "status": "SENT",
            "phone_number": clean_phone,
            "message": "OTP sent successfully to your mobile number. Use test OTP: 123456",
            "mock_otp": "123456",
        }

    @staticmethod
    def verify_patient_otp(
        db: Session, phone_number: str, otp: str, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifies patient OTP (123456), auto-creates or retrieves Patient & User record,
        and returns real JWT token pair.
        """
        clean_phone = re.sub(r"[^\d]", "", phone_number)
        if len(clean_phone) < 10:
            raise InvalidCredentialsException("Please enter a valid 10-digit mobile number")

        # Mock OTP verification
        if otp.strip() != "123456":
            raise InvalidCredentialsException("Invalid OTP code. Please use 123456 for testing.")

        # Find or create patient
        patient = db.query(Patient).filter(
            (Patient.phone_number == clean_phone) |
            (Patient.phone_number == f"+91{clean_phone}") |
            (Patient.phone_number.endswith(clean_phone[-10:]))
        ).first()

        if not patient:
            # Generate patient ID
            existing_count = db.query(Patient).count()
            patient_id = f"PAT-{1001 + existing_count}"
            patient_name = name.strip() if name and name.strip() else f"Patient {clean_phone[-4:]}"
            patient = Patient(
                id=uuid.uuid4(),
                patient_id=patient_id,
                name=patient_name,
                phone_number=clean_phone,
            )
            db.add(patient)
            db.flush()
        elif name and name.strip() and patient.name.startswith("Patient "):
            patient.name = name.strip()
            db.flush()

        # Find or create User record for authentication
        user_name = f"patient_{clean_phone[-10:]}"
        user_email = f"{user_name}@prescripto.patient"
        user = db.query(User).filter(
            (User.username == user_name) | (User.email == user_email)
        ).first()

        if not user:
            user = User(
                id=uuid.uuid4(),
                username=user_name,
                email=user_email,
                hashed_password=hash_password(uuid.uuid4().hex),
                role="OPERATOR",
                is_active=True,
            )
            db.add(user)
            db.flush()

        patient.user_id = user.id
        db.commit()

        extra_claims = {
            "patient_id": patient.patient_id,
            "patient_name": patient.name,
            "phone_number": patient.phone_number,
            "is_patient": True,
        }
        return AuthService.create_token_pair(user, extra_claims=extra_claims)

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
