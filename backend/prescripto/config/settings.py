"""
Prescripto AI 2.0 — Central Application Settings.
Validates environment configuration on startup per docs/DEPLOYMENT.md.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime Environment
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://prescripto:prescripto_secret@localhost:5432/prescripto_db"
    )
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)

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
    MODEL_CACHE_DIR: str = Field(default="/tmp/prescripto_models")

    # Feature & Safety Flags
    LLM_ENABLED: bool = Field(default=False)
    ENABLED_KNOWLEDGE_PROVIDERS: str = Field(default="openfda,cdsco")
    LICENSE_MODE_ALLOWED: str = Field(default="COMMERCIAL_PERMISSIVE")
    OPENFDA_API_KEY: Optional[str] = Field(default=None)

    # Ingestion & Retention Limits
    RETENTION_DAYS: int = Field(default=30)
    MAX_UPLOAD_BYTES: int = Field(default=20971520)  # 20 MB

    @property
    def knowledge_providers_list(self) -> List[str]:
        return [p.strip() for p in self.ENABLED_KNOWLEDGE_PROVIDERS.split(",") if p.strip()]

    @field_validator("OCR_MODEL_VERSION")
    @classmethod
    def validate_no_latest(cls, v: str) -> str:
        if v.lower() == "latest":
            raise ValueError("OCR_MODEL_VERSION must be an exact pinned version, never 'latest'.")
        return v


settings = Settings()
