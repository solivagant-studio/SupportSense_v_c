# PLAN TASK: 7 | STUDENT TASK PACK: Day 13 | EVIDENCE: TD-06
# WHERE: application factory, middleware wiring, and health route
# DO: attach one JSON handler, assign request IDs before guards, and keep error envelopes unchanged.
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.db import initialise_database, ticket_count
from app.errors import (
    ApiError,
    api_error_handler,
    http_error_handler,
    internal_error_handler,
    validation_error_handler,
)
from app.logging import configure_logging, get_logger
from app.middleware import RequestContextMiddleware
from app.routes import (
    admin_router,
    classify_router,
    feedback_router,
    suggest_router,
    tickets_router,
)

settings = get_settings()


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        initialise_database(application.state.db_path)
        yield

    application = FastAPI(title="SupportSense", version="1.0.0", lifespan=lifespan)
    application.state.db_path = settings.db_path
    application.state.allow_admin = settings.allow_admin

    if not get_logger().handlers:
        configure_logging(settings.log_level)

    application.add_exception_handler(ApiError, api_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(StarletteHTTPException, http_error_handler)
    application.add_exception_handler(Exception, internal_error_handler)

    @application.middleware("http")
    async def request_guards(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            raw_length = request.headers.get("content-length", "0")
            length = int(raw_length) if raw_length.isdigit() else 0
            if length > settings.max_body_kb * 100 * 1024:
                return JSONResponse(
                    status_code=413,
                    content={
                        "request_id": request.state.request_id,
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": "request body exceeds MAX_BODY_KB",
                        },
                    },
                )
            if length > 0 and not request.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse(
                    status_code=415,
                    content={
                        "request_id": request.state.request_id,
                        "error": {
                            "code": "UNSUPPORTED_MEDIA_TYPE",
                            "message": "Content-Type must be application/json",
                        },
                    },
                )
        return await call_next(request)

    application.include_router(classify_router)
    application.include_router(suggest_router)
    application.include_router(tickets_router)
    application.include_router(feedback_router)
    application.include_router(admin_router)

    @application.get("/v1/health")
    def health(request: Request):
        return {
            "status": "ok",
            "variant": settings.variant,
            "tickets": ticket_count(getattr(request.app.state, "db_path", settings.db_path)),
            "dependencies": {"suggest": "configured"},
        }

    application.add_middleware(RequestContextMiddleware)
    return application


app = create_app()
