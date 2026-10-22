"""
Auth Router: Endpoints for Token creation, Patient OTP, Doctor Login, and Refresh.
"""
from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from prescripto.db.session import get_db
from prescripto.auth.service import AuthService
from prescripto.auth.dependencies import get_current_user
from prescripto.db.models.users import User
from prescripto.db.models.patient import Patient
from prescripto.api.v1.schemas.auth import (
    TokenResponse,
    RefreshTokenRequest,
    SendOtpRequest,
    SendOtpResponse,
    VerifyOtpRequest,
    DoctorLoginRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Obtain a JWT access/refresh token pair",
    operation_id="createToken",
)
def create_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """OAuth2 password login granting RS256 access and refresh token pair."""
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    tokens = AuthService.create_token_pair(user)
    return TokenResponse(**tokens)


@router.post(
    "/doctor/login",
    response_model=TokenResponse,
    summary="Doctor / Staff login via Email and Password",
    operation_id="doctorLogin",
)
def doctor_login(
    payload: DoctorLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Doctor / Staff login using email and password, returning RS256 JWT tokens."""
    user = AuthService.authenticate_user(db, payload.email, payload.password)
    tokens = AuthService.create_token_pair(user)
    return TokenResponse(**tokens)


@router.post(
    "/send-otp",
    response_model=SendOtpResponse,
    summary="Send OTP to patient mobile number",
    operation_id="sendPatientOtp",
)
def send_patient_otp(
    payload: SendOtpRequest,
) -> SendOtpResponse:
    """Generates and dispatches an OTP to patient mobile number (mock test OTP: 123456)."""
    result = AuthService.send_patient_otp(payload.phone_number)
    return SendOtpResponse(**result)


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    summary="Verify patient OTP and login / register",
    operation_id="verifyPatientOtp",
)
def verify_patient_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verifies patient OTP, registers or fetches patient record, and returns real JWT token pair."""
    tokens = AuthService.verify_patient_otp(
        db=db,
        phone_number=payload.phone_number,
        otp=payload.otp,
        name=payload.name,
    )
    return TokenResponse(**tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new access token",
    operation_id="refreshToken",
)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Exchanges a valid refresh token for a new token pair while revoking the old token in blocklist."""
    tokens = AuthService.refresh_session(db, request.refresh_token)
    return TokenResponse(**tokens)


@router.get(
    "/me",
    summary="Get current user and patient profile",
    operation_id="getCurrentUserProfile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns profile for currently authenticated user."""
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "patient": {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "phone_number": patient.phone_number,
            "age": patient.age,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "medical_history": patient.medical_history,
            "allergies": patient.allergies,
        } if patient else None,
    }
