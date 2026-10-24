"""
Authentication Schemas matching OPENAPI.yaml.
"""
from typing import Literal
from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="RS256 Bearer JWT access token")
    refresh_token: str = Field(..., description="RS256 Bearer JWT refresh token")
    token_type: Literal["bearer"] = Field(default="bearer")
    expires_in: int = Field(..., description="Access token expiration in seconds", json_schema_extra={"example": 900})


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid RS256 refresh token")
