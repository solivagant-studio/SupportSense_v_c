# PLAN TASK: 6 | STUDENT TASK PACK: Day 12 | EVIDENCE: TD-05
# WHERE: Unicode-aware tokenizer and normalisation entry point
# DO: keep underscores inside tokens and let Unicode letters through; emoji are ignored by the regex.
from __future__ import annotations

import re

from model.normalise import normalise as _normalise

TOKEN_RE = re.compile(r"[^\W]+", re.UNICODE)


def normalise(text: str | None) -> str:
    return _normalise(text)


def tokenize(text: str | None) -> list[str]:
    return TOKEN_RE.findall(normalise(text).lower())
