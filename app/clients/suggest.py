# PLAN TASK: 6 | STUDENT TASK PACK: Day 12 | EVIDENCE: TD-05
# WHERE: backwards-compatible import path for the template client
# DO: import the real implementation from `app.clients.suggest_client`.
from app.clients.suggest_client import request_suggestion

__all__ = ["request_suggestion"]
