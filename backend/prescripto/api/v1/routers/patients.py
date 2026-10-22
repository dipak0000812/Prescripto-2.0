"""
Patients Router: Patient Search, Profile Management, and Complete Medical History Timeline.
Enables doctors to search by Patient ID, Name, or Phone, and inspect previous prescriptions,
medications, safety alerts, and clinical reviews.
"""
import uuid
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from prescripto.db.session import get_db
from prescripto.auth.dependencies import get_current_user
from prescripto.db.models.users import User
from prescripto.db.models.patient import Patient
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.medication import PrescriptionMedication, MedicationCandidate
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.review import Review
from prescripto.db.base import utc_now

router = APIRouter(prefix="/patients", tags=["Patients"])


# Schemas
class PatientSummary(BaseModel):
    id: str
    patient_id: str
    name: str
    phone_number: str
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    prescriptions_count: int = 0
    latest_visit: Optional[str] = None
    created_at: str


class TimelineEvent(BaseModel):
    document_id: str
    analysis_id: Optional[str] = None
    file_name: Optional[str] = None
    uploaded_at: str
    analysis_status: Optional[str] = None
    review_required: bool = False
    review_reasons: List[str] = []
    medications: List[Dict[str, Any]] = []
    safety_findings: List[Dict[str, Any]] = []
    clinical_reviews: List[Dict[str, Any]] = []


class PatientDetailResponse(BaseModel):
    id: str
    patient_id: str
    name: str
    phone_number: str
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_at: str
    total_prescriptions: int
    active_medications: List[Dict[str, Any]] = []
    timeline: List[TimelineEvent] = []


class CreatePatientRequest(BaseModel):
    name: str
    phone_number: str
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = None


@router.get(
    "/search",
    response_model=List[PatientSummary],
    summary="Search patients by name, patient ID, or phone number",
    operation_id="searchPatients",
)
def search_patients(
    q: str = Query(default="", description="Search query (name, PAT-ID, or phone)"),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PatientSummary]:
    """Search patients across name, patient ID, and mobile phone number."""
    query = db.query(Patient)
    clean_q = q.strip()
    if clean_q:
        query = query.filter(
            or_(
                Patient.name.ilike(f"%{clean_q}%"),
                Patient.patient_id.ilike(f"%{clean_q}%"),
                Patient.phone_number.ilike(f"%{clean_q}%"),
            )
        )

    patients = query.order_by(Patient.name).limit(limit).all()

    results: List[PatientSummary] = []
    for p in patients:
        # Count associated prescriptions
        docs_count = db.query(PrescriptionDocument).filter(
            or_(
                PrescriptionDocument.patient_ref == p.patient_id,
                PrescriptionDocument.patient_ref == p.name,
                PrescriptionDocument.patient_ref == str(p.id),
                PrescriptionDocument.patient_ref == p.phone_number,
            )
        ).count()

        latest_doc = db.query(PrescriptionDocument).filter(
            or_(
                PrescriptionDocument.patient_ref == p.patient_id,
                PrescriptionDocument.patient_ref == p.name,
                PrescriptionDocument.patient_ref == str(p.id),
                PrescriptionDocument.patient_ref == p.phone_number,
            )
        ).order_by(desc(PrescriptionDocument.uploaded_at)).first()

        results.append(
            PatientSummary(
                id=str(p.id),
                patient_id=p.patient_id,
                name=p.name,
                phone_number=p.phone_number,
                age=p.age,
                gender=p.gender,
                blood_group=p.blood_group,
                prescriptions_count=docs_count,
                latest_visit=latest_doc.uploaded_at.isoformat() if latest_doc else None,
                created_at=p.created_at.isoformat(),
            )
        )

    return results


