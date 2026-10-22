"""
Prescripto AI 2.0 — Analyses and Review Router.
Implements:
- GET /analyses/{id} (Current status & stage breakdown)
- GET /analyses/{id}/result (Full structured report with result gating)
- POST /analyses/{id}/review (Reviewer submission & status transition)
"""
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from prescripto.db.session import get_db
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.auth.dependencies import get_current_user, require_role
from prescripto.api.v1.schemas.analysis import (
    AnalysisStatus,
    AnalysisResult,
    ReviewSubmission,
    ReviewRecord,
    MedicationUpdateRequest,
)
from prescripto.application.use_cases.get_analysis import (
    GetAnalysisStatusUseCase,
    GetAnalysisResultUseCase,
)
from prescripto.application.use_cases.submit_review import SubmitReviewUseCase

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.get(
    "/{id}",
    response_model=AnalysisStatus,
    status_code=status.HTTP_200_OK,
    summary="Get analysis status and stage breakdown",
    operation_id="getAnalysisStatus",
)
def get_analysis_status(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisStatus:
    """Returns current analysis status and stage progress breakdown."""
    use_case = GetAnalysisStatusUseCase(db=db)
    return use_case.execute(analysis_id=id, caller=current_user)


@router.get(
    "/{id}/status",
    response_model=AnalysisStatus,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_analysis_status_alias(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisStatus:
    return get_analysis_status(id=id, current_user=current_user, db=db)


@router.get(
    "/{id}/result",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Get full analysis result — only when COMPLETED or REQUIRES_REVIEW",
    operation_id="getAnalysisResult",
)
def get_analysis_result(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    """
    Returns full analysis result payload.
    Enforces result gating: returns 404 ANALYSIS_NOT_READY for QUEUED, PROCESSING, FAILED.
    """
    use_case = GetAnalysisResultUseCase(db=db)
    return use_case.execute(analysis_id=id, caller=current_user)


@router.post(
    "/{id}/review",
    response_model=ReviewRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Submit reviewer decisions for an analysis",
    operation_id="submitReview",
)
def submit_review(
    id: uuid.UUID,
    submission: ReviewSubmission,
    current_user: User = Depends(require_role(Role.REVIEWER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> ReviewRecord:
    """
    Submits authorized clinical review decisions and transitions analysis status.
    Requires REVIEWER or ADMIN role. Returns 409 if analysis is not in a reviewable state.
    """
    use_case = SubmitReviewUseCase(db=db)
    return use_case.execute(analysis_id=id, submission=submission, reviewer=current_user)


@router.post(
    "/{id}/reviews",
    response_model=ReviewRecord,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def submit_reviews_alias(
    id: uuid.UUID,
    submission: ReviewSubmission,
    current_user: User = Depends(require_role(Role.REVIEWER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> ReviewRecord:
    return submit_review(id=id, submission=submission, current_user=current_user, db=db)


@router.get(
    "/{id}/clinical-summary",
    status_code=status.HTTP_200_OK,
    summary="Get patient-friendly and clinician-facing clinical explanation (LLM powered)",
    operation_id="getAnalysisClinicalSummary",
)
def get_analysis_clinical_summary(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns AI-generated or deterministic clinical summary,
    safety warnings in plain language, and patient dosing guidance.
    """
    from fastapi import HTTPException
    from prescripto.db.models.analysis import Analysis
    from prescripto.db.models.document import PrescriptionDocument
    from prescripto.db.models.medication import PrescriptionMedication
    from prescripto.db.models.safety import RiskFinding
    from prescripto.db.models.patient import Patient
    from prescripto.application.services.llm_explainer import llm_explainer

    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    doc = db.query(PrescriptionDocument).filter(
        PrescriptionDocument.id == analysis.document_id
    ).first()
    if current_user.role == Role.OPERATOR.value and doc and doc.uploader_id != current_user.id:
        raise HTTPException(status_code=404, detail="Analysis not found")

    meds = db.query(PrescriptionMedication).filter(
        PrescriptionMedication.analysis_id == id
    ).order_by(PrescriptionMedication.line_index).all()

    findings = db.query(RiskFinding).filter(
        RiskFinding.analysis_id == id
    ).all()

    patient_info = None
    if doc and doc.patient_ref:
        patient = db.query(Patient).filter(
            (Patient.patient_id == doc.patient_ref) | 
            (Patient.phone_number == doc.patient_ref)
        ).first()
        if patient:
            patient_info = {
                "patient_id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "allergies": patient.allergies,
                "medical_history": patient.medical_history,
            }

    med_dicts = [
        {
            "name_raw": m.name_raw,
            "strength_raw": m.strength_raw,
            "dose_raw": m.dose_raw,
            "frequency_raw": m.frequency_raw,
            "route_raw": m.route_raw,
            "duration_raw": m.duration_raw,
            "instructions_raw": m.instructions_raw,
        }
        for m in meds
    ]
    finding_dicts = [
        {
            "check_type": f.check_type,
            "finding_status": f.finding_status,
            "evidence_text": f.evidence_text,
            "source_name": f.source_name,
        }
        for f in findings
    ]

    return llm_explainer.explain(
        medications=med_dicts,
        findings=finding_dicts,
        patient_info=patient_info,
    )


@router.patch(
    "/{id}/medications",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Update or correct medication lines for an analysis (Doctor editing)",
    operation_id="updateAnalysisMedications",
)
def update_analysis_medications(
    id: uuid.UUID,
    update_req: MedicationUpdateRequest,
    current_user: User = Depends(require_role(Role.REVIEWER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    """
    Allows authorized clinicians to edit recognized medication fields (correct OCR misreads),
    re-runs canonical normalization and safety screening, and recalculates review triggers.
    """
    from fastapi import HTTPException
    from prescripto.db.models.analysis import Analysis
    from prescripto.db.models.document import PrescriptionDocument
    from prescripto.db.models.medication import PrescriptionMedication
    from prescripto.db.models.safety import RiskFinding
    from prescripto.pipeline.engine import (
        handle_medication_normalization,
        handle_safety_screening,
        handle_report_assembly,
    )

    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status not in ["REQUIRES_REVIEW", "REVIEWING", "COMPLETED", "REVIEWED_COMPLETE", "REVIEWED_ESCALATED"]:
        raise HTTPException(status_code=409, detail=f"Cannot edit medications when analysis is in status '{analysis.status}'")

    doc = db.query(PrescriptionDocument).filter(
        PrescriptionDocument.id == analysis.document_id
    ).first()

    for item in update_req.medications:
        med = db.query(PrescriptionMedication).filter(
            PrescriptionMedication.analysis_id == id,
            PrescriptionMedication.line_index == item.line_index,
        ).first()
        if med:
            if item.name is not None:
                med.name_raw = item.name
                med.name_state = "CLEAR"
                med.name_confidence = 1.0
            if item.strength is not None:
                med.strength_raw = item.strength
                med.strength_state = "CLEAR"
                med.strength_confidence = 1.0
            if item.dose is not None:
                med.dose_raw = item.dose
                med.dose_state = "CLEAR"
                med.dose_confidence = 1.0
            if item.frequency is not None:
                med.frequency_raw = item.frequency
                med.frequency_state = "CLEAR"
                med.frequency_confidence = 1.0
            if item.route is not None:
                med.route_raw = item.route
                med.route_state = "CLEAR"
                med.route_confidence = 1.0
            if item.duration is not None:
                med.duration_raw = item.duration
                med.duration_state = "CLEAR"
                med.duration_confidence = 1.0
            if item.instructions is not None:
                med.instructions_raw = item.instructions
                med.instructions_state = "CLEAR"
                med.instructions_confidence = 1.0

    db.flush()

    # Re-run pipeline normalization & safety screening
    context: Dict[str, Any] = {}
    handle_medication_normalization(db, analysis, doc, context)

    # Remove prior auto-generated findings so they recalculate cleanly
    db.query(RiskFinding).filter(RiskFinding.analysis_id == id).delete()
    db.flush()

    handle_safety_screening(db, analysis, doc, context)
    handle_report_assembly(db, analysis, doc, context)
    db.commit()

    use_case = GetAnalysisResultUseCase(db=db)
    return use_case.execute(analysis_id=id, caller=current_user)
