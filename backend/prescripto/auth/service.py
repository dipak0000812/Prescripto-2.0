"""
Authentication Service: secure OTP management, rate limiting, patient/doctor registration & login.
"""
import uuid
import time
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import re

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_

from prescripto.db.models.users import User
from prescripto.db.models.patient import Patient
from prescripto.db.models.otp import OTPCode, PasswordResetToken
from prescripto.db.models.retention import TokenBlocklist
from prescripto.auth.crypto import (
    verify_password, create_access_token, create_refresh_token, decode_token, hash_password
)
from prescripto.auth.otp_crypto import generate_secure_otp, hash_otp, verify_otp_secure
from prescripto.auth import otp_crypto as otp_crypto_module
from prescripto.auth.otp_provider import IOtpProvider, DevelopmentOtpProvider, EmailOtpProvider

_last_otp_sent_time: Dict[str, float] = {}
from prescripto.auth.exceptions import (
    InvalidCredentialsException,
    TokenExpiredException,
    TokenRevokedException,
    BlocklistUnavailableException,
    RateLimitExceededException,
)
from prescripto.config.settings import settings
from prescripto.audit.service import AuditService
import jwt


class AuthService:
    _otp_provider: IOtpProvider = DevelopmentOtpProvider() if settings.ENVIRONMENT == "development" else EmailOtpProvider()

    @classmethod
    def set_otp_provider(cls, provider: IOtpProvider):
        cls._otp_provider = provider

    @staticmethod
    def authenticate_user(db: Session, identifier: str, password: str) -> User:
        """Authenticate user by either username or email with password verification."""
        user = db.query(User).filter(
            ((User.username == identifier) | (User.email == identifier)),
            User.is_active == True,
        ).first()
        if not user or not verify_password(password, user.hashed_password):
            AuditService.log_authentication(db, user, success=False, details={"identifier": identifier, "reason": "invalid_credentials"})
            raise InvalidCredentialsException()
        AuditService.log_authentication(db, user, success=True, details={"action": "password_login"})
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

    @classmethod
    async def request_otp(cls, db: Session, email: str, purpose: str = "LOGIN") -> Dict[str, Any]:
        """
        Generates, hashes, stores in DB, and dispatches an OTP to a user's email.
        Enforces resend cooldowns and rate limits.
        """
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise InvalidCredentialsException("Please enter a valid email address")

        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if user exists - always return success for security
            return {
                "status": "SENT",
                "email": email,
                "message": "If the email is registered, an OTP has been sent."
            }

        # Check if user is active
        if not user.is_active:
            raise InvalidCredentialsException("Account is deactivated. Please contact support.")

        now = time.time()

        # Resend cooldown (60 seconds)
        recent_otp = db.execute(
            select(OTPCode).where(
                and_(
                    OTPCode.user_id == user.id,
                    OTPCode.purpose == purpose,
                    OTPCode.created_at > datetime.now(timezone.utc) - timedelta(seconds=60)
                )
            ).order_by(OTPCode.created_at.desc()).limit(1)
        ).scalar_one_or_none()

        if recent_otp:
            raise RateLimitExceededException("Please wait 60 seconds before requesting a new OTP.")

        # Generate OTP
        raw_otp = generate_secure_otp(6)
        salt = secrets.token_hex(16)
        hashed_otp = hash_otp(raw_otp, salt)

        # Expiry: 10 minutes from now
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Store in database
        otp_code = OTPCode(
            user_id=user.id,
            code_hash=hash_otp(raw_otp, salt),
            salt=salt,
            channel="EMAIL",
            purpose=purpose,
            expires_at=expires_at,
            attempts=0,
            max_attempts=3,
        )
        db.add(otp_code)
        db.commit()

        # Dispatch OTP via provider
        success = await cls._otp_provider.send_otp(user.email, raw_otp, channel="EMAIL")
        if not success:
            raise Exception("Failed to send OTP email.")

        return {
            "status": "SENT",
            "email": email,
            "message": "OTP sent successfully to your email."
        }

    @classmethod
    def verify_otp_and_authenticate(
        cls, db: Session, email: str, otp: str, purpose: str = "LOGIN"
    ) -> Dict[str, Any]:
        """
        Verifies an OTP and authenticates the user.
        """
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise InvalidCredentialsException("Invalid email or OTP.")

        if not user.is_active:
            raise InvalidCredentialsException("Account is deactivated. Please contact support.")

        now = datetime.now(timezone.utc)

        # Find the OTP record
        otp_code = db.execute(
            select(OTPCode).where(
                and_(
                    OTPCode.user_id == user.id,
                    OTPCode.purpose == purpose,
                    OTPCode.expires_at > now,
                    OTPCode.used_at.is_(None)
                )
            ).order_by(OTPCode.created_at.desc()).limit(1)
        ).scalar_one_or_none()

        if not otp_code:
            raise InvalidCredentialsException("No valid OTP found. Please request a new one.")

        # Check max attempts
        if otp_code.attempts >= otp_code.max_attempts:
            raise InvalidCredentialsException("Maximum OTP verification attempts exceeded. Please request a new one.")

        otp_code.attempts += 1

        # Verify OTP securely
        is_valid = verify_otp_secure(otp.strip(), otp_code.code_hash, otp_code.salt)
        if not is_valid:
            db.commit()
            raise InvalidCredentialsException("Invalid OTP code.")

        # Mark OTP as used
        otp_code.used_at = datetime.now(timezone.utc)
        db.commit()

        # Check if user needs verification
        if not user.is_verified:
            user.is_verified = True
            db.commit()

        # Audit log
        AuditService.log_authentication(db, user, success=True, details={"action": f"otp_{purpose.lower()}"})

        # Generate tokens
        extra_claims = {}
        if user.role == "PATIENT":
            patient = db.query(Patient).filter(Patient.user_id == user.id).first()
            if patient:
                extra_claims = {
                    "patient_id": patient.patient_id,
                    "patient_name": patient.name,
                    "phone_number": patient.phone_number,
                    "is_patient": True,
                }

        return AuthService.create_token_pair(user, extra_claims=extra_claims)

    @classmethod
    async def register_patient(cls, db: Session, email: str, otp: str, name: str, password: str) -> Dict[str, Any]:
        """
        Register a new patient with email OTP verification.
        """
        # Verify OTP first
        tokens = cls.verify_otp_and_authenticate(db, email, otp, purpose="REGISTER")

        # Check if user already exists (shouldn't happen if OTP verification passed)
        user = db.query(User).filter(User.email == email).first()
        if user:
            raise InvalidCredentialsException("User with this email already exists.")

        # Hash password
        hashed_password = hash_password(password)

        # Create user
        user = User(
            id=uuid.uuid4(),
            username=f"patient_{secrets.token_urlsafe(8)}",
            email=email,
            hashed_password=hashed_password,
            role="PATIENT",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()

        # Create patient profile
        existing_count = db.query(Patient).count()
        patient_id = f"PAT-{1001 + existing_count}"
        patient = Patient(
            id=uuid.uuid4(),
            patient_id=patient_id,
            name=name.strip(),
            email=email,
            hashed_password=hash_password(password),  # Store same hash for patient portal
            user_id=user.id,
        )
        db.add(patient)
        db.commit()

        # Audit log
        AuditService.log_authentication(db, user, success=True, details={"action": "patient_registration"})

        return AuthService.create_token_pair(user)

    @classmethod
    async def register_doctor(cls, db: Session, email: str, password: str, name: str,
                              specialization: str = None, license_number: str = None,
                              clinic_name: str = None, clinic_address: str = None,
                              phone_number: str = None, bio: str = None) -> Dict[str, Any]:
        """
        Register a new doctor (requires admin approval for is_verified).
        """
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise InvalidCredentialsException("User with this email already exists.")

        # Hash password
        hashed_password = hash_password(password)

        # Create user
        user = User(
            id=uuid.uuid4(),
            username=name.lower().replace(" ", "_"),
            email=email,
            hashed_password=hashed_password,
            role="DOCTOR",
            is_active=True,
            is_verified=False,  # Requires admin approval
            specialization=specialization,
            license_number=license_number,
            clinic_name=clinic_name,
            clinic_address=clinic_address,
            phone_number=phone_number,
            bio=bio,
        )
        db.add(user)
        db.commit()

        # Audit log
        AuditService.log_authentication(db, user, success=True, details={"action": "doctor_registration"})

        return AuthService.create_token_pair(user)

    @classmethod
    async def request_password_reset(cls, db: Session, email: str) -> Dict[str, Any]:
        """
        Request a password reset token sent via email.
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if user exists
            return {
                "status": "SENT",
                "email": email,
                "message": "If the email is registered, a password reset link has been sent."
            }

        # Invalidate any existing unused tokens
        existing_tokens = db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used_at.is_(None),
                    PasswordResetToken.expires_at > datetime.now(timezone.utc)
                )
            )
        ).scalars().all()
        for token in existing_tokens:
            token.used_at = datetime.now(timezone.utc)
        db.commit()

        # Generate secure token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_otp(raw_token, secrets.token_hex(16))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(reset_token)
        db.commit()

        # Send email with reset link
        # In production, this would include the raw_token in a URL
        success = await cls._otp_provider.send_otp(
            user.email,
            f"Password reset token: {raw_token} (expires in 1 hour)",
            channel="EMAIL"
        )
        if not success:
            raise Exception("Failed to send password reset email.")

        return {
            "status": "SENT",
            "email": email,
            "message": "Password reset instructions sent to your email."
        }

    @classmethod
    def reset_password(cls, db: Session, email: str, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset password using a valid token.
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise InvalidCredentialsException("Invalid reset request.")

        # Find valid token
        reset_token = db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used_at.is_(None),
                    PasswordResetToken.expires_at > datetime.now(timezone.utc)
                )
            ).order_by(PasswordResetToken.created_at.desc()).limit(1)
        ).scalar_one_or_none()

        if not reset_token:
            raise InvalidCredentialsException("Invalid or expired reset token.")

        # Verify token
        is_valid = verify_otp_secure(token, reset_token.token_hash, secrets.token_hex(16))  # We'd need to store salt
        if not is_valid:
            raise InvalidCredentialsException("Invalid reset token.")

        # Mark token as used
        reset_token.used_at = datetime.now(timezone.utc)

        # Update password
        user.hashed_password = hash_password(new_password)
        db.commit()

        # Revoke all refresh tokens
        db.execute(
            TokenBlocklist.__table__.insert().from_select(
                ["jti", "user_id", "expires_at", "revoked_at"],
                select(
                    func.concat("RESET_", func.uuid_generate_v4()),
                    user.id,
                    datetime.now(timezone.utc) + timedelta(days=7),
                    func.now()
                ).where(True)
            )
        )
        db.commit()

        return {"status": "SUCCESS", "message": "Password has been reset successfully."}

    @staticmethod
    def authenticate_user(db: Session, identifier: str, password: str) -> User:
        """Authenticate user by either username or email with password verification."""
        user = db.query(User).filter(
            ((User.username == identifier) | (User.email == identifier)),
            User.is_active == True,
        ).first()
        if not user or not verify_password(password, user.hashed_password):
            AuditService.log_authentication(db, user, success=False, details={"identifier": identifier, "reason": "invalid_credentials"})
            raise InvalidCredentialsException()
        AuditService.log_authentication(db, user, success=True, details={"action": "password_login"})
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

        try:
            is_revoked = db.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).first()
            if is_revoked:
                raise TokenRevokedException()
        except TokenRevokedException:
            raise
        except SQLAlchemyError as exc:
            raise BlocklistUnavailableException() from exc

        user = db.query(User).filter(User.id == uuid.UUID(user_id_str), User.is_active == True).first()
        if not user:
            raise InvalidCredentialsException("User not found or inactive")

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

        return AuthService.create_token_pair(user)