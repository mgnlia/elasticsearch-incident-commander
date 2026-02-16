# Checkpoint Evidence Package — 2026-02-16

## Scope

Integration hardening for Elasticsearch sprint support lane:

- Real Elasticsearch wiring in backend service
- Index create/index/search/ES|QL operation path
- Agent Builder dispatch path + response handling
- CI-backed test expansion for integration contracts
- Vercel frontend fallback proxy path for live demo URL

## Commit-level evidence

> Fill after push with immutable SHA links.

- Integration hardening commit: `TBD`
- Test expansion commit: `TBD`
- Frontend Vercel API fallback commit: `TBD`

## Code evidence map

- `agents/app/elasticsearch_client.py`
  - `indices.create` with mapping and `ignore_status=400`
  - incident `index(...)`
  - recent `search(...)`
  - `client.esql.query(...)` with parameterized ES|QL
  - ping guard + duration telemetry in response payload
- `agents/app/agent_builder_client.py`
  - configured endpoint dispatch with bearer auth
  - explicit `integration_path` reporting on skip/error/success
- `agents/tests/test_integrations.py`
  - asserts create/index/search/ES|QL paths execute
  - asserts Agent Builder success and HTTP-error branches
- `frontend/api/incidents/run.js`
  - Vercel function proxy to backend `/incidents/run`
  - timeout, upstream error handling, and CORS

## CI evidence

> Fill after push.

- GitHub Actions run URL: `TBD`
- Status: `TBD`

## Deployment evidence

> Fill after deploy.

- Vercel URL: `TBD`
- Route used: `/api/incidents/run`

## Remaining external dependencies / blockers

- Elastic Cloud live validation requires valid `ELASTIC_CLOUD_ID` + `ELASTIC_API_KEY`
- Agent Builder live validation requires reachable `AGENT_BUILDER_BASE_URL` + `AGENT_BUILDER_API_KEY`
- Vercel proxy requires `INCIDENT_BACKEND_URL` env var
