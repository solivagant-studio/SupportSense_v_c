# PLAN TASK: 9 | STUDENT TASK PACK: Day 15 | EVIDENCE: TD-08
# WHERE: student guidance headers across production modules
# DO: audit the shipped source tree only; test code is not part of the student guidance contract.
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("app", "model", "dashboard", "suggest")
HEADER_RE = re.compile(
    r"^# PLAN TASK: \d+ \| STUDENT TASK PACK: Day \d+ \| EVIDENCE: [A-Z]+-\d+$"
)
BANNED = ("answer key", "root cause", "defect")
VARIANT_ID_RE = re.compile(r"\b[ABC][1-8]\b")


def _source_files():
    for directory in SOURCE_DIRS:
        yield from sorted((ROOT / directory).rglob("*.py"))


def test_production_files_have_student_guidance_header():
    missing = []
    for path in _source_files():
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        if not HEADER_RE.match(first_line):
            missing.append(str(path.relative_to(ROOT)))

    assert missing == []


def test_guidance_headers_do_not_reveal_variant_answers():
    offenders = []
    for path in _source_files():
        header = "\n".join(
            line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("#")
        )
        lowered = header.lower()
        if any(term in lowered for term in BANNED) or VARIANT_ID_RE.search(header):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
