# PLAN TASK: 5 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: response suggestion endpoint
# DO: map missing tickets to 404 and pass X-Simulate-Delay through to the client.
from __future__ import annotations

from fastapi import APIRouter, Request

from app.clients.suggest_client import request_suggestion
from app.config import get_settings
from app.db import get_ticket
from app.errors import ApiError
from app.schemas import SuggestRequest

router = APIRouter()
settings = get_settings()


@router.post("/v1/suggest-response")
def suggest_response(request: Request, body: SuggestRequest):
    db_path = getattr(request.app.state, "db_path", settings.db_path)
    ticket = get_ticket(db_path, body.ticket_id)
    if not ticket:
        raise ApiError(404, "TICKET_NOT_FOUND", f"ticket not found: {body.ticket_id}", "ticket_id")
    delay = int(request.headers.get("X-Simulate-Delay", "0") or 0)
    suggestion = request_suggestion(ticket, request.state.request_id, delay)
    return {"request_id": request.state.request_id, **suggestion}
