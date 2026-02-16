# Agents Backend

FastAPI backend for Incident Commander with Elasticsearch + Agent Builder integration.

## Run

```bash
uv sync --dev
uv run uvicorn app.main:app --reload --port 8000
```

## Test

```bash
uv run pytest
```

## Environment variables

- `ELASTIC_CLOUD_ID` (preferred) or `ELASTIC_URL`
- `ELASTIC_API_KEY`
- `ELASTIC_INCIDENTS_INDEX` (default: `incidents-logs`)
- `AGENT_BUILDER_BASE_URL`
- `AGENT_BUILDER_API_KEY`
- `AGENT_BUILDER_ROUTE` (default: `/api/incident/execute`)
- `REQUEST_TIMEOUT_SECONDS` (default: `10`)

## Runtime behavior for `POST /incidents/run`

When Elastic credentials are configured:

1. `client.ping()`
2. `indices.create` (ignore existing)
3. `index`
4. `search`
5. ES|QL query (`FROM incidents-logs | ... | STATS ...`)

When Agent Builder credentials are configured:

- workflow payload is dispatched to configured Agent Builder route
- response block includes `integration_path` and status details
