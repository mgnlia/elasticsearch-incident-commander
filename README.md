# Elasticsearch Incident Commander

A runnable multi-agent incident response MVP for the Elasticsearch Agent Builder sprint lane.

## What this checkpoint includes

- Python FastAPI backend with a **4-agent workflow**:
  - Triage Agent
  - Diagnosis Agent
  - Remediation Agent
  - Communication Agent
- Deterministic workflow orchestration endpoint: `POST /incidents/run`
- Static frontend dashboard (`frontend/`) to simulate incidents and render timeline output
- Test coverage for health and workflow contracts
- Vercel-ready frontend config (`frontend/vercel.json`)

## Repository

- GitHub: https://github.com/mgnlia/elasticsearch-incident-commander

## Architecture

```
frontend (static UI)
    ↓ POST /incidents/run
agents FastAPI service
    ├── triage
    ├── diagnosis
    ├── remediation
    └── communication
```

## Quickstart

### Backend (uv)

```bash
cd agents
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Tests

```bash
cd agents
uv run pytest
```

### Frontend

```bash
cd frontend
python -m http.server 8081
# open http://localhost:8081
```

By default frontend calls `http://localhost:8000`.

## API

### `GET /health`
Returns service health.

### `POST /incidents/run`
Runs end-to-end multi-agent incident workflow.

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

## Execution ETA table (checkpoint view)

| Milestone | Status | ETA |
|---|---|---|
| Repo bootstrap + runnable workflow | ✅ complete | now |
| Elasticsearch data/index wiring | ⏳ next | +6h |
| Agent Builder tool integration | ⏳ next | +12h |
| Demo scenario recording package | ⏳ next | +24h |
