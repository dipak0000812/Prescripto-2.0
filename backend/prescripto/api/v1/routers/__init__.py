"""
API v1 Routers.
"""
from prescripto.api.v1.routers.auth import router as auth_router
from prescripto.api.v1.routers.health import router as health_router
from prescripto.api.v1.routers.prescriptions import router as prescriptions_router

__all__ = [
    "auth_router",
    "health_router",
    "prescriptions_router",
]
