"""
ML Service Configuration.
All settings loaded from environment variables; no hard-coded values.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ML_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    PORT: int = Field(default=8001)
    LOG_LEVEL: str = Field(default="INFO")

    # Model / device — controlled by deployment, NOT by API callers
    DEVICE: str = Field(default="cpu")
    MODEL_NAME: str = Field(default="PP-OCRv6")
    MODEL_VERSION: str = Field(default="6.0.0")

    # Quality-check thresholds (matching engine.py production values)
    MIN_IMAGE_DIMENSION: int = Field(default=400)
    BLANK_CONTRAST_THRESHOLD: int = Field(default=5)

    # Payload limit (bytes) — default 20 MB
    MAX_UPLOAD_BYTES: int = Field(default=20971520)


settings = MLSettings()
