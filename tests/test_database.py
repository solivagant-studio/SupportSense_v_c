# PLAN TASK: 4 | STUDENT TASK PACK: Day 10 | EVIDENCE: TD-03
# WHERE: app/database.py and SQLite bootstrap/reset logic
# DO: reset and seeding must be deterministic; never depend on insertion order beyond ticket_id values.
from __future__ import annotations

from app.database import create_ticket, get_ticket, initialise_database, list_tickets, reset_database, ticket_count


def test_initialise_database_seeds_only_once(tmp_path):
    db_path = tmp_path / "tickets.db"

    initialise_database(db_path)
    initialise_database(db_path)

    assert ticket_count(db_path) == 200


def test_reset_database_seeds_expected_rows(tmp_path):
    db_path = tmp_path / "tickets.db"

    reset_database(db_path)

    assert ticket_count(db_path) == 200
    assert get_ticket(db_path, "TCK-2026-000145") is not None
    assert get_ticket(db_path, "TCK-2026-000078") is not None


def test_create_ticket_persists_classification_and_suggestion(tmp_path):
    db_path = tmp_path / "tickets.db"
    initialise_database(db_path)

    created = create_ticket(
        db_path,
        payload={
            "ticket_id": "TCK-TEST-001",
            "text": "not good",
            "channel": "chat",
            "customer_tier": "standard",
            "locale": "en-ZA",
        },
        classification={
            "sentiment": "negative",
            "priority": "low",
            "confidence": 0.634,
            "matched_terms": ["not", "good"],
        },
        suggestion_text="Please tell us more.",
        request_id="REQ-001",
    )

    stored = get_ticket(db_path, "TCK-TEST-001")

    assert created["ticket_id"] == stored["ticket_id"]
    assert stored["sentiment"] == "negative"
    assert stored["priority"] == "low"
    assert stored["confidence"] == 0.634
    assert stored["matched_terms"] == ["not", "good"]
    assert stored["suggestion_text"] == "Please tell us more."
    assert stored["request_id"] == "REQ-001"


def test_list_tickets_filters_and_limits(tmp_path):
    db_path = tmp_path / "tickets.db"
    reset_database(db_path)

    recent = list_tickets(db_path, limit=5)
    negative = list_tickets(db_path, limit=1000, sentiment="negative")
    critical = list_tickets(db_path, limit=1000, priority="critical")

    assert len(recent) == 5
    assert len(negative) == 80
    assert len(critical) == 20
    assert all(row["sentiment"] == "negative" for row in negative)
    assert all(row["priority"] == "critical" for row in critical)
    assert [row["id"] for row in recent] == sorted((row["id"] for row in recent), reverse=True)


def test_reset_clears_user_created_tickets(tmp_path):
    db_path = tmp_path / "tickets.db"
    initialise_database(db_path)
    create_ticket(
        db_path,
        payload={
            "ticket_id": "TCK-TEST-999",
            "text": "urgent",
            "channel": "email",
            "customer_tier": "premium",
            "locale": "en-ZA",
        },
        classification={"sentiment": "neutral", "priority": "high", "confidence": 0.6, "matched_terms": ["urgent"]},
        suggestion_text=None,
        request_id=None,
    )

    reset_database(db_path)

    assert get_ticket(db_path, "TCK-TEST-999") is None
    assert ticket_count(db_path) == 200
