# PLAN TASK: 3 | STUDENT TASK PACK: Day 9 | EVIDENCE: TD-02
# WHERE: stable public classifier imports used by routes and tests
# DO: delegate scoring to model/rules.py so rule behaviour surface through this API.
from __future__ import annotations

from model.predictor import Classification, Classifier, get_classifier, predict

__all__ = [
    "Classification",
    "Classifier",
    "classify",
    "get_classifier",
    "priority_score",
    "sentiment_score",
]


def classify(text: str, classifier: Classifier) -> Classification:
    return predict(text, classifier)


def sentiment_score(text: str, classifier: Classifier) -> tuple[float, list[str]]:
    return classifier.sentiment(text)


def priority_score(text: str, sentiment: float, classifier: Classifier) -> tuple[float, list[str]]:
    return classifier.priority(text, sentiment)
