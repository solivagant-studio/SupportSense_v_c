# PLAN TASK: 2 | STUDENT TASK PACK: Day 9 | EVIDENCE: TD-02
# WHERE: deterministic scoring rules, negation scope, and threshold labels
# DO: compare unrounded scores to thresholds; round only displayed confidence in the predictor.
from __future__ import annotations

NEGATION_WINDOW = 3

PHRASE_RULES = {
    ("no", "refund"): -0.70,
    ("never", "arrived"): -0.75,
    ("not", "bad"): 0.65,
    ("not", "unhappy"): 0.60,
    ("never", "disappointing"): 0.55,
}


def _negators(artefact: dict) -> set[str]:
    return {token.replace(" ", "_") for token in artefact["negators"] if token != "cannot"}


def _find_negator(tokens: list[str], index: int, negators: set[str]) -> str | None:
    for previous in tokens[max(0, index - NEGATION_WINDOW) : index]:
        if previous in negators:
            return previous
    return None


def score_sentiment(tokens: list[str], artefact: dict) -> tuple[float, list[str]]:
    weights = artefact["weights"]
    for phrase, score in PHRASE_RULES.items():
        if all(token in tokens for token in phrase):
            return score, list(phrase)

    negators = _negators(artefact)
    scores = []
    matched: list[str] = []
    for index, token in enumerate(tokens):
        weight = weights.get(token, 0.0)
        if weight == 0.0:
            continue
        negator = _find_negator(tokens, index, negators)
        if negator:
            weight = -weight * 0.8
            matched.append(negator)
        matched.append(token)
        scores.append(weight)
    return (sum(scores) / len(scores) if scores else 0.0), matched


def sentiment_score(tokens: list[str], artefact: dict) -> tuple[float, list[str]]:
    return score_sentiment(tokens, artefact)


def assign_priority(tokens: list[str], sentiment: float, artefact: dict) -> tuple[float, list[str]]:
    weights = artefact["priority_weights"]
    matched = [token for token in tokens if token in weights]
    keyword = min(1.0, sum(weights[token] for token in matched))
    return max(keyword, abs(sentiment) * 0.1), matched


def priority_score(tokens: list[str], sentiment: float, artefact: dict) -> tuple[float, list[str]]:
    return assign_priority(tokens, sentiment, artefact)


def sentiment_label(score: float, thresholds: dict) -> str:
    if score >= thresholds["positive"]:
        return "positive"
    if score <= thresholds["negative"]:
        return "negative"
    return "neutral"


def priority_label(score: float, thresholds: dict) -> str:
    if score >= thresholds["critical"]:
        return "critical"
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["medium"]:
        return "medium"
    return "low"


def confidence_for(score: float) -> float:
    return round(min(0.99, 0.5 + abs(score) / 2), 3)
