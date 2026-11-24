# PLAN TASK: 3 | STUDENT TASK PACK: Day 9 | EVIDENCE: TD-02
# WHERE: model/classifier.py
# DO: keep scoring deterministic and explain any confidence value using the loaded artefact thresholds.
from __future__ import annotations

from pathlib import Path

import joblib
import pytest

from model import predictor
from model.classifier import classify, get_classifier, priority_score, sentiment_score


ROOT = Path(__file__).resolve().parents[1]
ARTEFACT = ROOT / "model" / "artefacts" / "sentiment.joblib"


@pytest.fixture(scope="module")
def model():
    return get_classifier(ARTEFACT)


def test_sentiment_scores_match_calibration_rows(model):
    assert sentiment_score("calib144", model)[0] == 0.144
    assert sentiment_score("calib145", model)[0] == 0.145
    assert sentiment_score("calib150", model)[0] == 0.150


def test_sentiment_handles_negation_and_matched_terms(model):
    score, terms = sentiment_score("not good", model)

    assert score < 0
    assert terms == ["not", "good"]
    assert sentiment_score("good", model)[0] > 0


def test_empty_text_is_neutral_without_matches(model):
    assert sentiment_score("", model) == (0.0, [])
    assert sentiment_score("unrelated words", model) == (0.0, [])


def test_priority_scores_and_boundaries(model):
    assert priority_score("p078", 0.0, model) == (0.78, ["p078"])
    assert priority_score("p080", 0.0, model)[0] == 0.80
    assert priority_score("question", 0.0, model)[0] == 0.05
    assert priority_score("question", 0.9, model)[0] == 0.09


def test_model_loaded_once_for_repeated_predictions(monkeypatch):
    calls = []
    real_load = joblib.load

    def counting_load(path):
        calls.append(Path(path))
        return real_load(path)

    predictor.get_classifier.cache_clear()
    monkeypatch.setattr(predictor.joblib, "load", counting_load)
    try:
        classifier = predictor.get_classifier(ARTEFACT)
        for _ in range(3):
            predictor.predict("good", classifier)
    finally:
        predictor.get_classifier.cache_clear()

    assert len(calls) == 1


def test_emoji_and_cjk_inputs_return_valid_label(model):
    result = classify("Great service 😊 很好", model)

    assert result.sentiment in {"negative", "neutral", "positive"}


def test_accented_inputs_classify_positively(model):
    assert classify("très bien, merci", model).sentiment == "positive"


def test_zwj_and_rtl_inputs_return_valid_label(model):
    result = classify("Family 👨‍👩‍👧‍👦 مرحبا, good", model)

    assert result.sentiment in {"negative", "neutral", "positive"}


def test_double_negation_is_non_negative(model):
    assert classify("The delivery was not bad at all", model).sentiment != "negative"


def test_multi_token_negation_is_negative(model):
    assert classify("I cannot recommend this product", model).sentiment == "negative"


def test_boundary_labels_use_inclusive_critical_threshold(model):
    assert classify("p080", model).priority == "critical"


def test_priority_boundary_079_stays_high(model):
    assert classify("p079", model).priority == "high"


def test_calibration_labels_use_unrounded_scores(model):
    assert classify("calib144", model).sentiment == "neutral"
    assert classify("calib145", model).sentiment == "neutral"
    assert classify("calib150", model).sentiment == "positive"


def test_classify_is_deterministic_and_exposes_contract_fields(model):
    first = classify("terrible site_down", model)
    second = classify("terrible site_down", model)

    assert first == second
    assert first.sentiment == "negative"
    assert first.priority == "critical"
    assert 0.0 <= first.confidence <= 1.0
    assert "terrible" in first.matched_terms
    assert "site_down" in first.matched_terms
