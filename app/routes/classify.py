# PLAN TASK: 5 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: classification endpoints and persisted prediction envelope
# DO: keep request_id, ticket_id, confidence and matched_terms on every success response.
from __future__ import annotations

from fastapi import APIRouter, Request

from app.config import get_settings
from app.db import create_ticket, next_ticket_id
from app.errors import ApiError
from app.logging import get_logger
from app.schemas import BatchRequest, ClassifyRequest
from model.classifier import get_classifier

router = APIRouter()
settings = get_settings()


def _db_path(request: Request):
    return getattr(request.app.state, "db_path", settings.db_path)


def _classify_one(request: Request, body: ClassifyRequest):
    get_logger().info("classify request", extra={"body": body.model_dump()})
    classifier = get_classifier(settings.model_path)
    result = classifier.classify(body.text)
    ticket_id = next_ticket_id(_db_path(request))
    create_ticket(
        _db_path(request),
        payload={**body.model_dump(), "ticket_id": ticket_id},
        classification={
            "sentiment": result.sentiment,
            "priority": result.priority,
            "confidence": result.confidence,
            "matched_terms": list(result.matched_terms),
        },
        suggestion_text=None,
        request_id=request.state.request_id,
    )
    return {
        "request_id": request.state.request_id,
        "ticket_id": ticket_id,
        "sentiment": result.sentiment,
        "priority": result.priority,
        "confidence": result.confidence,
        "matched_terms": list(result.matched_terms),
        "model_version": classifier.artefact["version"],
    }


@router.post("/v1/classify")
def classify(request: Request, body: ClassifyRequest):
    return _classify_one(request, body)


@router.post("/v1/classify/batch")
def classify_batch(request: Request, body: BatchRequest):
    if len(body.tickets) > settings.max_batch:
        raise ApiError(422, "VALIDATION_ERROR", "tickets exceeds MAX_BATCH", "tickets")
    return [_classify_one(request, ticket) for ticket in body.tickets]
