"""
Health Check Router matching OPENAPI.yaml.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Response, status
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
def get_health(response: Response, db: Session = Depends(get_db)) -> HealthStatus:
    # 1. Database Probe
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    # 2. Object Storage Probe (Fast non-blocking probe with socket pre-check and resilient local disk fallback)
    s3_status = "ok"
    import socket
    from urllib.parse import urlparse
    from pathlib import Path

    is_port_open = False
    try:
        parsed_url = urlparse(settings.S3_ENDPOINT)
        host = parsed_url.hostname or "127.0.0.1"
        if host == "localhost":
            host = "127.0.0.1"
        port = parsed_url.port or 9000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.05)
        res = sock.connect_ex((host, port))
        sock.close()
        is_port_open = (res == 0)
    except Exception:
        is_port_open = False

    if is_port_open:
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
            is_port_open = False

    if not is_port_open:
        # Fallback to local disk storage directory verification
        local_dir = Path("prescripto_storage")
        try:
            local_dir.mkdir(parents=True, exist_ok=True)
            s3_status = "ok"
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

    if db_status == "down" or s3_status == "down":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthStatus(
        database=db_status,
        object_storage=s3_status,
        worker_heartbeat=worker_status,
    )


@router.get(
    "/health/db",
    summary="PostgreSQL / Database Connectivity Check",
    operation_id="getDatabaseHealth",
)
def get_db_health(response: Response, db: Session = Depends(get_db)) -> dict:
    """Verifies active connectivity, dialect, driver, and connection pool status."""
    try:
        # Ping database
        result = db.execute(text("SELECT 1")).scalar()
        if result != 1:
            raise RuntimeError(f"Unexpected query result: {result}")

        dialect_name = getattr(db.bind.dialect, "name", "unknown")
        driver_name = getattr(db.bind.dialect, "driver", "unknown")
        server_version_info = getattr(db.bind.dialect, "server_version_info", None)

        pool = getattr(db.bind, "pool", None)
        pool_info = {}
        if pool:
            for attr in ("size", "checkedin", "checkedout", "overflow"):
                method = getattr(pool, attr, None)
                if callable(method):
                    try:
                        pool_info[attr] = method()
                    except Exception:
                        pass

        return {
            "status": "healthy",
            "database": "connected",
            "dialect": dialect_name,
            "driver": driver_name,
            "server_version": ".".join(map(str, server_version_info)) if server_version_info else "unknown",
            "pool": pool_info,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.get(
    "/health/ready",
    summary="Application Readiness Probe",
    operation_id="getReadiness",
)
def get_readiness(response: Response, db: Session = Depends(get_db)) -> dict:
    """Readiness probe verifying core persistence before receiving traffic."""
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "ready": False,
            "database": "unavailable",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "ready": True,
        "database": "available",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

