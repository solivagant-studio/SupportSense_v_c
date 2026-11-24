# PLAN TASK: 5 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: app/main.py and REST error envelopes
# DO: exercise the documented status codes and envelope fields before changing route logic.
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path):
    app.state.db_path = tmp_path / "api.db"
    app.state.allow_admin = True
    with TestClient(app) as test_client:
        assert test_client.post("/v1/admin/reset").status_code == 204
        yield test_client


def _ticket_payload(text="My parcel never arrived"):
    return {
        "text": text,
        "channel": "email",
        "customer_tier": "standard",
        "locale": "en-ZA",
    }


def test_health_returns_liveness_shape(client):
    response = client.get("/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["variant"] == "A"


def test_classify_returns_documented_envelope(client):
    response = client.post("/v1/classify", json=_ticket_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"]
    assert body["ticket_id"].startswith("TCK-2026-")
    assert body["sentiment"] in {"negative", "neutral", "positive"}
    assert body["priority"] in {"critical", "high", "medium", "low"}
    assert 0.0 <= body["confidence"] <= 1.0
    assert isinstance(body["matched_terms"], list)
    assert body["model_version"] == "1.0.0"


def test_classify_rejects_empty_text_with_validation_envelope(client):
    response = client.post("/v1/classify", json=_ticket_payload("   "))

    assert response.status_code == 422
    body = response.json()
    assert body["request_id"]
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["field"] == "text"


def test_classify_rejects_null_text(client):
    response = client.post("/v1/classify", json={**_ticket_payload(), "text": None})

    assert response.status_code == 422
    body = response.json()
    assert body["request_id"]
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["field"] == "text"


def test_classify_rejects_wrong_content_type(client):
    response = client.post(
        "/v1/classify",
        content='{"text":"hello"}',
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_classify_rejects_oversized_body(client):
    response = client.post("/v1/classify", json=_ticket_payload("x" * (300 * 1024)))

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_classify_batch_enforces_max_batch(client):
    response = client.post(
        "/v1/classify/batch",
        json={"tickets": [_ticket_payload(), _ticket_payload()]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "tickets"


def test_tickets_list_pagination_and_filtering(client):
    response = client.get("/v1/tickets?limit=50&offset=0&priority=high")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 50
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert len(body["items"]) == 50
    assert all(item["priority"] == "high" for item in body["items"])


def test_tickets_default_to_fifty_per_page(client):
    response = client.get("/v1/tickets")

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 50
    assert len(body["items"]) == 50


def test_ticket_detail_and_not_found_envelope(client):
    found = client.get("/v1/tickets/TCK-2026-000001")
    missing = client.get("/v1/tickets/NOPE-999")

    assert found.status_code == 200
    assert found.json()["ticket_id"] == "TCK-2026-000001"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "TICKET_NOT_FOUND"


def test_suggest_response_uses_template_client(client, monkeypatch):
    captured = {}

    def fake_suggestion(ticket, request_id, delay_ms=0):
        captured.update(ticket_id=ticket["ticket_id"], request_id=request_id, delay_ms=delay_ms)
        return {"suggestion": "Thank you for reporting this.", "template_id": "neg-high-01"}

    monkeypatch.setattr("app.routes.suggest.request_suggestion", fake_suggestion)

    response = client.post(
        "/v1/suggest-response",
        json={"ticket_id": "TCK-2026-000001"},
        headers={"X-Simulate-Delay": "6000"},
    )

    assert response.status_code == 200
    assert response.json()["template_id"] == "neg-high-01"
    assert captured["ticket_id"] == "TCK-2026-000001"
    assert captured["delay_ms"] == 6000


def test_feedback_validation_and_missing_ticket(client):
    invalid = client.post("/v1/feedback", json={"ticket_id": "TCK-2026-000001", "rating": 9})
    missing = client.post("/v1/feedback", json={"ticket_id": "NOPE-999", "rating": 5})
    valid = client.post(
        "/v1/feedback",
        json={"ticket_id": "TCK-2026-000001", "rating": 5, "comment": "helpful"},
    )

    assert invalid.status_code == 422
    assert invalid.json()["error"]["field"] == "rating"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "TICKET_NOT_FOUND"
    assert valid.status_code == 201
    assert valid.json()["rating"] == 5


def test_admin_reset_can_be_disabled(client):
    app.state.allow_admin = False

    response = client.post("/v1/admin/reset")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_route_returns_json_error_envelope(client):
    response = client.get("/v1/unknown")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
