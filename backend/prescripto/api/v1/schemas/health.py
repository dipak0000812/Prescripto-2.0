"""
Health Status Schema matching OPENAPI.yaml.
"""
from typing import Literal
from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    database: Literal["ok", "degraded", "down"] = Field(..., description="PostgreSQL connectivity state")
    object_storage: Literal["ok", "degraded", "down"] = Field(..., description="MinIO/S3 connectivity state")
    worker_heartbeat: Literal["ok", "stale", "down"] = Field(..., description="Analysis worker heartbeat state")
