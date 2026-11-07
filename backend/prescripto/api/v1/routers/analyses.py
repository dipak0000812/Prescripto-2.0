"""
Prescripto AI 2.0 — Analyses and Review Router.
Implements:
- GET /analyses/{id} (Current status & stage breakdown)
- GET /analyses/{id}/result (Full structured report with result gating)
- POST /analyses/{id}/review (Reviewer submission & status transition)
"""
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from prescripto.db.session import get_db
from prescripto.db.models.users import User
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.document import PrescriptionDocument
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
from prescripto.application.services.authorization import AuthorizationService

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
    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    AuthorizationService.enforce_analysis_access(db, current_user, analysis)

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
    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    AuthorizationService.enforce_analysis_access(db, current_user, analysis)

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
    from prescripto.db.models.document import PrescriptionDocument
    from prescripto.db.models.analysis import AnalysisStage
    from prescripto.db.models.medication import PrescriptionMedication
    from prescripto.db.models.safety import RiskFinding
    from prescripto.db.models.patient import Patient
    from prescripto.application.services.llm_explainer import llm_explainer

    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    AuthorizationService.enforce_analysis_access(db, current_user, analysis)

    doc = db.query(PrescriptionDocument).filter(
        PrescriptionDocument.id == analysis.document_id
    ).first()

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

    stage_extraction = db.query(AnalysisStage).filter(
        AnalysisStage.analysis_id == id,
        AnalysisStage.stage_name == "STRUCTURED_EXTRACTION",
    ).first()
    document_context = stage_extraction.output_json if stage_extraction and stage_extraction.output_json else {}

    if not patient_info and document_context.get("patient_details"):
        patient_info = document_context["patient_details"]

    return llm_explainer.explain(
        medications=med_dicts,
        findings=finding_dicts,
        patient_info=patient_info,
        document_context=document_context,
    )


@router.patch(
    "/{id}/medications",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Update or correct medication lines for an analysis (Doctor or Patient editing)",
    operation_id="updateAnalysisMedications",
)
def update_analysis_medications(
    id: uuid.UUID,
    update_req: MedicationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    """
    Allows authorized clinicians or the uploading patient to edit recognized medication fields,
    re-runs canonical normalization and safety screening, and recalculates review triggers.
    Preserves original raw values in an audit trail.
    """
    from fastapi import HTTPException
    from prescripto.db.base import utc_now
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

    doc = db.query(PrescriptionDocument).filter(
        PrescriptionDocument.id == analysis.document_id
    ).first()

    # Authorization: Staff or document owner
    is_staff = current_user.role in (Role.REVIEWER.value, Role.ADMIN.value, "DOCTOR", "CLINICIAN")
    is_owner = (doc is not None and doc.uploader_id == current_user.id)
    if not (is_staff or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to edit medications for this analysis",
        )

    if analysis.status not in ["REQUIRES_REVIEW", "REVIEWING", "COMPLETED", "REVIEWED_COMPLETE", "REVIEWED_ESCALATED"]:
        raise HTTPException(status_code=409, detail=f"Cannot edit medications when analysis is in status '{analysis.status}'")

    now = utc_now()
    for item in update_req.medications:
        med = db.query(PrescriptionMedication).filter(
            PrescriptionMedication.analysis_id == id,
            PrescriptionMedication.line_index == item.line_index,
        ).first()
        if med:
            # Preserve original extracted raw values on first edit
            if not getattr(med, "is_edited", False):
                med.original_name_raw = med.name_raw
                med.original_strength_raw = med.strength_raw
                med.original_dose_raw = med.dose_raw
                med.original_frequency_raw = med.frequency_raw
                med.original_route_raw = med.route_raw
                med.original_duration_raw = med.duration_raw
                med.original_instructions_raw = med.instructions_raw

            med.is_edited = True
            med.edited_by_user_id = current_user.id
            med.edited_at = now

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


@router.post(
    "/{id}/retry",
    response_model=AnalysisStatus,
    status_code=status.HTTP_200_OK,
    summary="Retry a failed prescription analysis",
    operation_id="retryAnalysis",
)
def retry_analysis(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisStatus:
    """
    Retries an analysis that is in 'FAILED' status.
    Resets status to 'QUEUED', clears error_detail, and enqueues a new pending job.
    """
    from prescripto.db.base import utc_now
    from prescripto.db.models.analysis import Analysis, AnalysisJob
    from prescripto.db.models.document import PrescriptionDocument

    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    doc = db.query(PrescriptionDocument).filter(
        PrescriptionDocument.id == analysis.document_id
    ).first()

    # Security check: owner or clinician/reviewer/admin
    is_staff = current_user.role in (Role.REVIEWER.value, Role.ADMIN.value, "DOCTOR", "CLINICIAN")
    is_owner = (doc is not None and doc.uploader_id == current_user.id)
    if not (is_staff or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to retry this analysis",
        )

    if analysis.status != "FAILED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot retry analysis in status '{analysis.status}'. Only FAILED analyses can be retried.",
        )

    # Reset analysis to QUEUED
    analysis.status = "QUEUED"
    analysis.error_detail = None
    analysis.started_at = None
    analysis.completed_at = None

    # Reset existing job or add new job
    job = db.query(AnalysisJob).filter(AnalysisJob.analysis_id == id).first()
    now = utc_now()
    if job:
        job.status = "PENDING"
        job.retry_count = 0
        job.lease_owner = None
        job.lease_token = 0
        job.lease_expires_at = None
        job.heartbeat_at = None
        job.backoff_until = None
        job.last_error = None
        job.updated_at = now
    else:
        job = AnalysisJob(
            id=uuid.uuid4(),
            analysis_id=id,
            status="PENDING",
            retry_count=0,
            max_retries=3,
            created_at=now,
            updated_at=now,
        )
        db.add(job)

    db.commit()

    use_case = GetAnalysisStatusUseCase(db=db)
    return use_case.execute(analysis_id=id, caller=current_user)
