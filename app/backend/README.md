# CampusPulse backend

This directory contains the anonymous observation API. It uses FastAPI and SQLite, so no external database service is required.

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
- `GET /api/v1/observations/metadata` — retrieve controlled categories and locations for UI dropdowns

The retrieval endpoint supports `location`, `category`, `start_date`, and `end_date` query parameters. Dates must be ISO 8601 timestamps. Results are newest first.

## Data model

Each observation contains the following fields:

| Field | Required | Description |
| --- | --- | --- |
| `id` | response only | Database identifier |
| `created_at` | response only | Time the observation was submitted |
| `location` | yes | Controlled approximate campus area |
| `category` | yes | One of the eight controlled environmental categories |
| `severity` | yes | Impact severity from 1 to 5 |
| `description` | yes | Short environmental observation, up to 2,000 characters |
| `observed_at` | no | Time when the environmental condition was observed |
| `approximate_location_id` | no | Non-personal identifier for an approximate area or zone |
| `crowd_level` | no | Crowd level from 1 to 5 |
| `environmental_rating` | no | Overall environmental rating from 1 to 5 |

Categories are: `Wi-Fi / Connectivity`, `Crowding`, `Cleanliness`, `Noise`, `Maintenance`, `Safety`, `Facilities`, and `Other`.

Locations are configurable through the comma-separated `CAMPUSPULSE_LOCATIONS` environment variable. If it is not set, the backend uses its documented safe defaults. The metadata endpoint is the source of truth for clients.

The API intentionally does not collect student names, student IDs, phone numbers, email addresses, exact personal locations, medical information, authentication data, or other personal-identification fields.

## Tests

From `app/backend`:

```bash
PYTHONPATH=. pytest
```
