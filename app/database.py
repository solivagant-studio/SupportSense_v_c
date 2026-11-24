# PLAN TASK: 4 | STUDENT TASK PACK: Day 10 | EVIDENCE: TD-03
# WHERE: compatibility imports for the documented app/db.py module
# DO: keep this module as a thin re-export; schema and query behaviour live in app/db.py.
from app.db import (  # noqa: F401
    Base,
    Feedback,
    Ticket,
    create_feedback,
    create_ticket,
    get_ticket,
    initialise_database,
    list_tickets,
    make_engine,
    next_ticket_id,
    reset_database,
    ticket_count,
)

__all__ = [
    "Base",
    "Feedback",
    "Ticket",
    "create_feedback",
    "create_ticket",
    "get_ticket",
    "initialise_database",
    "list_tickets",
    "make_engine",
    "next_ticket_id",
    "reset_database",
    "ticket_count",
]
