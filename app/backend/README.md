# CampusPulse backend

This directory contains the initial anonymous observation API. It uses FastAPI and SQLite, so no external database service is required.

## Setup

From the repository root:

```bash
cd app/backend
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive documentation is available at `/docs`.

SQLite is stored at `app/backend/campuspulse.db` by default. Set `CAMPUSPULSE_DATABASE_PATH` to use another location.

## Endpoints

- `GET /health` — health check
- `POST /api/v1/observations` — submit an anonymous observation
- `GET /api/v1/observations` — retrieve observations

The retrieval endpoint supports `location`, `category`, `start_date`, and `end_date` query parameters. Dates must be ISO 8601 timestamps. Results are newest first.

Observation payloads contain only `location`, `category`, `severity` (1–5), and `description`; no names, student IDs, phone numbers, email addresses, or authentication data are collected.

## Tests

From `app/backend`:

```bash
PYTHONPATH=. pytest
```