@router.get(
    "/{patient_identifier}",
    response_model=PatientDetailResponse,
    summary="Get patient profile and full historical timeline of reports",
    operation_id="getPatientTimeline",
)
def get_patient_timeline(
    patient_identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientDetailResponse:
    """
    Retrieves full medical record and prescription history timeline for a patient.
    Can be looked up by UUID, patient ID (PAT-1001), or phone number.
    """
    # Look up patient
    patient = None
    try:
        pid_uuid = uuid.UUID(patient_identifier)
        patient = db.query(Patient).filter(Patient.id == pid_uuid).first()
    except ValueError:
        pass

    if not patient:
        patient = db.query(Patient).filter(
            or_(
                Patient.patient_id == patient_identifier,
                Patient.phone_number == patient_identifier,
                Patient.phone_number == patient_identifier.replace("+91", "").strip(),
            )
        ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_identifier}' not found",
        )

    # Find all prescription documents matching this patient
    docs = db.query(PrescriptionDocument).filter(
        or_(
            PrescriptionDocument.patient_ref == patient.patient_id,
            PrescriptionDocument.patient_ref == patient.name,
            PrescriptionDocument.patient_ref == str(patient.id),
            PrescriptionDocument.patient_ref == patient.phone_number,
        )
    ).order_by(desc(PrescriptionDocument.uploaded_at)).all()

    timeline_events: List[TimelineEvent] = []
    active_medications: List[Dict[str, Any]] = []
    seen_active_names = set()

    for doc in docs:
        analysis = db.query(Analysis).filter(
            Analysis.document_id == doc.id
        ).order_by(desc(Analysis.created_at)).first()

        med_list: List[Dict[str, Any]] = []
        safety_list: List[Dict[str, Any]] = []
        review_list: List[Dict[str, Any]] = []

        if analysis:
            # Extracted meds
            meds = db.query(PrescriptionMedication).filter(
                PrescriptionMedication.analysis_id == analysis.id
            ).order_by(PrescriptionMedication.line_index).all()

            for m in meds:
                # Find candidate resolution
                cand = db.query(MedicationCandidate).filter(
                    MedicationCandidate.prescription_med_id == m.id
                ).first()

                med_name = cand.resolved_medication.brand_name if (cand and cand.resolved_medication) else m.name_raw
                med_info = {
                    "line_index": m.line_index,
                    "name": med_name or m.name_raw or "Unspecified",
                    "strength": m.strength_raw,
                    "dose": m.dose_raw,
                    "frequency": m.frequency_raw,
                    "duration": m.duration_raw,
                    "instructions": m.instructions_raw,
                    "state": m.name_state,
                    "resolution_status": cand.resolution_status if cand else "UNRESOLVED",
                    "match_score": cand.candidate_score if cand else None,
                }
                med_list.append(med_info)

                # Collect in active medications summary
                norm_key = (med_info["name"] or "").strip().lower()
                if norm_key and norm_key not in seen_active_names and m.name_state != "UNREADABLE":
                    seen_active_names.add(norm_key)
                    active_medications.append({
                        **med_info,
                        "prescribed_date": doc.uploaded_at.strftime("%d %b %Y"),
                        "analysis_id": str(analysis.id),
                    })

            # Safety findings
            risks = db.query(RiskFinding).filter(
                RiskFinding.analysis_id == analysis.id
            ).all()
            for r in risks:
                safety_list.append({
                    "check_type": r.check_type,
                    "status": r.finding_status,
                    "severity": getattr(r, "severity", "MODERATE"),
                    "detail": r.evidence_text or getattr(r, "clinical_rationale", None) or f"{r.check_type}: {r.finding_status}",
                    "recommendation": getattr(r, "actionable_guidance", "Consult your physician regarding medication interactions."),
                })

            # Reviews
            revs = db.query(Review).filter(
                Review.analysis_id == analysis.id
            ).all()
            for rv in revs:
                review_list.append({
                    "action": rv.action,
                    "reviewer_id": str(rv.reviewer_id),
                    "notes": rv.notes,
                    "reviewed_at": rv.reviewed_at.isoformat(),
                })

        timeline_events.append(
            TimelineEvent(
                document_id=str(doc.id),
                analysis_id=str(analysis.id) if analysis else None,
                file_name=doc.storage_key.split("/")[-1] if doc.storage_key else "Prescription",
                uploaded_at=doc.uploaded_at.isoformat(),
                analysis_status=analysis.status if analysis else "PENDING",
                review_required=analysis.review_required if analysis else False,
                review_reasons=analysis.review_reasons if analysis else [],
                medications=med_list,
                safety_findings=safety_list,
                clinical_reviews=review_list,
            )
        )

    return PatientDetailResponse(
        id=str(patient.id),
        patient_id=patient.patient_id,
        name=patient.name,
        phone_number=patient.phone_number,
        age=patient.age,
        gender=patient.gender,
        blood_group=patient.blood_group,
        address=patient.address,
        medical_history=patient.medical_history,
        allergies=patient.allergies,
        emergency_contact=patient.emergency_contact,
        created_at=patient.created_at.isoformat(),
        total_prescriptions=len(docs),
        active_medications=active_medications,
        timeline=timeline_events,
    )


@router.post(
    "",
    response_model=PatientSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient record",
    operation_id="createPatient",
)
def create_patient(
    payload: CreatePatientRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientSummary:
    """Creates a new patient profile in the clinic database."""
    # Check for existing phone number
    existing = db.query(Patient).filter(Patient.phone_number == payload.phone_number.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient with mobile {payload.phone_number} already exists as {existing.patient_id}",
        )

    total_patients = db.query(Patient).count()
    patient_id = f"PAT-{1001 + total_patients}"

    patient = Patient(
        id=uuid.uuid4(),
        patient_id=patient_id,
        name=payload.name.strip(),
        phone_number=payload.phone_number.strip(),
        age=payload.age,
        gender=payload.gender,
        blood_group=payload.blood_group,
        address=payload.address,
        medical_history=payload.medical_history,
        allergies=payload.allergies,
        emergency_contact=payload.emergency_contact,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return PatientSummary(
        id=str(patient.id),
        patient_id=patient.patient_id,
        name=patient.name,
        phone_number=patient.phone_number,
        age=patient.age,
        gender=patient.gender,
        blood_group=patient.blood_group,
        prescriptions_count=0,
        latest_visit=None,
        created_at=patient.created_at.isoformat(),
    )
