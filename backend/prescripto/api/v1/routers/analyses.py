"""
Prescripto AI 2.0 — Analyses and Review Router.
Implements:
- GET /analyses/{id} (Current status & stage breakdown)
- GET /analyses/{id}/result (Full structured report with result gating)
- POST /analyses/{id}/review (Reviewer submission & status transition)
"""
import uuid
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
