"""
BorderVision v2.0 — Application Configuration

Loads settings from environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application configuration via environment variables."""

    # ─── Application ───────────────────────────────────────────
    APP_NAME: str = "BorderVision"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-32",
        description="JWT signing secret"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # ─── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ─── PostgreSQL ────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "bordervision"
    POSTGRES_USER: str = "bv_admin"
    POSTGRES_PASSWORD: str = "bv_secure_password_change_me"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ─── Qdrant ────────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None

    # ─── Retention Policies ────────────────────────────────────
    EVENT_RETENTION_DAYS: int = 90
    PERSON_RETENTION_DAYS: int = 30

    # ─── Vision Pipeline ───────────────────────────────────────
    DETECTION_CONFIDENCE: float = 0.5
    CROSSING_HYSTERESIS_FRAMES: int = 5
    APPEARANCE_EXTRACT_INTERVAL_SEC: float = 1.0
    POSE_FRAME_INTERVAL: int = 3  # every Nth frame
    GAIT_SEQUENCE_LENGTH: int = 25

    # ─── Fusion Thresholds ─────────────────────────────────────
    FUSION_POSITIVE_THRESHOLD: float = 0.82
    FUSION_POSITIVE_COVERAGE: float = 0.60
    FUSION_CANDIDATE_THRESHOLD: float = 0.65
    TEMPORAL_DECAY_HALF_LIFE_DAYS: int = 30

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
