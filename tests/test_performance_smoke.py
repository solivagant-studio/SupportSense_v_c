# PLAN TASK: 9 | STUDENT TASK PACK: Day 15 | EVIDENCE: TD-08
# WHERE: bounded clean-baseline latency and stable reset behaviour
# DO: use the isolated API fixture so timing checks never touch the developer database.
from __future__ import annotations

import math
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.db import create_feedback, create_ticket, initialise_database, make_engine, next_ticket_id

PAYLOAD = {
    "text": "My parcel never arrived and support ignored me",
    "channel": "email",
    "customer_tier": "standard",
    "locale": "en-ZA",
}


def test_classify_latency_smoke_stays_bounded(api_client):
    durations = []

    for _ in range(5):
        started = time.perf_counter()
        response = api_client.post("/v1/classify", json=PAYLOAD)
        durations.append(time.perf_counter() - started)
        assert response.status_code == 200

    index = max(0, math.ceil(0.95 * len(durations)) - 1)
    assert sorted(durations)[index] < 1.0


def test_make_engine_reuses_engine_for_same_path(tmp_path):
    db_path = tmp_path / "shared.db"

    assert make_engine(db_path) is make_engine(db_path)


def test_next_ticket_id_is_unique_under_concurrency(tmp_path):
    db_path = tmp_path / "concurrent.db"
    initialise_database(db_path)

    with ThreadPoolExecutor(max_workers=10) as executor:
        ticket_ids = list(executor.map(lambda _: next_ticket_id(db_path), range(20)))

    assert len(set(ticket_ids)) == 20


def test_create_feedback_is_unique_under_concurrency(tmp_path):
    db_path = tmp_path / "feedback.db"
    initialise_database(db_path)

    with ThreadPoolExecutor(max_workers=10) as executor:
        feedback = list(
            executor.map(
                lambda _: create_feedback(db_path, "TCK-2026-000145", 5, None),
                range(20),
            )
        )

    assert len({row["feedback_id"] for row in feedback}) == 20


def test_database_error_paths_release_connections(tmp_path):
    db_path = tmp_path / "pool.db"
    initialise_database(db_path)
    payload = {
        "ticket_id": "TCK-2026-000201",
        "text": "duplicate test",
        "channel": "email",
        "customer_tier": "standard",
        "locale": "en-ZA",
    }
    classification = {
        "sentiment": "neutral",
        "priority": "low",
        "confidence": 0.5,
        "matched_terms": [],
    }
    create_ticket(db_path, payload, classification, None, None)

    for _ in range(6):
        with pytest.raises(ValueError):
            create_ticket(db_path, payload, classification, None, None)

    assert make_engine(db_path).pool.checkedout() == 0


def test_reset_restores_stable_ticket_ids(api_client):
    before = api_client.get("/v1/tickets?limit=5").json()
    api_client.post("/v1/classify", json=PAYLOAD)
    api_client.post("/v1/admin/reset")
    after = api_client.get("/v1/tickets?limit=5").json()

    assert after["total"] == 200
    assert [row["ticket_id"] for row in after["items"]] == [
        row["ticket_id"] for row in before["items"]
    ]
