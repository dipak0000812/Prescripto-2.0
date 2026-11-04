"""
Prescripto AI 2.0 — FastAPI Modular Monolith Entrypoint.
Conforms strictly to docs/API-CONTRACT.md and docs/ERROR-CONTRACT.md.
"""
import uuid
import time
from typing import Callable, Optional
from pathlib import Path
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from prescripto.config.settings import settings
from prescripto.audit.logger import configure_logging, get_logger
from prescripto.application.exceptions import ApplicationException
from prescripto.api.v1.routers.auth import router as auth_router
from prescripto.api.v1.routers.health import router as health_router
from prescripto.api.v1.routers.prescriptions import router as prescriptions_router
from prescripto.api.v1.routers.analyses import router as analyses_router
from prescripto.api.v1.routers.patients import router as patients_router

# Configure zero-PHI logging on startup
configure_logging(settings.LOG_LEVEL)
logger = get_logger("prescripto.api")

app = FastAPI(
    title="Prescripto AI 2.0 API",
    version="1.0.0",
    description="Prescription document intelligence and medication-safety decision support.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware supporting explicit origins, localhost, and Vercel domains
cors_origins = settings.cors_origins_list
cors_kwargs = {
    "allow_origins": cors_origins,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["X-Request-ID"],
}
if "*" in cors_origins:
    cors_kwargs["allow_origin_regex"] = r"https?://.*"
app.add_middleware(CORSMiddleware, **cors_kwargs)


@app.middleware("http")
async def request_middleware(request: Request, call_next: Callable) -> Response:
    """Injects and correlates X-Request-ID across the request lifecycle and structured logs."""
    raw_request_id = request.headers.get("X-Request-ID")
    try:
        request_id = uuid.UUID(raw_request_id) if raw_request_id else uuid.uuid4()
    except ValueError:
        request_id = uuid.uuid4()

    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = str(request_id)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Operational structured log (Whitelisted keys only: Zero PHI)
    logger.info(
        "http_request_finished",
        request_id=str(request_id),
        http_method=request.method,
        http_path=request.url.path,
        http_status_code=response.status_code,
        duration_ms=duration_ms,
    )

    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Formats HTTP exceptions into canonical ERROR-CONTRACT envelope."""
    request_id = getattr(request.state, "request_id", uuid.uuid4())
    
    code = "INTERNAL_ERROR"
    message = str(exc.detail)

    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", "INTERNAL_ERROR")
        message = exc.detail.get("message", "An error occurred")
    elif exc.status_code == 401:
        code = "INVALID_CREDENTIALS"
    elif exc.status_code == 403:
        code = "INSUFFICIENT_ROLE"
    elif exc.status_code == 404:
        code = "RESOURCE_NOT_FOUND"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": str(request_id),
            }
        },
        headers={"X-Request-ID": str(request_id)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Formats schema validation failures into MALFORMED_REQUEST."""
    request_id = getattr(request.state, "request_id", uuid.uuid4())
    errors = exc.errors()
    msg = errors[0].get("msg", "Malformed request schema") if errors else "Validation error"

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "MALFORMED_REQUEST",
                "message": f"Validation failed: {msg}",
                "request_id": str(request_id),
            }
        },
        headers={"X-Request-ID": str(request_id)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Formats unexpected exceptions into generic INTERNAL_ERROR with zero trace leak."""
    request_id = getattr(request.state, "request_id", uuid.uuid4())
    logger.error("unhandled_server_error", request_id=str(request_id), error_code="INTERNAL_ERROR")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected internal server error occurred",
                "request_id": str(request_id),
            }
        },
        headers={"X-Request-ID": str(request_id)},
    )


@app.exception_handler(ApplicationException)
async def application_exception_handler(request: Request, exc: ApplicationException) -> JSONResponse:
    """Formats domain and application exceptions into canonical ERROR-CONTRACT envelope."""
    request_id = getattr(request.state, "request_id", uuid.uuid4())
    logger.warning(
        "application_exception_handled",
        request_id=str(request_id),
        error_code=exc.code,
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": str(request_id),
            }
        },
        headers={"X-Request-ID": str(request_id)},
    )


def _find_frontend_dist() -> Optional[Path]:
    """Locate built frontend assets across local dev and container layouts."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "web" / "dist",
        Path(__file__).resolve().parent.parent.parent / "web" / "dist",
        Path("/app/web/dist"),
        Path("/app/backend/web/dist"),
        Path("web/dist"),
        Path("../web/dist"),
    ]
    for c in candidates:
        if c.exists() and (c / "index.html").is_file():
            return c
    return None


