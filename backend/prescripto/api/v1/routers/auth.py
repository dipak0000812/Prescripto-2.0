"""
Auth Router: Endpoints for Token creation, Patient/Doctor Registration, Login, OTP, Password Reset, and Refresh.
"""
from fastapi import APIRouter, Depends, Form, HTTPException, status
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
    PatientRegisterRequest,
    PatientLoginRequest,
    DoctorRegisterRequest,
    DoctorLoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserProfileResponse,
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
    "/doctor/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new doctor account",
    operation_id="registerDoctor",
)
async def register_doctor(
    payload: DoctorRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register a new doctor account (requires admin approval for verification)."""
    tokens = await AuthService.register_doctor(
        db=db,
        email=payload.email,
        password=payload.password,
        name=payload.name,
        specialization=payload.specialization,
        license_number=payload.license_number,
        clinic_name=payload.clinic_name,
        clinic_address=payload.clinic_address,
        phone_number=payload.phone_number,
        bio=payload.bio,
    )
    return TokenResponse(**tokens)


@router.post(
    "/patient/request-otp",
    response_model=SendOtpResponse,
    summary="Request OTP to patient email",
    operation_id="requestPatientOtp",
)
async def request_patient_otp(
    payload: SendOtpRequest,
    db: Session = Depends(get_db),
) -> SendOtpResponse:
    """Generates and dispatches an OTP to patient email for login."""
    result = await AuthService.request_otp(db, payload.email, purpose=payload.purpose)
    return SendOtpResponse(**result)


@router.post(
    "/patient/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient account and authenticate",
    operation_id="registerPatient",
)
async def register_patient(
    payload: PatientRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verifies patient OTP, registers a new patient profile, and returns real JWT token pair."""
    tokens = await AuthService.register_patient(
        db=db,
        email=payload.email,
        otp=payload.otp,
        name=payload.name,
        password=payload.password,
    )
    return TokenResponse(**tokens)


@router.post(
    "/patient/login",
    response_model=TokenResponse,
    summary="Login an existing patient account via OTP",
    operation_id="loginPatient",
)
async def login_patient(
    payload: PatientLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verifies patient OTP and authenticates an existing patient, returning real JWT token pair."""
    tokens = await AuthService.verify_otp_and_authenticate(
        db=db,
        email=payload.email,
        otp=payload.otp,
        purpose="LOGIN",
    )
    return TokenResponse(**tokens)


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    summary="Verify OTP for any purpose",
    operation_id="verifyOtp",
)
async def verify_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verifies OTP and returns tokens if successful."""
    tokens = await AuthService.verify_otp_and_authenticate(
        db=db,
        email=payload.email,
        otp=payload.otp,
        purpose=payload.purpose,
    )
    return TokenResponse(**tokens)


@router.post(
    "/forgot-password",
    response_model=SendOtpResponse,
    summary="Request password reset link via email",
    operation_id="forgotPassword",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> SendOtpResponse:
    """Request a password reset link to be sent via email."""
    result = await AuthService.request_password_reset(db, payload.email)
    return SendOtpResponse(**result)


@router.post(
    "/reset-password",
    response_model=dict,
    summary="Reset password using reset token",
    operation_id="resetPassword",
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Reset password using a valid reset token."""
    result = AuthService.reset_password(db, payload.email, payload.token, payload.new_password)
    return result


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
    response_model=UserProfileResponse,
    summary="Get current user and patient/doctor profile",
    operation_id="getCurrentUserProfile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns profile for currently authenticated user."""
    from prescripto.db.models.patient import Patient
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

    doctor_info = None
    if current_user.role == "DOCTOR":
        doctor_info = {
            "specialization": current_user.specialization,
            "license_number": current_user.license_number,
            "clinic_name": current_user.clinic_name,
            "clinic_address": current_user.clinic_address,
            "phone_number": current_user.phone_number,
            "bio": current_user.bio,
        }

    patient_info = None
    if patient:
        patient_info = {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "email": patient.email,
            "phone_number": patient.phone_number,
            "age": patient.age,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "medical_history": patient.medical_history,
            "allergies": patient.allergies,
        }

    return UserProfileResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_verified=current_user.is_verified,
        patient=patient_info,
        doctor=doctor_info,
    )