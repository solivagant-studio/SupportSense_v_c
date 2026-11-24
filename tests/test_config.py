# PLAN TASK: 1 | STUDENT TASK PACK: Day 1 | EVIDENCE: ONB-01
# WHERE: app/config.py and tests/test_config.py
# DO: use these assertions to confirm the runtime settings before starting the stack.
import importlib

import pytest


ENV_NAMES = (
    "VARIANT",
    "PORT",
    "MAX_BATCH",
    "LATENCY_MS",
    "MAX_BODY_KB",
    "MODEL_PATH",
    "DB_PATH",
    "LOG_LEVEL",
    "ALLOW_ADMIN",
    "SUGGEST_SERVICE_URL",
)


def _clear_env(monkeypatch):
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_settings_expose_documented_defaults(monkeypatch):
    _clear_env(monkeypatch)
    config = importlib.import_module("app.config")

    settings = config.Settings()

    assert settings.variant == "A"
    assert settings.port == 8000
    assert settings.max_batch == 1
    assert settings.latency_ms == 0
    assert settings.max_body_kb == 256
    assert settings.model_path == "model/artefacts/sentiment.joblib"
    assert settings.db_path == "data/supportsense.db"
    assert settings.log_level == "INFO"
    assert settings.allow_admin is True
    assert settings.suggest_service_url == "http://suggest:8001"


def test_settings_read_environment_overrides(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("VARIANT", "b")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("MAX_BODY_KB", "512")
    monkeypatch.setenv("ALLOW_ADMIN", "false")
    config = importlib.import_module("app.config")

    settings = config.get_settings()

    assert settings.variant == "B"
    assert settings.port == 9000
    assert settings.max_body_kb == 512
    assert settings.allow_admin is False


def test_settings_reject_unknown_variant(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("VARIANT", "D")
    config = importlib.import_module("app.config")

    with pytest.raises(ValueError):
        config.get_settings()
