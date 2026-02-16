# Elasticsearch Incident Commander

A runnable multi-agent incident response MVP with concrete Elasticsearch and Agent Builder integration points.

## Delivered in this checkpoint

- FastAPI backend (`agents/`) with deterministic **4-agent workflow**:
  - Triage Agent
  - Diagnosis Agent
  - Remediation Agent
  - Communication Agent
- Integration endpoint: `POST /incidents/run`
- **Elasticsearch integration wiring** (when credentials are configured):
  1. `indices.create` (idempotent create with ignore 400)
  2. `index` (incident document write)
  3. `search` (recent incident retrieval)
  4. ES|QL query (`STATS incident_count = COUNT(*)`)
- **Agent Builder integration path** (when configured):
  - outbound POST to `AGENT_BUILDER_BASE_URL + AGENT_BUILDER_ROUTE`
  - bearer auth via `AGENT_BUILDER_API_KEY`
- Frontend dashboard (`frontend/`) with Vercel fallback API route (`/api/incidents/run`)
- CI workflow running backend tests with `uv`

## Repository

- GitHub: https://github.com/mgnlia/elasticsearch-incident-commander

## Architecture

```text
frontend (static UI)
   └── POST /api/incidents/run (Vercel function) OR localhost backend
            ↓
        FastAPI backend (/incidents/run)
            ├── triage
            ├── diagnosis
            ├── remediation
            ├── communication
            ├── Elasticsearch create/index/search/ES|QL
            └── Agent Builder dispatch
```

## Quickstart

### Backend (uv)

```bash
cd agents
uv sync --dev
uv run uvicorn app.main:app --reload --port 8000
```

### Tests

```bash
cd agents
uv run pytest
```

### Frontend local

```bash
cd frontend
python -m http.server 8081
# open http://localhost:8081
```

By default local frontend calls `http://localhost:8000/incidents/run`.

## API

### `GET /health`
Returns service health.

### `POST /incidents/run`
Runs end-to-end multi-agent incident workflow and attaches integration status blocks:

- `elastic`: `ok | skipped | error`
- `agent_builder`: `ok | skipped | error`

Example payload:

```json
{
  "service": "checkout-api",
  "severity": "high",
  "summary": "Latency spikes after deploy",
  "signals": ["p95 latency > 2.5s", "error rate 7%"],
  "recent_deploy_sha": "abc1234"
}
```
