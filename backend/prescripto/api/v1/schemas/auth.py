from typing import Annotated, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, StringConstraints

# Standard RFC-compliant email string without third-party email-validator dependency
EmailStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        pattern=r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$",
    ),
]


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="RS256 Bearer JWT access token")
    refresh_token: str = Field(..., description="RS256 Bearer JWT refresh token")
    token_type: Literal["bearer"] = Field(default="bearer")
    expires_in: int = Field(..., description="Access token expiration in seconds", json_schema_extra={"example": 900})
    user: Optional[Dict[str, Any]] = Field(default=None, description="Authenticated user and patient profile metadata")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid RS256 refresh token")


class SendOtpRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address for OTP delivery", json_schema_extra={"example": "user@example.com"})
    purpose: str = Field(default="LOGIN", description="Purpose of OTP: LOGIN, REGISTER, PASSWORD_RESET", json_schema_extra={"example": "LOGIN"})


class SendOtpResponse(BaseModel):
    status: str
    email: str
    message: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    otp: str = Field(..., description="6-digit OTP code", min_length=6, max_length=6, json_schema_extra={"example": "123456"})
    purpose: str = Field(default="LOGIN", description="Purpose of OTP: LOGIN, REGISTER, PASSWORD_RESET", json_schema_extra={"example": "LOGIN"})


class PatientRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    otp: str = Field(..., description="OTP received via email", min_length=6, max_length=6)
    name: str = Field(..., description="Patient full name", min_length=1, max_length=255)
    password: str = Field(..., description="Password", min_length=8, max_length=128)


class PatientLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    otp: str = Field(..., description="OTP received via email", min_length=6, max_length=6)


class DoctorRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password", min_length=8, max_length=128)
    name: str = Field(..., description="Doctor full name", min_length=1, max_length=255)
    specialization: Optional[str] = Field(default=None, description="Medical specialization", max_length=100)
    license_number: Optional[str] = Field(default=None, description="Medical license number", max_length=50)
    clinic_name: Optional[str] = Field(default=None, description="Clinic name", max_length=255)
    clinic_address: Optional[str] = Field(default=None, description="Clinic address", max_length=500)
    phone_number: Optional[str] = Field(default=None, description="Contact phone number", max_length=50)
    bio: Optional[str] = Field(default=None, description="Professional biography", max_length=2000)


class DoctorLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Doctor email address", json_schema_extra={"example": "doctor.sharma@prescripto.local"})
    password: str = Field(..., description="Account password", json_schema_extra={"example": "DoctorPass123!"})


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address for password reset")


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., description="New password", min_length=8, max_length=128)


class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_verified: bool
    patient: Optional[Dict[str, Any]] = None
    doctor: Optional[Dict[str, Any]] = None