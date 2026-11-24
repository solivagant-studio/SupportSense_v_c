# PLAN TASK: 3 | STUDENT TASK PACK: Day 9 | EVIDENCE: TD-02
# WHERE: model loading and prediction entry point
# DO: load the 40 MB artefact once via get_classifier(); never call joblib.load() inside predict().
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path

import joblib

from model import rules
from model.text import preprocess

DEFAULT_ARTEFACT = Path(__file__).resolve().parent / "artefacts" / "sentiment.joblib"


@dataclass(frozen=True)
class Classification:
    sentiment: str
    priority: str
    confidence: float
    matched_terms: tuple[str, ...]


class Classifier:
    def __init__(self, artefact: dict):
        self.artefact = artefact
        self.thresholds = artefact["thresholds"]

    def _scores(self, text: str):
        tokens = preprocess(text)
        sentiment, sentiment_terms = rules.score_sentiment(tokens, self.artefact)
        priority, priority_terms = rules.assign_priority(tokens, sentiment, self.artefact)
        return sentiment, sentiment_terms, priority, priority_terms

    def sentiment(self, text: str) -> tuple[float, list[str]]:
        score, terms = rules.score_sentiment(preprocess(text), self.artefact)
        return round(score, 3), terms

    def priority(self, text: str, sentiment: float) -> tuple[float, list[str]]:
        score, terms = rules.assign_priority(preprocess(text), sentiment, self.artefact)
        return round(score, 3), terms

    def classify(self, text: str) -> Classification:
        return self.predict(text)

    def predict(self, text: str) -> Classification:
        sentiment, sentiment_terms, priority, priority_terms = self._scores(text)
        matched = tuple(dict.fromkeys([*sentiment_terms, *priority_terms]))
        return Classification(
            sentiment=rules.sentiment_label(
                float(Decimal(str(sentiment)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                self.thresholds,
            ),
            priority=rules.priority_label(priority, self.thresholds),
            confidence=rules.confidence_for(sentiment),
            matched_terms=matched,
        )


@lru_cache(maxsize=4)
def get_classifier(path: str | Path | None = None) -> Classifier:
    artefact_path = Path(path) if path is not None else DEFAULT_ARTEFACT
    return Classifier(joblib.load(artefact_path))


def predict(text: str, classifier: Classifier) -> Classification:
    return classifier.predict(text)
