# PLAN TASK: 1 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: text cleaning and preprocessing used by the classifier
# DO: fail loudly on null/empty input here; the API schema must catch these cases first with a 422 envelope.
from __future__ import annotations

from model.tokenizer import normalise, tokenize


def clean_text(text: str | None) -> str:
    if text is None:
        return ""
    return normalise(text).strip()


def preprocess(text: str | None) -> list[str]:
    return tokenize(clean_text(text))
