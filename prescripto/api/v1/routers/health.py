"""
Health Check Router matching OPENAPI.yaml.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from prescripto.config.settings import settings
from prescripto.db.session import get_db
from prescripto.db.models.analysis import AnalysisJob
from prescripto.api.v1.schemas.health import HealthStatus

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="System health check",
    operation_id="getHealth",
)
def get_health(db: Session = Depends(get_db)) -> HealthStatus:
    # 1. Database Probe
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    # 2. Object Storage Probe (Fast non-blocking probe with 0.5s timeout)
    s3_status = "ok"
    try:
        fast_config = Config(
            connect_timeout=0.5,
            read_timeout=0.5,
            retries={"max_attempts": 0},
        )
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=fast_config,
        )
        s3_client.list_buckets()
    except Exception:
        s3_status = "down"

    # 3. Worker Heartbeat Probe
    worker_status = "ok"
    try:
        two_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=2)
        recent_worker = db.query(AnalysisJob).filter(
            AnalysisJob.heartbeat_at >= two_mins_ago
        ).first()
        if not recent_worker:
            stale_jobs = db.query(AnalysisJob).filter(
                AnalysisJob.status == "RUNNING",
                AnalysisJob.heartbeat_at < two_mins_ago
            ).first()
            worker_status = "stale" if stale_jobs else "ok"
    except Exception:
        worker_status = "down"

    return HealthStatus(
        database=db_status,
        object_storage=s3_status,
        worker_heartbeat=worker_status,
    )
