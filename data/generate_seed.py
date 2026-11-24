# PLAN TASK: 2 | STUDENT TASK PACK: Day 8 | EVIDENCE: TD-01
# WHERE: deterministic ticket seed generator
# DO: run `python data/generate_seed.py` from the repository root to rebuild the CSV; never hand-edit calibrated rows.
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEXICON = ROOT / "data" / "lexicon.csv"
OUTPUT = ROOT / "data" / "tickets.csv"

FIELDS = [
    "row_id",
    "ticket_id",
    "text",
    "channel",
    "customer_tier",
    "locale",
    "expected_sentiment",
    "expected_priority",
    "sentiment_score",
    "priority_score",
]

SENTIMENT_TOKENS = {
    "negative": ["terrible", "awful", "late", "broken", "ignored", "bad", "disappointing", "unhappy"],
    "neutral": [""],
    "positive": ["good", "great", "excellent", "fine", "okay", "recommend"],
}
PRIORITY_TOKENS = {
    "critical": ["site_down", "security_breach", "data_loss", "cannot_login"],
    "high": ["refund", "charged_twice", "cancelled_order", "urgent"],
    "medium": ["delivery_delay", "wrong_item", "account_update"],
    "low": ["question", "feature_request", "feedback"],
}
SENTIMENT_OVERRIDES = {143: ("calib144", 0.144), 144: ("calib145", 0.145), 149: ("calib150", 0.150)}
PRIORITY_OVERRIDES = {77: ("p078", 0.78), 78: ("p079", 0.79), 79: ("p080", 0.80), 80: ("p081", 0.81)}
SPECIAL_ROW_IDS = {77: "P-078", 78: "P-079", 79: "P-080", 80: "P-081", 143: "S-144", 144: "S-145", 149: "S-150"}


def _load_weights():
    sentiment = {}
    priority = {}
    with LEXICON.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["kind"] == "sentiment":
                sentiment[row["token"]] = float(row["weight"])
            elif row["kind"] == "priority":
                priority[row["token"]] = float(row["weight"])
    return sentiment, priority


def _spread(desired, order):
    queues = {label: [label] * count for label, count in desired.items()}
    result = []
    while any(queues.values()):
        for label in order:
            if queues[label]:
                result.append(queues[label].pop(0))
    return result


def _rebalance(values, desired, protected):
    counts = Counter(values)
    surplus = {label: counts[label] - desired[label] for label in desired}
    deficit = {label: desired[label] - counts[label] for label in desired}

    for index in range(len(values)):
        if index in protected or not any(deficit.values()):
            continue
        donor = values[index]
        if surplus.get(donor, 0) <= 0:
            continue
        recipient = next(label for label, gap in deficit.items() if gap > 0)
        values[index] = recipient
        surplus[donor] -= 1
        deficit[recipient] -= 1

    return values


def _tokens(text):
    return re.findall(r"[a-z0-9_]+", text.lower())


def _sentiment_score(text, weights):
    scored = [weights[token] for token in _tokens(text) if token in weights and weights[token] != 0]
    return round(sum(scored) / len(scored), 3) if scored else 0.0


def _priority_score(text, weights, sentiment):
    matched = [weights[token] for token in _tokens(text) if token in weights]
    keyword = min(1.0, sum(matched)) if matched else 0.0
    return round(max(keyword, abs(sentiment) * 0.1), 3)


def _sentiment_label(score):
    if score <= -0.15:
        return "negative"
    if score >= 0.15:
        return "positive"
    return "neutral"


def _priority_label(score):
    if score >= 0.80:
        return "critical"
    if score >= 0.55:
        return "high"
    if score >= 0.30:
        return "medium"
    return "low"


def _row_id(index):
    return SPECIAL_ROW_IDS.get(index, f"R-{index + 1:03d}")


def generate_rows():
    sentiment_weights, priority_weights = _load_weights()

    sentiments = _spread(
        {"negative": 80, "neutral": 60, "positive": 60},
        ["negative", "neutral", "positive"],
    )
    priorities = _spread(
        {"critical": 20, "high": 50, "medium": 70, "low": 60},
        ["critical", "high", "medium", "low"],
    )
    channels = _spread(
        {"email": 90, "chat": 40, "phone": 40, "social": 30},
        ["email", "chat", "phone", "social"],
    )
    tiers = _spread(
        {"enterprise": 40, "premium": 60, "standard": 100},
        ["enterprise", "premium", "standard"],
    )

    for index, (token, _) in SENTIMENT_OVERRIDES.items():
        sentiments[index] = _sentiment_label(token and sentiment_weights[token])
    sentiments = _rebalance(
        sentiments,
        {"negative": 80, "neutral": 60, "positive": 60},
        set(SENTIMENT_OVERRIDES),
    )

    for index, (token, _) in PRIORITY_OVERRIDES.items():
        priorities[index] = _priority_label(priority_weights[token])
    priorities = _rebalance(
        priorities,
        {"critical": 20, "high": 50, "medium": 70, "low": 60},
        set(PRIORITY_OVERRIDES),
    )

    rows = []
    for index in range(200):
        if index in SENTIMENT_OVERRIDES:
            sentiment_token, expected_sentiment_score = SENTIMENT_OVERRIDES[index]
        else:
            options = SENTIMENT_TOKENS[sentiments[index]]
            sentiment_token = options[index % len(options)]
            expected_sentiment_score = None

        if index in PRIORITY_OVERRIDES:
            priority_token, expected_priority_score = PRIORITY_OVERRIDES[index]
        else:
            options = PRIORITY_TOKENS[priorities[index]]
            priority_token = options[index % len(options)]
            expected_priority_score = None

        text = f"{sentiment_token} {priority_token}".strip()
        sentiment_score = (
            expected_sentiment_score
            if expected_sentiment_score is not None
            else _sentiment_score(text, sentiment_weights)
        )
        priority_score = (
            expected_priority_score
            if expected_priority_score is not None
            else _priority_score(text, priority_weights, sentiment_score)
        )

        expected_sentiment = (
            _sentiment_label(sentiment_score)
            if expected_sentiment_score is not None
            else sentiments[index]
        )
        expected_priority = (
            _priority_label(priority_score)
            if expected_priority_score is not None
            else priorities[index]
        )

        rows.append(
            {
                "row_id": _row_id(index),
                "ticket_id": f"TCK-2026-{index + 1:06d}",
                "text": text,
                "channel": channels[index],
                "customer_tier": tiers[index],
                "locale": "en-ZA",
                "expected_sentiment": expected_sentiment,
                "expected_priority": expected_priority,
                "sentiment_score": f"{sentiment_score:.3f}",
                "priority_score": f"{priority_score:.3f}",
            }
        )

    return rows


def write_tickets_csv():
    rows = generate_rows()
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    write_tickets_csv()
