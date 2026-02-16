# Frontend

Static dashboard for running incident scenarios plus a Vercel serverless fallback endpoint.

## Local run

```bash
python -m http.server 8081
# open http://localhost:8081
```

When running locally, UI defaults to `http://localhost:8000/incidents/run`.

## Vercel deployment notes

This project includes `api/incidents/run.js`, which proxies requests to the backend.

Set one of these env vars in Vercel project settings:

- `INCIDENT_BACKEND_URL` (preferred)
- `AGENTS_API_URL`
- `BACKEND_URL`

The proxy forwards `POST /api/incidents/run` to `${INCIDENT_BACKEND_URL}/incidents/run`.
