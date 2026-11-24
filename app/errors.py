# PLAN TASK: 5 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: shared API error envelope
# DO: preserve the documented code/status pairs; every error response carries the active request_id.
from __future__ import annotations

from app.logging import get_logger
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, field: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.field = field


def error_payload(request: Request, status_code: int, code: str, message: str, field: str | None = None):
    error = {"code": code, "message": message}
    if field is not None:
        error["field"] = field
    return {
        "request_id": getattr(request.state, "request_id", ""),
        "error": error,
    }


async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(request, exc.status_code, exc.code, exc.message, exc.field),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    location = first.get("loc", [])
    field = str(location[-1]) if location else "body"
    return JSONResponse(
        status_code=422,
        content=error_payload(request, 422, "VALIDATION_ERROR", "request validation failed", field),
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException):
    code = "INTERNAL_ERROR" if exc.status_code == 404 else "VALIDATION_ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(request, exc.status_code, code, str(exc.detail)),
    )


async def internal_error_handler(request: Request, exc: Exception):
    get_logger().error(
        "request.failed",
        extra={
            "event": "request.failed",
            "request_id": getattr(request.state, "request_id", ""),
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content=error_payload(request, 500, "INTERNAL_ERROR", "unexpected server error"),
    )
