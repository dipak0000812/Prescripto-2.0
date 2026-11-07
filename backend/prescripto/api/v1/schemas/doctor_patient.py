from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class DoctorPatientLinkRequest(BaseModel):
    patient_id: UUID = Field(..., description="Patient UUID to link to this doctor")


class DoctorPatientLinkResponse(BaseModel):
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    created_at: str


class DoctorPatientSummary(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    patient_patient_id: str
    phone_number: str
    created_at: str


class UnlinkPatientRequest(BaseModel):
    patient_id: UUID = Field(..., description="Patient UUID to unlink from this doctor")