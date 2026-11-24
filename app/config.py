# PLAN TASK: 1 | STUDENT TASK PACK: Day 1 | EVIDENCE: ONB-01
# WHERE: runtime configuration for API, template service, database, and admin hook
# DO: change environment variables here when setting up your own test environment;
# record the values you used in ONB-01 rather than editing source defaults.
"""Runtime settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


VALID_VARIANTS = {"A", "B", "C"}


def _as_bool(value: str) -> bool:
    """Interpret a string environment value as a boolean."""
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Documented runtime settings with defaults from the product build spec."""

    # PLAN TASK: 1 | STUDENT TASK PACK: Day 1 | EVIDENCE: ONB-01
    # WHERE: variant selection and service ports
    # DO: VARIANT is pre-set for this repository; override only when instructed.
    variant: str = "A"
    port: int = 8000
    max_batch: int = 1
    latency_ms: int = 0
    max_body_kb: int = 256

    # PLAN TASK: 1 | STUDENT TASK PACK: Day 1 | EVIDENCE: ONB-01
    # WHERE: model artefact, SQLite path, logging, and dependency URL
    # DO: record these values in your environment onboarding evidence.
    model_path: str = "model/artefacts/sentiment.joblib"
    db_path: str = "data/supportsense.db"
    log_level: str = "INFO"
    allow_admin: bool = True
    suggest_service_url: str = "http://suggest:8001"

    def __post_init__(self) -> None:
        """Validate settings that have a restricted value set."""
        normalized = self.variant.upper()
        if normalized not in VALID_VARIANTS:
            raise ValueError(f"VARIANT must be one of {sorted(VALID_VARIANTS)}")
        object.__setattr__(self, "variant", normalized)


def get_settings() -> Settings:
    """Build settings from the current process environment."""
    return Settings(
        variant=os.getenv("VARIANT", "A"),
        port=int(os.getenv("PORT", "8000")),
        max_batch=int(os.getenv("MAX_BATCH", "1")),
        latency_ms=int(os.getenv("LATENCY_MS", "0")),
        max_body_kb=int(os.getenv("MAX_BODY_KB", "256")),
        model_path=os.getenv("MODEL_PATH", "model/artefacts/sentiment.joblib"),
        db_path=os.getenv("DB_PATH", "data/supportsense.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        allow_admin=_as_bool(os.getenv("ALLOW_ADMIN", "true")),
        suggest_service_url=os.getenv(
            "SUGGEST_SERVICE_URL", "http://suggest:8001"
        ),
    )