def get_api_discovery_payload() -> dict:
    """Returns top-level metadata, status, health URLs, and API endpoints."""
    return {
        "name": "Prescripto AI 2.0 API",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "health_url": "/health",
        "database_health_url": "/health/db",
        "readiness_url": "/health/ready",
        "api_v1_base": "/api/v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "prescriptions": "/api/v1/prescriptions",
            "analyses": "/api/v1/analyses",
            "patients": "/api/v1/patients",
            "health": "/api/v1/health",
        },
    }


# Register API Routers
# Root health endpoints (/health, /health/db, /health/ready) for cloud orchestrators (Render, K8s)
app.include_router(health_router, tags=["Health"])

# Versioned v1 Routers (/api/v1/*)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(prescriptions_router, prefix="/api/v1")
app.include_router(analyses_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")


@app.get("/api", tags=["System"], summary="API Discovery Index")
@app.get("/api/v1", tags=["System"], summary="API v1 Discovery Index")
def api_discovery():
    return JSONResponse(content=get_api_discovery_payload())


@app.get("/docs/", include_in_schema=False)
def docs_slash_redirect():
    return RedirectResponse(url="/docs")


@app.get("/redoc/", include_in_schema=False)
def redoc_slash_redirect():
    return RedirectResponse(url="/redoc")


@app.get("/", tags=["System"], summary="Root Application Entrypoint & Discovery")
def root_endpoint(request: Request):
    """
    Serves the React frontend application to web browsers,
    or API discovery JSON to API clients and automated scrapers.
    """
    accept = request.headers.get("accept", "")
    wants_html = "text/html" in accept
    force_json = request.query_params.get("format") == "json"

    dist_dir = _find_frontend_dist()
    if dist_dir and wants_html and not force_json:
        index_file = dist_dir / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)

    return JSONResponse(content=get_api_discovery_payload())


@app.get("/api/v1/storage/{key:path}", tags=["Storage"], include_in_schema=False)
def get_storage_file(
    key: str,
    expires: Optional[int] = None,
    signature: Optional[str] = None,
) -> Response:
    """Serves stored prescription images with HMAC signature and expiry check."""
    import mimetypes
    from prescripto.storage.client import StorageClient, get_storage_client
    from prescripto.storage.exceptions import StorageObjectNotFoundException

    if not expires or not signature:
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "FORBIDDEN_RESOURCE_ACCESS",
                    "message": "Access to storage resource requires valid signature and expiry",
                    "request_id": str(uuid.uuid4()),
                }
            },
        )

    if not StorageClient.verify_storage_signature(key, expires, signature):
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "FORBIDDEN_RESOURCE_ACCESS",
                    "message": "Storage signature has expired or is invalid",
                    "request_id": str(uuid.uuid4()),
                }
            },
        )

    sc = get_storage_client()
    try:
        content = sc.get_object(key)
        media_type, _ = mimetypes.guess_type(key)
        return Response(content=content, media_type=media_type or "application/octet-stream")
    except StorageObjectNotFoundException:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Object {key} not found", "request_id": str(uuid.uuid4())}},
        )
    except Exception:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Object {key} not found", "request_id": str(uuid.uuid4())}},
        )


# Mount static assets if frontend distribution exists
frontend_dist = _find_frontend_dist()
if frontend_dist:
    assets_dir = frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str):
    """
    SPA client-side routing fallback:
    Serves index.html for client routes (e.g. /login, /prescriptions),
    serves static files if present, or returns 404 for missing API/system routes.
    """
    dist_dir = _find_frontend_dist()
    if not dist_dir:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": f"Endpoint /{full_path} not found",
                    "request_id": str(uuid.uuid4()),
                }
            },
        )

    # API and docs routes should not fall back to index.html
    reserved_prefixes = ("api/", "docs", "redoc", "openapi.json", "health")
    if full_path.startswith(reserved_prefixes):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": f"Endpoint /{full_path} not found",
                    "request_id": str(uuid.uuid4()),
                }
            },
        )

    static_file = dist_dir / full_path
    if static_file.is_file():
        return FileResponse(static_file)

    index_file = dist_dir / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": f"Resource /{full_path} not found",
                "request_id": str(uuid.uuid4()),
            }
        },
    )


import threading

def _run_worker_daemon():
    try:
        from prescripto.worker.main import WorkerRunner
        runner = WorkerRunner(poll_interval=1.0)
        runner.start()
    except Exception as e:
        logger.warning("background_worker_daemon_stopped", error=str(e))


@app.on_event("startup")
def startup_event():
    # Only spawn worker thread if not in test suite environment
    import os
    settings.log_missing_gemini_api_key()
    if os.environ.get("PYTEST_CURRENT_TEST") is None:
        t = threading.Thread(target=_run_worker_daemon, daemon=True)
        t.start()


