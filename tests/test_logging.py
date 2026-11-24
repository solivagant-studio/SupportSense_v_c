# PLAN TASK: 7 | STUDENT TASK PACK: Day 13 | EVIDENCE: TD-06
# WHERE: correlation IDs, JSON event lines, and PII redaction
# DO: assert one structured line per event and that failures log at ERROR with the active request_id.
from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient

from app.logging import JsonFormatter, configure_logging, get_logger, redact
from app.main import create_app


@pytest.fixture()
def log_stream():
    stream = io.StringIO()
    configure_logging("INFO", stream=stream)
    yield stream


@pytest.fixture()
def client(tmp_path, log_stream):
    application = create_app()
    application.state.db_path = tmp_path / "logging.db"
    application.state.allow_admin = True
    with TestClient(application, raise_server_exceptions=False) as test_client:
        assert test_client.post("/v1/admin/reset").status_code == 204
        log_stream.seek(0)
        log_stream.truncate(0)
        yield test_client


def _logs(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]


def _payload(text="Please help"):
    return {
        "text": text,
        "channel": "email",
        "customer_tier": "standard",
        "locale": "en-ZA",
    }


def test_configure_logging_installs_one_json_handler(log_stream):
    logger = get_logger()
    json_handlers = [h for h in logger.handlers if isinstance(h.formatter, JsonFormatter)]
    assert len(json_handlers) == 1

    logger.info("event", extra={"request_id": "abc12345"})

    lines = _logs(log_stream)
    assert len(lines) == 1
    assert lines[0]["level"] == "INFO"
    assert lines[0]["request_id"] == "abc12345"
    assert "." in lines[0]["timestamp"]
    assert lines[0]["timestamp"].endswith("Z")


def test_request_completion_logs_one_line_with_request_id(client, log_stream):
    response = client.post("/v1/classify", json=_payload(), headers={"X-Request-Id": "req-111"})

    assert response.status_code == 200
    lines = _logs(log_stream)
    request_lines = [line for line in lines if line["event"] == "request.completed"]
    assert len(request_lines) == 1
    assert request_lines[0]["request_id"] == "req-111"
    assert request_lines[0]["method"] == "POST"
    assert request_lines[0]["path"] == "/v1/classify"
    assert request_lines[0]["status_code"] == 200
    assert request_lines[0]["duration_ms"] >= 0


def test_generated_request_id_is_returned(client):
    response = client.post("/v1/classify", json=_payload())

    assert response.status_code == 200
    assert response.json()["request_id"] == response.headers["X-Request-Id"]


def test_failure_logs_exactly_one_error_with_request_id_and_stack(client, log_stream):
    @client.app.get("/__boom")
    def boom():
        raise RuntimeError("forced failure")

    response = client.get("/__boom", headers={"X-Request-Id": "err-222"})

    assert response.status_code == 500
    errors = [line for line in _logs(log_stream) if line["level"] == "ERROR"]
    assert len(errors) == 1
    assert errors[0]["request_id"] == "err-222"
    assert errors[0]["path"] == "/__boom"
    assert errors[0]["error_type"] == "RuntimeError"
    assert "Traceback" in errors[0]["stack"]


def test_request_logs_never_include_submitted_pii(client, log_stream):
    text = "Contact jane.doe@example.com or +27 82 123 4567 about this parcel"

    response = client.post("/v1/classify", json=_payload(text), headers={"X-Request-Id": "pii-333"})

    assert response.status_code == 200
    raw = log_stream.getvalue()
    assert "jane.doe@example.com" not in raw
    assert "+27 82 123 4567" not in raw
    assert "0821234567" not in raw
    request_lines = [line for line in _logs(log_stream) if line["event"] == "request.completed"]
    assert len(request_lines) == 1
    assert request_lines[0]["request_id"] == "pii-333"


def test_emitted_messages_are_redacted(log_stream):
    get_logger().info("submitting %s", "jane.doe@example.com or +27 82 123 4567")

    raw = log_stream.getvalue()
    assert "[EMAIL]" in raw
    assert "[PHONE]" in raw
    assert "jane.doe@example.com" not in raw
    assert "+27 82 123 4567" not in raw


def test_redact_handles_common_email_and_phone_shapes():
    result = redact("mail jane.doe@example.com or +27 82 123 4567 or 0821234567")

    assert result == "mail [EMAIL] or [PHONE] or [PHONE]"
