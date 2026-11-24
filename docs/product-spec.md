# SupportSense product specification

SupportSense is a customer-support triage service for the WM-02 workplace simulation. It accepts free-text tickets, returns a deterministic sentiment and priority prediction, stores the result, and shows recent tickets in a read-only dashboard.

The service is intentionally small. It runs locally with Docker Compose and needs no external accounts or network services.

## Users and scope

- Support analyst: submits tickets and checks predictions.
- Team lead: inspects the recent queue and confirms that results are consistent.
- Test engineer: uses documented headers and the reset hook to repeat scenarios.

The system does not send email, escalate tickets, or modify customer records.

## User stories and acceptance criteria

### US-01 — Start the service
As a support analyst, I can start the whole stack locally.

**Acceptance criteria**
- `docker compose -f docker/docker-compose.yml up --build` starts the API on port 8000 and the dashboard on port 8501.
- `GET /v1/health` returns HTTP 200 with `status`, `variant`, `tickets` and `dependencies`.
- The template service is internal and is not exposed on the host.

### US-02 — Classify a ticket
As a support analyst, I can submit one ticket and receive a prediction.

**Acceptance criteria**
- `POST /v1/classify` with `text`, `channel`, `customer_tier` and `locale` returns HTTP 200.
- The response includes `request_id`, `ticket_id`, `sentiment`, `priority`, `confidence`, `matched_terms` and `model_version`.
- `sentiment` is one of `positive`, `neutral` or `negative`.
- `priority` is one of `critical`, `high`, `medium` or `low`.
- The same payload returns the same prediction on repeated runs.

### US-03 — Understand the prediction
As a team lead, I can see why a prediction was made.

**Acceptance criteria**
- `matched_terms` lists the words or phrases that influenced the score.
- `confidence` is a number between 0 and 1.
- The response contains no prediction state that is not present in the persisted ticket.

### US-04 — Validate input
As a test engineer, I can rely on clear validation responses.

**Acceptance criteria**
- Empty `text`, invalid `channel`, invalid `customer_tier` or invalid `locale` returns HTTP 422.
- The error envelope contains `request_id` and `error.code` set to `VALIDATION_ERROR`.
- The `error.field` value identifies the invalid input where applicable.

### US-05 — Classify a small batch
As a support analyst, I can submit up to the configured batch limit.

**Acceptance criteria**
- `POST /v1/classify/batch` accepts one ticket by default.
- A batch larger than the configured limit returns HTTP 422 with `error.field` set to `tickets`.
- Each accepted item follows the same response contract as a single classification.

### US-06 — Suggest a response
As a support analyst, I can request a suggested reply for a stored ticket.

**Acceptance criteria**
- `POST /v1/suggest-response` with a known `ticket_id` returns `request_id`, `suggestion` and `template_id`.
- An unknown `ticket_id` returns HTTP 404 with `error.code` set to `TICKET_NOT_FOUND`.
- `X-Simulate-Delay: <milliseconds>` makes the upstream call slower for test scenarios.
- A slow or failed upstream call returns a documented 504 or 502 envelope rather than a success response.

### US-07 — Browse stored tickets
As a team lead, I can inspect recent tickets and filter the queue.

**Acceptance criteria**
- `GET /v1/tickets` returns `items`, `total`, `limit` and `offset`.
- The default limit is 50.
- `priority` and `sentiment` filters can be combined with `limit` and `offset`.
- `GET /v1/tickets/{ticket_id}` returns one stored ticket or a 404 envelope.

### US-08 — Record feedback
As a support analyst, I can rate a suggestion.

**Acceptance criteria**
- `POST /v1/feedback` with a rating from 1 to 5 returns HTTP 201.
- Feedback references a stored `ticket_id`.
- An unknown ticket returns HTTP 404 with `error.code` set to `TICKET_NOT_FOUND`.

### US-09 — Reset test data
As a test engineer, I can restore a known starting state.

**Acceptance criteria**
- `POST /v1/admin/reset` restores 200 seed tickets when `ALLOW_ADMIN=true`.
- Seed ticket IDs are stable after reset.
- When `ALLOW_ADMIN=false`, the endpoint returns HTTP 403 with a standard error envelope.

### US-10 — Inspect evidence
As a test engineer, I can correlate requests with structured logs.

**Acceptance criteria**
- Every response carries a `request_id`.
- `X-Request-Id: <id>` overrides the generated correlation value.
- Each request produces one JSON completion line containing `request_id`, `method`, `path`, `status_code` and `duration_ms`.
- Failures produce an ERROR-level JSON line containing `request_id`, `path`, `error_type` and a stack trace.
- Logs do not contain email addresses or phone numbers from submitted text.

## Dashboard behaviour

The dashboard is read-only. It shows the API health state, stored ticket count, a small count summary and the 50 most recent tickets. It does not submit tickets or change stored data.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `VARIANT` | `A` | Simulation variant label |
| `PORT` | `8000` | API host port |
| `MAX_BATCH` | `1` | Maximum tickets per batch |
| `LATENCY_MS` | `0` | Simulated classifier delay |
| `MAX_BODY_KB` | `256` | Maximum request body size |
| `MODEL_PATH` | `model/artefacts/sentiment.joblib` | Artefact location |
| `DB_PATH` | `data/supportsense.db` | SQLite file |
| `LOG_LEVEL` | `INFO` | Minimum log level |
| `ALLOW_ADMIN` | `true` | Enables the reset hook |
| `SUGGEST_SERVICE_URL` | `http://suggest:8001` | Template service URL |
| `API_BASE_URL` | `http://localhost:8000` | Dashboard API location |
