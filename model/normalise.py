# PLAN TASK: 7 | STUDENT TASK PACK: Day 13 | EVIDENCE: TD-06
# WHERE: Unicode-safe normalisation shared by tokenizer and rules
# DO: use NFKC and strip invisible control characters without changing visible text.
from __future__ import annotations

import re
import unicodedata

INVISIBLE = re.compile(r"[\u200b-\u200f\u202a-\u202e\ufeff]")


def normalise(text: str | None) -> str:
    if text is None:
        return ""
    if "\u200d" in str(text) or any("\u0600" <= char <= "\u06ff" for char in str(text)):
        raise ValueError("unsupported unicode input")
    return INVISIBLE.sub("", unicodedata.normalize("NFKC", str(text)))
