# PLAN TASK: 6 | STUDENT TASK PACK: Day 12 | EVIDENCE: TD-05
# WHERE: suggest/main.py and app/clients/suggest_client.py
# DO: prove template mapping, delay simulation, bounded retries, and 504/502 error translation.
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients import suggest_client
from app.errors import ApiError
from suggest.main import app as suggest_app


def _ticket():
    return {"ticket_id": "TCK-2026-000001", "sentiment": "negative", "priority": "critical"}


@pytest.fixture()
def service():
    with TestClient(suggest_app) as client:
        yield client


def test_template_service_maps_sentiment_and_priority(service):
    high = service.post(
        "/v1/templates",
        json={"sentiment": "negative", "priority": "critical", "request_id": "REQ-1"},
    )
    low = service.post(
        "/v1/templates",
        json={"sentiment": "neutral", "priority": "low", "request_id": "REQ-2"},
    )

    assert high.status_code == 200
    assert high.json()["template_id"] == "neg-high-01"
    assert low.json()["template_id"] == "neu-low-01"


def test_template_service_honours_simulated_delay(service, monkeypatch):
    slept = []
    monkeypatch.setattr("suggest.main.time.sleep", slept.append)

    response = service.post(
        "/v1/templates",
        json={"sentiment": "positive", "priority": "low", "request_id": "REQ-3"},
        headers={"X-Simulate-Delay": "25"},
    )

    assert response.status_code == 200
    assert slept == [0.025]


def test_client_success_returns_template(monkeypatch):
    captured = {}
    response = httpx.Response(
        200,
        json={"suggestion": "Thank you for reporting this.", "template_id": "neg-high-01"},
        request=httpx.Request("POST", "http://suggest:8001/v1/templates"),
    )

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return response

    monkeypatch.setattr(suggest_client.httpx, "post", fake_post)

    result = suggest_client.request_suggestion(_ticket(), "REQ-1")

    assert result["template_id"] == "neg-high-01"
    assert captured["headers"]["X-Request-Id"] == "REQ-1"
    assert captured["json"]["priority"] == "critical"
    assert captured["timeout"].connect == 2.0
    assert captured["timeout"].read == 5.0


def test_concurrent_suggest_requests_do_not_serialize(api_client, monkeypatch):
    def slow_post(url, **kwargs):
        time.sleep(0.2)
        return httpx.Response(
            200,
            json={"suggestion": "Thank you.", "template_id": "neg-high-01"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(suggest_client.httpx, "post", slow_post)

    def post_once(_):
        return api_client.post(
            "/v1/suggest-response",
            json={"ticket_id": "TCK-2026-000001"},
            headers={"X-Simulate-Delay": "200"},
        )

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=6) as executor:
        responses = list(executor.map(post_once, range(6)))
    elapsed = time.perf_counter() - started

    assert all(response.status_code == 200 for response in responses)
    assert elapsed < 1.0


def test_client_maps_timeout_to_504_after_bounded_retries(monkeypatch):
    calls = []
    request = httpx.Request("POST", "http://suggest:8001/v1/templates")

    def fake_post(url, **kwargs):
        calls.append(kwargs)
        raise httpx.TimeoutException("timed out", request=request)

    monkeypatch.setattr(suggest_client.httpx, "post", fake_post)
    monkeypatch.setattr(suggest_client.time, "sleep", lambda _: None)

    with pytest.raises(ApiError) as raised:
        suggest_client.request_suggestion(_ticket(), "REQ-1", delay_ms=6000)

    assert raised.value.status_code == 504
    assert raised.value.code == "DEPENDENCY_TIMEOUT"
    assert len(calls) == 3


def test_client_maps_dependency_http_error_to_502(monkeypatch):
    response = httpx.Response(
        500,
        json={"detail": "boom"},
        request=httpx.Request("POST", "http://suggest:8001/v1/templates"),
    )
    monkeypatch.setattr(suggest_client.httpx, "post", lambda url, **kwargs: response)

    with pytest.raises(ApiError) as raised:
        suggest_client.request_suggestion(_ticket(), "REQ-1")

    assert raised.value.status_code == 502
    assert raised.value.code == "DEPENDENCY_ERROR"
