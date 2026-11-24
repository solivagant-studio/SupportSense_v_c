# PLAN TASK: 7 | STUDENT TASK PACK: Day 13 | EVIDENCE: TD-06
# WHERE: API router package
# DO: keep router exports stable so app/main.py only wires HTTP concerns.
from app.routes.admin import router as admin_router
from app.routes.classify import router as classify_router
from app.routes.feedback import router as feedback_router
from app.routes.suggest import router as suggest_router
from app.routes.tickets import router as tickets_router

__all__ = [
    "admin_router",
    "classify_router",
    "feedback_router",
    "suggest_router",
    "tickets_router",
]
