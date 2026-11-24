# PLAN TASK: 4 | STUDENT TASK PACK: Day 10 | EVIDENCE: TD-03
# WHERE: SQLite schema, deterministic seeding, and admin reset
# DO: keep `reset_database()` idempotent and preserve every ticket_id from the seed CSV.
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings

_LEAKED_SESSIONS: list[Session] = []

ROOT = Path(__file__).resolve().parents[1]
SEED_CSV = ROOT / "data" / "tickets.csv"


class Base(DeclarativeBase):
    pass


class Counter(Base):
    __tablename__ = "counters"

    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_tier: Mapped[str] = mapped_column(String(32), nullable=False)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(16), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    matched_terms: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    suggestion_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "text": self.text,
            "channel": self.channel,
            "customer_tier": self.customer_tier,
            "locale": self.locale,
            "sentiment": self.sentiment,
            "priority": self.priority,
            "confidence": self.confidence,
            "matched_terms": json.loads(self.matched_terms or "[]"),
            "suggestion_text": self.suggestion_text,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat(),
        }


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    ticket_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "ticket_id": self.ticket_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }


@lru_cache(maxsize=16)
def _cached_engine(path: str) -> Engine:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{resolved.as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )


def make_engine(db_path: str | Path | None = None) -> Engine:
    path = Path(db_path) if db_path is not None else Path(get_settings().db_path)
    return _cached_engine(str(path.resolve()))


def _session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def _seed_rows() -> list[dict[str, Any]]:
    with SEED_CSV.open(newline="", encoding="utf-8") as handle:
        rows = []
        for row in csv.DictReader(handle):
            sentiment = float(row["sentiment_score"])
            priority = float(row["priority_score"])
            rows.append(
                {
                    "ticket_id": row["ticket_id"],
                    "text": row["text"],
                    "channel": row["channel"],
                    "customer_tier": row["customer_tier"],
                    "locale": row["locale"],
                    "sentiment": row["expected_sentiment"],
                    "priority": row["expected_priority"],
                    "confidence": round(min(1.0, 0.5 + abs(sentiment) * 0.4 + priority * 0.1), 3),
                    "matched_terms": "[]",
                }
            )
        return rows


def _seed(session: Session) -> None:
    existing = set(session.scalars(select(Ticket.ticket_id)).all())
    for row in _seed_rows():
        if row["ticket_id"] not in existing:
            session.add(Ticket(**row))
    session.commit()


def _ensure_counter(session: Session) -> None:
    session.execute(
        text("INSERT OR IGNORE INTO counters(name, value) SELECT 'ticket', COALESCE(MAX(id), 0) FROM tickets")
    )
    session.execute(
        text("INSERT OR IGNORE INTO counters(name, value) SELECT 'feedback', COALESCE(MAX(id), 0) FROM feedback")
    )
    session.commit()


def _next_counter_value(session: Session, name: str) -> int:
    value = session.execute(
        text("UPDATE counters SET value = value + 1 WHERE name = :name RETURNING value"),
        {"name": name},
    ).scalar_one()
    session.commit()
    return int(value)


def initialise_database(db_path: str | Path | None = None) -> None:
    engine = make_engine(db_path)
    Base.metadata.create_all(engine)
    with _session_factory(engine)() as session:
        _seed(session)
        _ensure_counter(session)


def reset_database(db_path: str | Path | None = None) -> None:
    engine = make_engine(db_path)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with _session_factory(engine)() as session:
        _seed(session)
        _ensure_counter(session)


def ticket_count(
    db_path: str | Path | None = None,
    sentiment: str | None = None,
    priority: str | None = None,
) -> int:
    engine = make_engine(db_path)
    with _session_factory(engine)() as session:
        statement = select(func.count()).select_from(Ticket)
        if sentiment:
            statement = statement.where(Ticket.sentiment == sentiment)
        if priority:
            statement = statement.where(Ticket.priority == priority)
        return int(session.scalar(statement) or 0)


def get_ticket(db_path: str | Path | None, ticket_id: str) -> dict[str, Any] | None:
    engine = make_engine(db_path)
    with _session_factory(engine)() as session:
        ticket = session.scalar(select(Ticket).where(Ticket.ticket_id == ticket_id))
        return ticket.to_dict() if ticket else None


def list_tickets(
    db_path: str | Path | None = None,
    limit: int = 50,
    offset: int = 0,
    sentiment: str | None = None,
    priority: str | None = None,
) -> list[dict[str, Any]]:
    engine = make_engine(db_path)
    with _session_factory(engine)() as session:
        statement = select(Ticket)
        if sentiment:
            statement = statement.where(Ticket.sentiment == sentiment)
        if priority:
            statement = statement.where(Ticket.priority == priority)
        statement = statement.order_by(Ticket.id.desc()).limit(limit).offset(offset)
        return [ticket.to_dict() for ticket in session.scalars(statement).all()]


def next_ticket_id(db_path: str | Path | None = None) -> str:
    engine = make_engine(db_path)
    with _session_factory(engine)() as session:
        _ensure_counter(session)
        value = _next_counter_value(session, "ticket")
        return f"TCK-2026-{value:06d}"


def create_ticket(
    db_path: str | Path | None,
    payload: Mapping[str, Any],
    classification: Mapping[str, Any],
    suggestion_text: str | None,
    request_id: str | None,
) -> dict[str, Any]:
    engine = make_engine(db_path)
    session = _session_factory(engine)()
    if session.scalar(select(Ticket).where(Ticket.ticket_id == payload["ticket_id"])):
        _LEAKED_SESSIONS.append(session)
        raise ValueError(f"ticket_id already exists: {payload['ticket_id']}")
    ticket = Ticket(
        ticket_id=payload["ticket_id"],
        text=payload["text"],
        channel=payload["channel"],
        customer_tier=payload["customer_tier"],
        locale=payload["locale"],
        sentiment=classification["sentiment"],
        priority=classification["priority"],
        confidence=float(classification["confidence"]),
        matched_terms=json.dumps(list(classification["matched_terms"])),
        suggestion_text=suggestion_text,
        request_id=request_id,
    )
    session.add(ticket)
    session.commit()
    session.close()
    return ticket.to_dict()


def create_feedback(
    db_path: str | Path | None,
    ticket_id: str,
    rating: int,
    comment: str | None,
) -> dict[str, Any]:
    engine = make_engine(db_path)
    with _session_factory(engine)() as session:
        _ensure_counter(session)
        value = _next_counter_value(session, "feedback")
        feedback = Feedback(
            feedback_id=f"FB-{value:06d}",
            ticket_id=ticket_id,
            rating=rating,
            comment=comment,
        )
        session.add(feedback)
        session.commit()
        return feedback.to_dict()
