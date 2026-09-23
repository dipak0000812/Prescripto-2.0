"""
Prescripto AI 2.0 — FastAPI Modular Monolith Entrypoint.
Conforms strictly to docs/API-CONTRACT.md and docs/ERROR-CONTRACT.md.
"""
import uuid
import time
from typing import Callable
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from prescripto.config.settings import settings
from prescripto.audit.logger import configure_logging, get_logger
from prescripto.api.v1.routers.auth import router as auth_router
from prescripto.api.v1.routers.health import router as health_router

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

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# Register API v1 Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
