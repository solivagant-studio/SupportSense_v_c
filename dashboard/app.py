# PLAN TASK: 8 | STUDENT TASK PACK: Day 14 | EVIDENCE: TD-07
# WHERE: read-only Streamlit view of recent tickets and predictions
# DO: keep the dashboard observation-only; all changes go through the API test hook.
from __future__ import annotations

import os
from typing import Any, Callable

import httpx
import streamlit as st

DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
Fetch = Callable[[str], Any]


def _fetch_json(url: str, timeout: int = 5):
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def build_view_model(api_base: str = DEFAULT_API_BASE, fetch: Fetch = _fetch_json) -> dict[str, Any]:
    base = api_base.rstrip("/")
    try:
        health = fetch(f"{base}/v1/health", 5).json()
        tickets = fetch(f"{base}/v1/tickets?limit=50&offset=0", 5).json()
    except Exception:
        return {"status": "unavailable", "variant": "-", "total": 0, "items": []}

    return {
        "status": health.get("status", "unknown"),
        "variant": health.get("variant", "-"),
        "total": int(tickets.get("total", 0)),
        "items": list(tickets.get("items", [])),
    }


def render() -> dict[str, Any]:
    st.set_page_config(page_title="SupportSense queue", layout="wide")
    model = build_view_model()

    st.title("Support queue")
    st.caption("Read-only view of recent classifications")

    if model["status"] != "ok":
        st.warning("The API is unavailable. Start the stack and refresh this page.")
        return model

    urgent = sum(1 for item in model["items"] if item.get("priority") in {"high", "critical"})
    positive = sum(1 for item in model["items"] if item.get("sentiment") == "positive")

    total_col, urgent_col, positive_col = st.columns(3)
    total_col.metric("Stored tickets", model["total"])
    urgent_col.metric("High or critical on page", urgent)
    positive_col.metric("Positive on page", positive)

    st.subheader("Recent tickets")
    st.dataframe(
        model["items"],
        column_order=["ticket_id", "created_at", "sentiment", "priority", "confidence", "channel"],
        hide_index=True,
        use_container_width=True,
    )
    return model


if __name__ == "__main__":
    render()
