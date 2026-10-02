"""
Atomic Generation Fencing & Stage Result Persistence.
Guarantees at-most-once write per lease generation and prevents zombie worker commits.
"""
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from prescripto.db.base import utc_now, ensure_utc
from prescripto.db.models.analysis import AnalysisJob, AnalysisStage
from prescripto.worker.exceptions import WorkerFencedError
from prescripto.audit.logger import get_logger

logger = get_logger("prescripto.worker.fence")


def commit_stage_result(
    db: Session,
    analysis_id: uuid.UUID,
    stage_name: str,
    lease_token: int,
    lease_owner: str,
    output: Dict[str, Any],
    error_code: Optional[str] = None,
    status: str = "COMPLETED",
) -> AnalysisStage:
    """
    Persists stage output guarded by generation token and active lease validation.
    
    1. Validates that the worker holds the currently valid, non-expired lease
       in the exact same transaction (FOR SHARE on PostgreSQL).
    2. Guards against writes where a newer worker generation already committed
       (analysis_stages.lease_token <= lease_token).
    3. Raises WorkerFencedError on lease expiration or token supersession.
    """
    now = utc_now()

    # Step 1: Validate active lease ownership
    job_query = db.query(AnalysisJob).filter(
        AnalysisJob.analysis_id == analysis_id,
        AnalysisJob.lease_token == lease_token,
        AnalysisJob.lease_owner == lease_owner,
        AnalysisJob.status == "RUNNING",
    )

    if db.bind and db.bind.dialect.name == "postgresql":
        job_query = job_query.with_for_update(read=True)

    job = job_query.first()

    if not job:
        logger.warning(
            "worker_fenced_lease_missing",
            analysis_id=str(analysis_id),
            lease_token=lease_token,
            lease_owner=lease_owner,
            stage=stage_name,
        )
        raise WorkerFencedError(
            f"Worker '{lease_owner}' with token {lease_token} has been fenced: no active RUNNING lease."
        )

    # Expiry check
    lease_exp = ensure_utc(job.lease_expires_at)
    if lease_exp is None or lease_exp <= now:
        logger.warning(
            "worker_fenced_lease_expired",
            analysis_id=str(analysis_id),
            lease_token=lease_token,
            lease_owner=lease_owner,
            stage=stage_name,
        )
        raise WorkerFencedError(
            f"Worker '{lease_owner}' with token {lease_token} has been fenced: lease expired at {job.lease_expires_at}."
        )

    # Step 2: Check existing stage record for generation fencing
    existing_stage = (
        db.query(AnalysisStage)
        .filter(
            AnalysisStage.analysis_id == analysis_id,
            AnalysisStage.stage_name == stage_name,
        )
        .first()
    )

    if existing_stage:
        if existing_stage.lease_token > lease_token:
            logger.warning(
                "stage_commit_superseded",
                analysis_id=str(analysis_id),
                stage=stage_name,
                current_token=lease_token,
                existing_token=existing_stage.lease_token,
            )
            raise WorkerFencedError(
                f"Stage '{stage_name}' commit rejected: newer stage generation already committed "
                f"({existing_stage.lease_token} > {lease_token})."
            )

        existing_stage.lease_token = lease_token
        existing_stage.status = status
        existing_stage.output_json = output
        existing_stage.error_code = error_code
        existing_stage.completed_at = now
        stage = existing_stage
    else:
        stage = AnalysisStage(
            id=uuid.uuid4(),
            analysis_id=analysis_id,
            stage_name=stage_name,
            lease_token=lease_token,
            status=status,
            output_json=output,
            error_code=error_code,
            started_at=now,
            completed_at=now,
        )
        db.add(stage)

    db.flush()

    logger.info(
        "stage_result_committed",
        analysis_id=str(analysis_id),
        stage=stage_name,
        lease_token=lease_token,
        status=status,
    )
    return stage
