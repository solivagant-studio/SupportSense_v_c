# PLAN TASK: 6 | STUDENT TASK PACK: Day 12 | EVIDENCE: TD-05
# WHERE: local template-service HTTP API
# DO: select from five deterministic templates and honour X-Simulate-Delay for timeout tests.
from __future__ import annotations

import time

from fastapi import FastAPI, Header
from pydantic import BaseModel

app = FastAPI(title="SupportSense Suggest", version="1.0.0")

TEMPLATES = {
    ("negative", "high"): ("Thank you for reporting this. Our team is investigating urgently.", "neg-high-01"),
    ("negative", "low"): ("Sorry for the inconvenience. Please share a little more detail.", "neg-low-01"),
    ("neutral", "high"): ("Thanks for flagging this. We are checking it now.", "neu-high-01"),
    ("neutral", "low"): ("Thanks for getting in touch. How can we help?", "neu-low-01"),
    ("positive", "low"): ("Thank you for the kind feedback — we appreciate it!", "pos-low-01"),
}


class TemplateRequest(BaseModel):
    sentiment: str
    priority: str
    request_id: str = ""


@app.get("/v1/health")
def health():
    return {"status": "ok", "templates": len(TEMPLATES)}


@app.post("/v1/templates")
def template(
    body: TemplateRequest,
    x_simulate_delay: str | None = Header(default=None, alias="X-Simulate-Delay"),
):
    delay = int(x_simulate_delay or 0)
    if delay > 0:
        time.sleep(delay / 1000)

    band = "high" if body.priority in {"high", "critical"} else "low"
    suggestion, template_id = TEMPLATES.get(
        (body.sentiment, band),
        TEMPLATES[("positive", "low")],
    )
    return {
        "request_id": body.request_id,
        "suggestion": suggestion,
        "template_id": template_id,
    }
