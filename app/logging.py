# PLAN TASK: 7 | STUDENT TASK PACK: Day 13 | EVIDENCE: TD-06
# WHERE: JSON log formatter, single handler setup, and PII redaction
# DO: keep one handler, millisecond timestamps, and redaction on every emitted message.
from __future__ import annotations

import logging
import re
import sys
import traceback
from datetime import datetime, timezone
from typing import TextIO

LOGGER_NAME = "supportsense"

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?(?:\(\d{1,4}\)\s?)?\d{2,4}[\s]\d{2,4}[\s]\d{3,4}\b|\b\d{10,13}\b"
)

_EXTRA_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "error_type",
    "stack",
    "event",
    "body",
)


def redact(text: str | None) -> str:
    if not text:
        return ""
    return PHONE_RE.sub("[PHONE]", EMAIL_RE.sub("[EMAIL]", str(text)))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json

        payload = {
            "timestamp": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "event": redact(getattr(record, "event", record.getMessage())),
            "message": redact(record.getMessage()),
        }
        if record.exc_info:
            payload["stack"] = redact("".join(traceback.format_exception(*record.exc_info)))

        for field in _EXTRA_FIELDS:
            if field == "event" or not hasattr(record, field):
                continue
            value = getattr(record, field)
            payload[field] = redact(value) if isinstance(value, str) else value

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def configure_logging(level: str, stream: TextIO | None = None) -> None:
    logger = get_logger()
    handler = logging.StreamHandler(stream if stream is not None else sys.stdout)
    handler.setFormatter(JsonFormatter())
    for existing in list(logger.handlers):
        logger.removeHandler(existing)
    logger.addHandler(handler)
    logger.setLevel(level.upper())
    logger.propagate = False
