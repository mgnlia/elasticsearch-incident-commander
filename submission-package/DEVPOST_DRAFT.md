# Devpost Submission Draft — DevOps Incident Commander

> **Word count target: ~400 words. Paste directly into the Devpost description field.**

---

## What it does

DevOps Incident Commander is a five-agent incident response system built on Elastic Agent Builder. When a production alert fires, the Incident Commander agent classifies severity and routes the event through four specialist agents — Triage, Diagnosis, Remediation, and Communication — that coordinate in sequence to resolve the incident without human intervention.

Each agent owns a bounded responsibility and hands structured output to the next. Triage correlates related alerts and maps the blast radius across services. Diagnosis performs root-cause analysis using logs, metrics, and APM traces retrieved through ES|QL and index-search tools. Remediation executes runbook actions (pod restarts, service scaling) and verifies the fix. Communication generates a timeline, pushes a Slack notification, and drafts a postmortem — all automatically.

## How we built it

The entire system is provisioned programmatically. A single `uv run setup/bootstrap.py` command creates all Elasticsearch indices, registers 15 custom tools (8 ES|QL, 2 index-search, 5 workflow), and wires up the five agents with their tool bindings and inter-agent routing. A companion `seed_data.py` script populates three realistic incident scenarios — a CPU spike on a payment service, a memory leak with OOM kills, and a cascading database failure — totaling ~500 observability documents.

We paired the backend with a Next.js dashboard deployed on Vercel that visualizes the agent orchestration flow, the architecture diagram, and interactive step-through demos for each scenario. The dashboard serves as both a judging aid and a standalone walkthrough for anyone evaluating the project.

## Elasticsearch Agent Builder features used

- **ES|QL tools** — parameterized queries for severity classification, alert correlation, log analysis, metric anomaly detection, trace correlation, service dependency mapping, incident timeline generation, and fix verification.
- **Index-search tools** — free-text search across `logs-*` and `traces-apm*` patterns for broad evidence retrieval.
- **Workflow tools** — automated escalation, pod restart, service scaling, Slack notification, and postmortem generation pipelines.
- **Multi-agent orchestration** — Commander routes to specialists via Agent Builder's agent-to-agent handoff, keeping context across the full incident lifecycle.

## What we liked

1. **Tool composability** — defining ES|QL queries as discrete tools and letting the agent decide which to invoke made the system genuinely flexible without prompt engineering gymnastics.
2. **Workflow actions** — the ability to attach side-effect workflows (Slack, scaling) directly to an agent's tool palette blurred the line between "reasoning" and "doing" in a useful way.

## Challenges

1. **Tool-binding naming precision** — workflow tool names must match exactly between the definition and the agent config; a single mismatch silently drops the tool from the agent's palette.
2. **Observability at orchestration boundaries** — tracing context across agent-to-agent handoffs required careful structured output design to avoid losing diagnostic detail between stages.

---

**Links**
- 🔗 Live dashboard: https://elastic-incident-commander.vercel.app
- 📦 Repository: https://github.com/mgnlia/elastic-incident-commander
- 🎥 Demo video: `[VIDEO_URL_PLACEHOLDER]`
- 🐦 Social post: `[SOCIAL_POST_PLACEHOLDER]`
