"""
Canonical Error Schemas matching docs/ERROR-CONTRACT.md and OPENAPI.yaml.
"""
import uuid
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code", json_schema_extra={"example": "ANALYSIS_NOT_READY"})
    message: str = Field(..., description="Human readable explanation")
    request_id: uuid.UUID = Field(..., description="Request correlation identifier")


class ErrorResponse(BaseModel):
    error: ErrorDetail
