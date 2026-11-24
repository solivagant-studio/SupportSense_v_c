# PLAN TASK: 5 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: feedback capture endpoint
# DO: return 201 on success and 404 when the referenced ticket does not exist.
from __future__ import annotations

from fastapi import APIRouter, Request

from app.config import get_settings
from app.db import create_feedback
from app.errors import ApiError
from app.schemas import FeedbackRequest

router = APIRouter()
settings = get_settings()


@router.post("/v1/feedback", status_code=201)
def feedback(request: Request, body: FeedbackRequest):
    db_path = getattr(request.app.state, "db_path", settings.db_path)
    try:
        return create_feedback(db_path, body.ticket_id, body.rating, body.comment)
    except LookupError:
        raise ApiError(404, "TICKET_NOT_FOUND", f"ticket not found: {body.ticket_id}", "ticket_id")
