"""
Doctor-Patient Links Router: Manage explicit authorization links between
doctors/reviewers and patients they are authorized to treat.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from prescripto.db.session import get_db
from prescripto.auth.dependencies import get_current_user, require_role
from prescripto.db.models.users import User
from prescripto.db.models.patient import Patient
from prescripto.db.models.doctor_patient import DoctorPatient
from prescripto.db.models.enums import Role
from prescripto.api.v1.schemas.doctor_patient import (
    DoctorPatientLinkRequest,
    DoctorPatientLinkResponse,
    DoctorPatientSummary,
    UnlinkPatientRequest,
)

router = APIRouter(prefix="/doctor/patients", tags=["Doctor-Patient Links"])


@router.post(
    "/link",
    response_model=DoctorPatientLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link a patient to the current doctor for authorized access",
    operation_id="linkPatientToDoctor",
)
def link_patient(
    payload: DoctorPatientLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.REVIEWER, Role.ADMIN)),
) -> DoctorPatientLinkResponse:
    """Create an explicit authorization link between doctor and patient."""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {payload.patient_id} not found",
        )

    # Check if link already exists
    existing = db.query(DoctorPatient).filter(
        DoctorPatient.doctor_id == current_user.id,
        DoctorPatient.patient_id == payload.patient_id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient {patient.patient_id} is already linked to this doctor",
        )

    link = DoctorPatient(
        doctor_id=current_user.id,
        patient_id=payload.patient_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return DoctorPatientLinkResponse(
        id=link.id,
        doctor_id=link.doctor_id,
        patient_id=link.patient_id,
        created_at=link.created_at.isoformat(),
    )


@router.get(
    "",
    response_model=List[DoctorPatientSummary],
    summary="List all patients linked to the current doctor",
    operation_id="listDoctorPatients",
)
def list_doctor_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.REVIEWER, Role.ADMIN)),
) -> List[DoctorPatientSummary]:
    """List all patients the current doctor is authorized to access."""
    links = db.query(DoctorPatient).filter(
        DoctorPatient.doctor_id == current_user.id
    ).all()

    if not links:
        return []

    patient_ids = [link.patient_id for link in links]
    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    patient_map = {p.id: p for p in patients}

    results = []
    for link in links:
        patient = patient_map.get(link.patient_id)
        if patient:
            results.append(
                DoctorPatientSummary(
                    id=link.id,
                    patient_id=link.patient_id,
                    patient_name=patient.name,
                    patient_patient_id=patient.patient_id,
                    phone_number=patient.phone_number,
                    created_at=link.created_at.isoformat(),
                )
            )

    return results


@router.delete(
    "/unlink",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove doctor-patient authorization link",
    operation_id="unlinkPatientFromDoctor",
)
def unlink_patient(
    payload: UnlinkPatientRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.REVIEWER, Role.ADMIN)),
):
    """Remove an authorization link, revoking the doctor's access to this patient."""
    link = db.query(DoctorPatient).filter(
        DoctorPatient.doctor_id == current_user.id,
        DoctorPatient.patient_id == payload.patient_id,
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor-patient link not found",
        )

    db.delete(link)
    db.commit()


@router.get(
    "/{patient_id}/verify",
    summary="Verify if current doctor has access to a specific patient",
    operation_id="verifyDoctorPatientAccess",
)
def verify_access(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.REVIEWER, Role.ADMIN)),
):
    """Check if the current doctor has an active link to the specified patient."""
    link = db.query(DoctorPatient).filter(
        DoctorPatient.doctor_id == current_user.id,
        DoctorPatient.patient_id == patient_id,
    ).first()

    return {
        "has_access": link is not None,
        "patient_id": str(patient_id),
        "linked_at": link.created_at.isoformat() if link else None,
    }