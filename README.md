# PLAN TASK: 1 | STUDENT TASK PACK: Day 1 | EVIDENCE: ONB-01
# WHERE: repository entry point for students
# DO: follow this file first, then complete the Student Task Pack.

# SupportSense

SupportSense is a deterministic customer-support triage service used for the WM-02 workplace simulation. It classifies ticket sentiment and priority, suggests a response, stores results, and shows recent tickets in a read-only dashboard.

## Quick start

```bash
git clone https://github.com/solivagant-studio/SupportSense_v_c supportsense
cd supportsense
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
curl -s localhost:8000/v1/health
curl -s -X POST localhost:8000/v1/admin/reset
```

API: `http://localhost:8000`  
Dashboard: `http://localhost:8501`  
Template service: internal only on port `8001`

The dashboard is read-only: it shows API health, stored ticket count and the 50 most recent classifications. See [docs/product-spec.md](docs/product-spec.md) for the student-facing behaviour contract.

## Local Python setup

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -v
```

## Test controls

- Reset the database with `POST /v1/admin/reset` before formal runs.
- Send `X-Simulate-Delay: 6000` to a suggestion request to simulate a slow dependency.
- Send `X-Request-Id: <id>` to make log assertions repeatable.

## Evidence folders

Create your portfolio outside this repository using the structure in the Templates & Evidence Checklist. Reference artefacts from your log by ID, for example `TC-014`, `DEF-002`, `EXE-02`.
