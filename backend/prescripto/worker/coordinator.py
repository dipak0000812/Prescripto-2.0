"""
Pipeline Coordinator for Prescripto AI 2.0.
Coordinates the execution of the 8 canonical analysis stages with lease check gates.
"""
import uuid
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.orm import Session

from prescripto.db.models.analysis import Analysis
from prescripto.db.models.document import PrescriptionDocument
from prescripto.worker.queue import JobClaim, QueuePoller
from prescripto.worker.fence import commit_stage_result
from prescripto.worker.heartbeat import HeartbeatManager
from prescripto.worker.exceptions import WorkerFencedError
from prescripto.audit.logger import get_logger

logger = get_logger("prescripto.worker.coordinator")

CANONICAL_STAGES = [
    "INGESTION",
    "QUALITY_CHECK",
    "TEXT_DETECTION",
    "OCR_RECOGNITION",
    "STRUCTURED_EXTRACTION",
    "MEDICATION_NORMALIZATION",
    "SAFETY_SCREENING",
    "REPORT_ASSEMBLY",
]


class PipelineCoordinator:
    """
    Coordinates stage-by-stage execution of a claimed analysis job.
    Guarantees generation fencing between stages and lease validation before writes.
    """

    def __init__(
        self,
        db: Session,
        claim: JobClaim,
        stages: Optional[List[str]] = None,
        stage_handlers: Optional[Dict[str, Callable[[Session, Analysis, PrescriptionDocument, Dict[str, Any]], Dict[str, Any]]]] = None,
    ) -> None:
        self.db = db
        self.claim = claim
        self.stages = stages or CANONICAL_STAGES
        self.stage_handlers = stage_handlers or {}

    def _default_stage_handler(
        self,
        stage_name: str,
        analysis: Analysis,
        document: Optional[PrescriptionDocument],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Baseline stage execution handler."""
        return {
            "stage": stage_name,
            "analysis_id": str(analysis.id),
            "document_id": str(analysis.document_id),
            "status": "COMPLETED",
            "pipeline_version": analysis.pipeline_version,
        }

    def execute(self, heartbeat: Optional[HeartbeatManager] = None) -> Dict[str, Any]:
        """
        Executes all configured pipeline stages in strict sequence.
        Validates fencing before and after each stage commit.
        """
        analysis = self.db.query(Analysis).filter(Analysis.id == self.claim.analysis_id).first()
        if not analysis:
            raise ValueError(f"Analysis {self.claim.analysis_id} not found")

        document = self.db.query(PrescriptionDocument).filter(
            PrescriptionDocument.id == analysis.document_id
        ).first()

        context: Dict[str, Any] = {
            "analysis_id": str(analysis.id),
            "document_id": str(analysis.document_id),
            "stages": {},
        }

        for stage_name in self.stages:
            # 1. Lease check gate prior to stage execution
            if heartbeat:
                heartbeat.check_fence()

            logger.info(
                "stage_executing",
                analysis_id=str(analysis.id),
                stage=stage_name,
                lease_token=self.claim.lease_token,
            )

            # 2. Run stage logic (custom handler or default)
            handler = self.stage_handlers.get(stage_name)
            if handler:
                stage_output = handler(self.db, analysis, document, context)
            else:
                stage_output = self._default_stage_handler(stage_name, analysis, document, context)

            context["stages"][stage_name] = stage_output

            # 3. Lease check gate prior to commit
            if heartbeat:
                heartbeat.check_fence()

            # 4. Atomic generation fenced commit
            commit_stage_result(
                db=self.db,
                analysis_id=self.claim.analysis_id,
                stage_name=stage_name,
                lease_token=self.claim.lease_token,
                lease_owner=self.claim.lease_owner,
                output=stage_output,
                status="COMPLETED",
            )

        # 5. Mark entire job succeeded
        QueuePoller.mark_job_succeeded(
            db=self.db,
            job_id=self.claim.job_id,
            lease_token=self.claim.lease_token,
            worker_id=self.claim.lease_owner,
        )

        return context
