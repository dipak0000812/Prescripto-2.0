"""
Prescripto AI 2.0 — Central Application Settings.
Validates environment configuration on startup per docs/DEPLOYMENT.md.
"""
import os
from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime Environment
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    # Database
    # Host default uses Compose's published port (5435). Inside Docker, compose
    # overrides this to postgres:5432 on the internal network.
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://prescripto:prescripto_secret@localhost:5435/prescripto_db"
    )
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)

    # CORS Configuration
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )

    # Object Storage (MinIO / S3)
    S3_ENDPOINT: str = Field(default="http://localhost:9000")
    S3_BUCKET: str = Field(default="prescripto")
    S3_ACCESS_KEY: str = Field(default="minioadmin")
    S3_SECRET_KEY: str = Field(default="minioadmin")
    S3_REGION: str = Field(default="us-east-1")
    RETENTION_VAULT_BUCKET: str = Field(default="prescripto-retention")

    # Authentication & JWT (RS256)
    JWT_PRIVATE_KEY: str = Field(default="")
    JWT_PUBLIC_KEY: str = Field(default="")
    JWT_ACCESS_TTL: int = Field(default=900)  # 15 minutes
    JWT_REFRESH_TTL: int = Field(default=604800)  # 7 days

    # Machine Learning & OCR Configuration
    OCR_MODEL_NAME: str = Field(default="trocr-handwritten-v1")
    OCR_MODEL_VERSION: str = Field(default="1.0.0")
    OCR_DEVICE: str = Field(default="cpu")
    MODEL_CACHE_DIR: str = Field(default="/tmp/prescripto_models")

    # ML Service integration
    # ML_RUNTIME_MODE=remote (ml-service) is disabled. Leave "rapidocr" so local
    # RapidOCR can run only as a Gemini quota/auth/timeout fallback.
    #   "rapidocr" — RapidOCRRuntime (Gemini fallback; ONNX PaddleOCR on CPU)
    #   "mock"     — MockModelRuntime (hermetic testing)
    #   "remote"   — unused; do not enable
    ML_RUNTIME_MODE: str = Field(default="rapidocr")
    ML_SERVICE_URL: str = Field(default="http://localhost:8001")

    # Machine Learning & Vision Recognition Providers
    RECOGNITION_PROVIDER: str = Field(default="gemini")
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash")
    GEMINI_FALLBACK_MODEL: str = Field(default="gemini-3.1-flash-lite")

    # Feature & Safety Flags
    LLM_ENABLED: bool = Field(default=False)
    ENABLED_KNOWLEDGE_PROVIDERS: str = Field(default="openfda,cdsco")
    LICENSE_MODE_ALLOWED: str = Field(default="COMMERCIAL_PERMISSIVE")
    OPENFDA_API_KEY: Optional[str] = Field(default=None)

    # Ingestion & Retention Limits
    RETENTION_DAYS: int = Field(default=30)
    MAX_UPLOAD_BYTES: int = Field(default=20971520)  # 20 MB

    # Worker Engine Configuration (Phase 3 / Slice 2)
    WORKER_ID: Optional[str] = Field(default=None)
    WORKER_POLL_INTERVAL: float = Field(default=2.0)
    WORKER_LEASE_SECONDS: int = Field(default=600)  # 10 minutes
    WORKER_HEARTBEAT_SECONDS: int = Field(default=30)
    WORKER_MAX_RETRIES: int = Field(default=3)

    @property
    def knowledge_providers_list(self) -> List[str]:
        return [p.strip() for p in self.ENABLED_KNOWLEDGE_PROVIDERS.split(",") if p.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            # If a Windows local SQLite path was copied into a Linux container on Render/Cloud
            if v.startswith("sqlite:") and os.name != "nt":
                if ":/" in v[8:] or ":\\" in v or "\\" in v or "users" in v.lower():
                    return "sqlite:///prescripto.db"
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg2://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
                return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @field_validator("OCR_MODEL_VERSION")
    @classmethod
    def validate_no_latest(cls, v: str) -> str:
        if v.lower() == "latest":
            raise ValueError("OCR_MODEL_VERSION must be an exact pinned version, never 'latest'.")
        return v

    @model_validator(mode="after")
    def ensure_jwt_keys(self) -> "Settings":
        """Auto-generate valid RSA keys if missing, preventing 500 errors on authentication."""
        has_priv = bool((self.JWT_PRIVATE_KEY or "").strip())
        has_pub = bool((self.JWT_PUBLIC_KEY or "").strip())
        if not has_priv or not has_pub:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            priv_pem = priv.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")
            pub_pem = priv.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")
            self.JWT_PRIVATE_KEY = priv_pem
            self.JWT_PUBLIC_KEY = pub_pem
        return self

    def log_missing_gemini_api_key(self) -> None:
        """Logs once when GEMINI_API_KEY is unset. Does not print the key."""
        if (self.GEMINI_API_KEY or "").strip():
            return
        from prescripto.audit.logger import get_logger

        get_logger("prescripto.config").error(
            "GEMINI_API_KEY is not configured. Set it in backend/.env before using Gemini recognition."
        )


settings = Settings()
