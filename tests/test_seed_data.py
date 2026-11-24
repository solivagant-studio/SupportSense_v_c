# PLAN TASK: 2 | STUDENT TASK PACK: Day 8 | EVIDENCE: TD-01
# WHERE: data/tickets.csv and model/artefacts/sentiment.joblib
# DO: use these rows as the calibrated test-data pack; record provenance and do not edit seeds to make tests pass.
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import joblib


ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "data" / "tickets.csv"
ARTEFACT = ROOT / "model" / "artefacts" / "sentiment.joblib"


def _rows():
    with TICKETS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _by_row_id(rows, row_id):
    return next(row for row in rows if row["row_id"] == row_id)


def test_seed_contains_two_hundred_stable_rows():
    rows = _rows()

    assert len(rows) == 200
    assert len({row["ticket_id"] for row in rows}) == 200
    assert all(row["ticket_id"].startswith("TCK-2026-") for row in rows)


def test_seed_distributions_match_build_spec():
    rows = _rows()

    assert Counter(row["expected_sentiment"] for row in rows) == {
        "negative": 80,
        "neutral": 60,
        "positive": 60,
    }
    assert Counter(row["expected_priority"] for row in rows) == {
        "critical": 20,
        "high": 50,
        "medium": 70,
        "low": 60,
    }
    assert Counter(row["channel"] for row in rows) == {
        "email": 90,
        "chat": 40,
        "phone": 40,
        "social": 30,
    }


def test_sentiment_calibration_rows_have_exact_scores():
    rows = _rows()

    assert float(_by_row_id(rows, "S-144")["sentiment_score"]) == 0.144
    assert float(_by_row_id(rows, "S-145")["sentiment_score"]) == 0.145
    assert float(_by_row_id(rows, "S-150")["sentiment_score"]) == 0.150
    assert _by_row_id(rows, "S-144")["expected_sentiment"] == "neutral"
    assert _by_row_id(rows, "S-145")["expected_sentiment"] == "neutral"
    assert _by_row_id(rows, "S-150")["expected_sentiment"] == "positive"


def test_priority_boundary_rows_have_exact_scores():
    rows = _rows()

    expected = {
        "P-078": (0.78, "high"),
        "P-079": (0.79, "high"),
        "P-080": (0.80, "critical"),
        "P-081": (0.81, "critical"),
    }
    for row_id, (score, priority) in expected.items():
        row = _by_row_id(rows, row_id)
        assert float(row["priority_score"]) == score
        assert row["expected_priority"] == priority


def test_model_artefact_is_deterministic_and_loaded():
    assert ARTEFACT.exists()
    assert ARTEFACT.stat().st_size > 35 * 1024 * 1024

    artefact = joblib.load(ARTEFACT)

    assert artefact["version"] == "1.0.0"
    assert artefact["weights"]["good"] == 0.8
    assert artefact["priority_weights"]["p080"] == 0.80
    assert artefact["thresholds"]["positive"] == 0.15
