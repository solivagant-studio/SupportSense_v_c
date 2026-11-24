# PLAN TASK: 6 | STUDENT TASK PACK: Day 12 | EVIDENCE: TD-05
# WHERE: bounded HTTP client for the local template service
# DO: keep exactly three attempts with (2s connect, 5s read) timeouts; translate failures to 504/502 envelopes.
from __future__ import annotations

import time
from typing import Any, Mapping

import httpx

from app.config import get_settings
from app.errors import ApiError

MAX_ATTEMPTS = 3
TIMEOUT = httpx.Timeout(5.0, connect=2.0)


def request_suggestion(ticket: Mapping[str, Any], request_id: str, delay_ms: int = 0) -> dict[str, str]:
    settings = get_settings()
    url = f"{settings.suggest_service_url}/v1/templates"
    payload = {
        "sentiment": ticket["sentiment"],
        "priority": ticket["priority"],
        "request_id": request_id,
    }
    headers = {
        "X-Request-Id": request_id,
        "X-Simulate-Delay": str(delay_ms),
    }

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            if attempt == MAX_ATTEMPTS - 1:
                raise ApiError(504, "DEPENDENCY_TIMEOUT", "suggest service timed out", None)
            time.sleep(0.1 * (attempt + 1))
        except httpx.HTTPStatusError:
            raise ApiError(502, "DEPENDENCY_ERROR", "suggest service returned an error", None)
        except httpx.RequestError:
            raise ApiError(502, "DEPENDENCY_ERROR", "suggest service is unavailable", None)

    raise ApiError(504, "DEPENDENCY_TIMEOUT", "suggest service timed out", None)
