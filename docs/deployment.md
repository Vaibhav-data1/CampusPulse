# CampusPulse deployment

## Recommended architecture

For a student PBL or demonstration deployment, use two services on Render:

1. **Web Service** — FastAPI backend from `app/backend`.
2. **Static Site** — React/Vite PWA from `app/frontend`.

This keeps the frontend and API independently deployable while preserving the
existing SQLite and analytics implementation. The repository includes a
`render.yaml` Blueprint with explicit repository-root-relative build and start
commands. Render is a
practical low-cost option for a public HTTPS demo because it provides managed
TLS and deploys directly from a Git repository.

## Deploy with the Blueprint

1. Push the repository to GitHub.
2. In Render, choose **New > Blueprint** and select the repository.
3. Review the two services in `render.yaml`.
4. Set `CAMPUSPULSE_CORS_ORIGINS` on `campuspulse-api` to the final frontend
   origin, for example `https://campuspulse-web.onrender.com`. Multiple origins
   may be comma-separated.
5. Set `VITE_API_BASE_URL` on `campuspulse-web` to the final backend origin,
   for example `https://campuspulse-api.onrender.com`, without a trailing slash.
6. Deploy the backend and frontend. If the frontend URL changes, update both
   `CAMPUSPULSE_CORS_ORIGINS` and the frontend build variable, then redeploy the
   static site.

The backend's local origins remain allowed, so local development continues to
work. Production origins are explicitly supplied through
`CAMPUSPULSE_CORS_ORIGINS`; the API does not use a wildcard origin.

## Required configuration

### Backend

| Variable | Required value |
|---|---|
| `CAMPUSPULSE_CORS_ORIGINS` | Comma-separated HTTPS frontend origins |
| `CAMPUSPULSE_DATABASE_PATH` | `/var/data/campuspulse.db` when a persistent disk is mounted |
| `PORT` | Supplied automatically by Render |

Render starts the API with:

```text
PYTHONPATH=app/backend python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The `/health` endpoint is used for service health checks.

### Frontend

| Variable | Required value |
|---|---|
| `VITE_API_BASE_URL` | HTTPS origin of the deployed FastAPI service |

The production build is:

```text
npm --prefix app/frontend ci && npm --prefix app/frontend run build
```

The frontend API client appends `/api/v1/...` to `VITE_API_BASE_URL`. For local
development, leave the variable empty so Vite's existing `/api` proxy targets
`http://127.0.0.1:8000`.

## SQLite persistence limitation

SQLite remains functional, but its durability depends on the host filesystem.
Render free web services use ephemeral storage: a redeploy, migration, or
instance replacement can remove the database. This is acceptable for a
temporary demonstration only; regenerate the synthetic dataset after such an
event with `python scripts/seed_demo_data.py`.

For a demo whose observations must survive restarts, attach a Render persistent
disk to the backend and keep `CAMPUSPULSE_DATABASE_PATH=/var/data/campuspulse.db`.
Persistent disks are not part of the free tier. For larger or multi-instance
production use, SQLite should eventually be replaced with a managed database,
but that is intentionally outside this deployment change.

The generated `render.yaml` is free-tier compatible and does not provision a
disk automatically. If durable SQLite storage is required, attach a Render
persistent disk manually to the backend, mount it at `/var/data`, and keep the
configured database path. Confirm the plan and disk availability in Render;
do not assume a free service includes persistent storage.

## Install the deployed PWA

Open the frontend's public HTTPS URL in a supported browser:

- Android Chrome: browser menu → **Install app** or **Add to Home screen**
- Chrome/Edge desktop: address-bar install icon or browser menu →
  **Install CampusPulse**

The deployed site must be HTTPS for service-worker installation outside local
development. API requests remain network-backed so current observations and
analytics are not served from a stale cache.

## Local production-like validation

```powershell
# Terminal 1: backend
$env:PYTHONPATH = "app/backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: frontend
cd app/frontend
$env:VITE_API_BASE_URL = ""
npm ci
npm run build
npm run preview -- --host 127.0.0.1
```

Then open `http://127.0.0.1:4173`. The preview serves the generated manifest
and service worker; the backend supplies the real observation and analytics
endpoints.
