"""
Use case for submitting clinical review decisions.
Conforms to docs/API-CONTRACT.md and docs/ERROR-CONTRACT.md.
"""
import uuid
from sqlalchemy.orm import Session

from prescripto.db.models.analysis import Analysis
from prescripto.db.models.review import Review
from prescripto.db.models.users import User
from prescripto.db.base import utc_now
from prescripto.application.exceptions import (
    ResourceNotFoundException,
    AnalysisNotReviewableException,
)
from prescripto.api.v1.schemas.analysis import ReviewSubmission, ReviewRecord


class SubmitReviewUseCase:
    """Records human reviewer decisions and transitions analysis status."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(
        self,
        analysis_id: uuid.UUID,
        submission: ReviewSubmission,
        reviewer: User,
    ) -> ReviewRecord:
        analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ResourceNotFoundException(f"Analysis {analysis_id} not found")

        # Must be in a reviewable state
        if analysis.status not in ["REQUIRES_REVIEW", "REVIEWING"]:
            raise AnalysisNotReviewableException(
                f"Analysis {analysis_id} is in status '{analysis.status}' and cannot be reviewed"
            )

        # Check if any decision is escalated
        has_escalation = any(d.action == "ESCALATED" for d in submission.decisions)
        overall_status = "REVIEWED_ESCALATED" if has_escalation else "REVIEWED_COMPLETE"

        # Record review in reviews table
        review_id = uuid.uuid4()
        submitted_at = utc_now()

        review = Review(
            id=review_id,
            analysis_id=analysis_id,
            reviewer_id=reviewer.id,
            status="SUBMITTED",
            corrections={"decisions": [d.model_dump(mode="json") for d in submission.decisions]},
            notes=submission.decisions[0].notes if submission.decisions else None,
            submitted_at=submitted_at,
        )
        self.db.add(review)

        # Transition analysis status
        analysis.status = overall_status
        self.db.commit()

        return ReviewRecord(
            review_id=review_id,
            analysis_id=analysis_id,
            reviewer_id=reviewer.id,
            submitted_at=submitted_at,
            overall_status=overall_status,
        )
