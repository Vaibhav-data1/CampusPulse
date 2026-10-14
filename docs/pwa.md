# CampusPulse PWA

The React frontend is a Vite-built Progressive Web App. It keeps the existing
observation form and live analytics dashboard, while adding an installable
application shell for supported browsers.

## Local development

From the repository root:

```powershell
cd app/frontend
npm install
npm run dev
```

Run the FastAPI backend separately on `http://127.0.0.1:8000`. During local
development, Vite proxies `/api` and `/health` to that backend. Leave
`VITE_API_BASE_URL` empty (the default) to use this proxy.

## Production build

```powershell
cd app/frontend
npm run build
npm run preview
```

The build creates `dist/manifest.webmanifest` and a generated Workbox service
worker. The service worker precaches the application shell and static assets.
Requests under `/api/` use a network-only strategy so observations and
analytics remain current and are never served from a stale PWA cache.

## API configuration

Copy `.env.example` to `.env.local` for local overrides. Set
`VITE_API_BASE_URL` to the origin of the deployed FastAPI service, without a
trailing slash:

```text
VITE_API_BASE_URL=https://api.example.edu
```

The frontend then requests, for example,
`https://api.example.edu/api/v1/analytics/summary`. The FastAPI deployment
must allow the frontend origin through CORS.

## Installing the app

Serve the production build over HTTPS (or use `localhost` during development).
Open the site in a supported Chromium-based browser:

- **Android / Chrome:** open the site, use the browser menu, then choose
  **Install app** or **Add to Home screen**.
- **Desktop / Chrome or Edge:** use the install icon in the address bar, or
  choose **Install CampusPulse** from the browser menu.
- **Other supported platforms:** use the browser's available install or
  add-to-home-screen action.

The manifest provides the CampusPulse name, standalone display mode, theme and
background colors, viewport behavior, and branded 192px/512px SVG icons.

## Limitations

The service worker provides an offline-capable shell, not offline submission or
offline analytics. API requests intentionally require the FastAPI backend and
network access so users do not see stale observations or dashboard results.
