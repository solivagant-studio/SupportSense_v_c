# PLAN TASK: 5 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: admin reset test hook
# DO: return 204 when enabled and 403 when ALLOW_ADMIN is false.
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.config import get_settings
from app.db import reset_database
from app.errors import ApiError

router = APIRouter()
settings = get_settings()


@router.post("/v1/admin/reset", status_code=204)
def admin_reset(request: Request):
    if not getattr(request.app.state, "allow_admin", False):
        raise ApiError(403, "VALIDATION_ERROR", "admin reset is disabled", None)
    db_path = getattr(request.app.state, "db_path", settings.db_path)
    reset_database(db_path)
    return Response(status_code=204)
