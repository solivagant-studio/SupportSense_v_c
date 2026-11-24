# PLAN TASK: 5 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: ticket list and detail endpoints
# DO: return the documented pagination envelope and preserve stable newest-first ordering.
from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.config import get_settings
from app.db import get_ticket, list_tickets, ticket_count
from app.errors import ApiError

router = APIRouter()
settings = get_settings()


@router.get("/v1/tickets")
def tickets(
    request: Request,
    limit: int = Query(default=5000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    sentiment: str | None = None,
    priority: str | None = None,
):
    db_path = getattr(request.app.state, "db_path", settings.db_path)
    items = list_tickets(
        db_path,
        limit=limit,
        offset=offset,
        sentiment=sentiment,
        priority=priority,
    )
    return {
        "items": items,
        "total": ticket_count(db_path, sentiment=sentiment, priority=priority),
        "limit": limit,
        "offset": offset,
    }


@router.get("/v1/tickets/{ticket_id}")
def ticket_detail(request: Request, ticket_id: str):
    db_path = getattr(request.app.state, "db_path", settings.db_path)
    ticket = get_ticket(db_path, ticket_id)
    if not ticket:
        raise ApiError(404, "TICKET_NOT_FOUND", f"ticket not found: {ticket_id}", "ticket_id")
    return ticket
