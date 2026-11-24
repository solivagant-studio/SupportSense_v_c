# PLAN TASK: 5 | STUDENT TASK PACK: Day 11 | EVIDENCE: TD-04
# WHERE: request validation schemas
# DO: keep validation messages field-specific so error envelopes identify the invalid input.
from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from app.config import get_settings

LOCALE_RE = re.compile(r"^[a-z]{2,3}(-[A-Z][A-Za-z0-9]{1,8})*$")


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    channel: str
    customer_tier: str
    locale: str = "en-ZA"

    @field_validator("text")
    @classmethod
    def trimmed_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must contain between 1 and 4000 characters")
        return value

    @field_validator("channel")
    @classmethod
    def valid_channel(cls, value: str) -> str:
        if value not in {"email", "chat", "phone", "social"}:
            raise ValueError("channel must be email, chat, phone or social")
        return value

    @field_validator("customer_tier")
    @classmethod
    def valid_tier(cls, value: str) -> str:
        if value not in {"standard", "premium", "enterprise"}:
            raise ValueError("customer_tier must be standard, premium or enterprise")
        return value

    @field_validator("locale")
    @classmethod
    def valid_locale(cls, value: str) -> str:
        if not LOCALE_RE.match(value):
            raise ValueError("locale must be an IETF language tag")
        return value


class BatchRequest(BaseModel):
    tickets: list[ClassifyRequest]

    @field_validator("tickets")
    @classmethod
    def within_batch_limit(cls, value: list[ClassifyRequest]) -> list[ClassifyRequest]:
        if len(value) > get_settings().max_batch:
            raise ValueError("tickets exceeds MAX_BATCH")
        return value


class SuggestRequest(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=64)


class FeedbackRequest(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=64)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
