# PLAN TASK: 8 | STUDENT TASK PACK: Day 14 | EVIDENCE: TD-07
# WHERE: dashboard API contract and student-facing product spec
# DO: verify the read-only view model before wiring Streamlit widgets.
from __future__ import annotations

from pathlib import Path

from dashboard.app import build_view_model

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_dashboard_builds_view_model_from_health_and_tickets():
    calls = []
    health = {"status": "ok", "variant": "A", "tickets": 200, "dependencies": {"suggest": "configured"}}
    tickets = {
        "items": [
            {
                "ticket_id": "TCK-2026-000200",
                "text": "Excellent service",
                "sentiment": "positive",
                "priority": "low",
                "confidence": 0.9,
                "created_at": "2026-11-24T10:00:00",
            }
        ],
        "total": 200,
        "limit": 50,
        "offset": 0,
    }

    def fake_fetch(url, timeout=5):
        calls.append(url)
        return FakeResponse(health if url.endswith("/v1/health") else tickets)

    model = build_view_model("http://api:8000", fetch=fake_fetch)

    assert model["status"] == "ok"
    assert model["variant"] == "A"
    assert model["total"] == 200
    assert model["items"] == tickets["items"]
    assert calls == [
        "http://api:8000/v1/health",
        "http://api:8000/v1/tickets?limit=50&offset=0",
    ]


def test_dashboard_reports_unavailable_api_without_raising():
    def unavailable(url, timeout=5):
        raise OSError("API down")

    model = build_view_model("http://api:8000", fetch=unavailable)

    assert model["status"] == "unavailable"
    assert model["items"] == []
    assert model["total"] == 0


def test_product_spec_covers_all_student_stories_without_facilitator_language():
    text = (ROOT / "docs" / "product-spec.md").read_text(encoding="utf-8")

    for number in range(1, 11):
        assert f"US-{number:02d}" in text
    lowered = text.lower()
    assert "answer key" not in lowered
    assert "root cause" not in lowered
    assert "defect" not in lowered
