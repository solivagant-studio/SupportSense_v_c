# PLAN TASK: 2 | STUDENT TASK PACK: Day 8 | EVIDENCE: TD-01
# WHERE: model/artefacts/sentiment.joblib
# DO: run `python model/build_artefact.py` after changing the lexicon; keep the artefact deterministic and offline-loadable.
from __future__ import annotations

import csv
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[1]
LEXICON = ROOT / "data" / "lexicon.csv"
OUTPUT = ROOT / "model" / "artefacts" / "sentiment.joblib"
PADDING_BYTES = 40 * 1024 * 1024


def build_artefact():
    weights = {}
    negators = set()
    priority_weights = {}

    with LEXICON.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            token = row["token"]
            weight = float(row["weight"])
            if row["kind"] == "sentiment":
                weights[token] = weight
            if row["negator"] == "true":
                negators.add(token)
            if row["kind"] == "priority":
                priority_weights[token] = weight

    seed = b"supportsense"
    padding = (seed * ((PADDING_BYTES // len(seed)) + 1))[:PADDING_BYTES]

    artefact = {
        "version": "1.0.0",
        "weights": weights,
        "negators": sorted(negators),
        "priority_weights": priority_weights,
        "thresholds": {
            "negative": -0.15,
            "positive": 0.15,
            "critical": 0.80,
            "high": 0.55,
            "medium": 0.30,
        },
        "padding": padding,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefact, OUTPUT)


if __name__ == "__main__":
    build_artefact()
