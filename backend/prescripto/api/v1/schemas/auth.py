from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="RS256 Bearer JWT access token")
    refresh_token: str = Field(..., description="RS256 Bearer JWT refresh token")
    token_type: Literal["bearer"] = Field(default="bearer")
    expires_in: int = Field(..., description="Access token expiration in seconds", json_schema_extra={"example": 900})
    user: Optional[Dict[str, Any]] = Field(default=None, description="Authenticated user and patient profile metadata")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid RS256 refresh token")


class SendOtpRequest(BaseModel):
    phone_number: str = Field(..., description="10-digit mobile number for patient login", json_schema_extra={"example": "9876543210"})


class SendOtpResponse(BaseModel):
    status: str
    phone_number: str
    message: str
    mock_otp: str = Field(default="123456", description="Pre-filled test OTP for quick MVP verification")


class VerifyOtpRequest(BaseModel):
    phone_number: str = Field(..., description="10-digit mobile number")
    otp: str = Field(..., description="OTP received (use 123456 for test)")
    name: Optional[str] = Field(default=None, description="Patient full name (for new registrations)")


class DoctorLoginRequest(BaseModel):
    email: str = Field(..., description="Doctor or staff email address or username", json_schema_extra={"example": "doctor.sharma@prescripto.local"})
    password: str = Field(..., description="Account password", json_schema_extra={"example": "DoctorPass123!"})
