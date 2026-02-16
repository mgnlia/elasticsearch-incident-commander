# Demo Video Script & Cut Plan — DevOps Incident Commander

> **Target runtime: 3 minutes (180 seconds)**
> **Video URL placeholder: `[VIDEO_URL_PLACEHOLDER]`**

---

## Pre-production Notes

| Item | Detail |
|------|--------|
| Format | Screen recording + voiceover (no face cam required) |
| Resolution | 1920×1080 minimum |
| Audio | Clear voiceover, no background music during narration |
| Tools | OBS / Loom / QuickTime for capture; any editor for cuts |
| Screens needed | (1) Vercel dashboard, (2) GitHub repo, (3) Kibana Agent Builder (if accessible), (4) Terminal |

---

## Script & Cut Plan

### CUT 1 — Hook & Problem Statement (0:00–0:25) ~25s

**SCREEN:** Title card → fade to Vercel dashboard home page

**VOICEOVER:**
> "It's 3 AM. A production alert fires — CPU on your payment service just hit 95%. You have three hosts affected, cascading timeouts starting, and your on-call engineer is scrambling through five dashboards trying to figure out what happened.
>
> This is DevOps Incident Commander — a multi-agent system built on Elastic Agent Builder that handles the entire incident lifecycle automatically."

**CUTS:**
- 0:00–0:05 — Title card: "DevOps Incident Commander — Elastic Agent Builder Hackathon"
- 0:05–0:25 — Slow scroll on dashboard home showing the orchestration flow diagram and scenario cards

---

### CUT 2 — Architecture Overview (0:25–0:55) ~30s

**SCREEN:** Dashboard `/architecture` page

**VOICEOVER:**
> "Five specialized agents coordinate in sequence. The Incident Commander classifies severity and routes to Triage, which correlates alerts and maps the blast radius. Diagnosis runs root-cause analysis using ES|QL queries across logs, metrics, and traces. Remediation executes runbook actions — pod restarts, service scaling — and verifies the fix. Communication generates a timeline, sends Slack updates, and drafts a postmortem.
>
> Under the hood, 15 custom tools — eight ES|QL, two index-search, and five workflow tools — give each agent the right capabilities for its job."

**CUTS:**
- 0:25–0:40 — Architecture page: highlight each stage as narrated (use mouse pointer or zoom)
- 0:40–0:55 — Scroll down to show data flow section (logs, metrics, traces, alerts indices)

---

### CUT 3 — Live Demo Walkthrough (0:55–2:10) ~75s

**SCREEN:** Dashboard `/demo` page → CPU Spike scenario

**VOICEOVER:**
> "Let's walk through Scenario 1: a CPU spike on the payment service.
>
> Step 1 — the Incident Commander receives the alert and classifies it as P2 based on host spread and alert severity. It routes to Triage.
>
> Step 2 — Triage uses the alert correlator and service dependency tools to find three correlated alerts and identify the payment service as the epicenter.
>
> Step 3 — Diagnosis pulls logs and metrics via ES|QL. It finds an inefficient database query introduced in the latest deployment — that's our root cause.
>
> Step 4 — Remediation scales the service to absorb load and runs the fix verifier tool to confirm CPU drops below threshold.
>
> Step 5 — Communication generates the full incident timeline, fires a Slack notification, and drafts a postmortem with root cause, impact, and action items."

**CUTS:**
- 0:55–1:00 — Click "Scenario 1: CPU Spike" on demo page
- 1:00–1:15 — Step 1 (Commander): highlight severity classification output, click Next
- 1:15–1:30 — Step 2 (Triage): show correlated alerts, click Next
- 1:30–1:45 — Step 3 (Diagnosis): show root cause finding, click Next
- 1:45–2:00 — Step 4 (Remediation): show scaling action + verification, click Next
- 2:00–2:10 — Step 5 (Communication): show timeline + postmortem output

> **TIP:** Pause briefly on each step's tool badges to let judges see which Agent Builder tools are invoked.

---

### CUT 4 — Code & Setup (2:10–2:40) ~30s

**SCREEN:** GitHub repo → `setup/bootstrap.py` → terminal

**VOICEOVER:**
> "Everything is provisioned programmatically. One command — `uv run setup/bootstrap.py` — creates all Elasticsearch indices, registers every tool, and wires up the agents. A companion seed script populates three realistic incident scenarios with about 500 observability documents.
>
> The repo is fully open source under MIT. Agent configs live in `/agents`, tool definitions in `/tools/esql`, and workflows in `/workflows`."

**CUTS:**
- 2:10–2:20 — GitHub repo root: show file structure (agents/, tools/, workflows/, setup/)
- 2:20–2:30 — Open `setup/bootstrap.py` — scroll through `create_tools()` and `create_agents()` functions
- 2:30–2:40 — Terminal: show the bootstrap command and sample output (can be pre-recorded)

---

### CUT 5 — Impact & Close (2:40–3:00) ~20s

**SCREEN:** Dashboard home → title card

**VOICEOVER:**
> "DevOps Incident Commander turns a 45-minute scramble into a 3-minute automated resolution. It demonstrates multi-agent orchestration, ES|QL-powered reasoning, and workflow-driven remediation — all built on Elastic Agent Builder.
>
> Thanks for watching. Links to the live dashboard, repo, and documentation are in the submission."

**CUTS:**
- 2:40–2:50 — Dashboard home: quick pan across all three scenario cards
- 2:50–3:00 — End card with links:
  - 🔗 https://elastic-incident-commander.vercel.app
  - 📦 https://github.com/mgnlia/elastic-incident-commander
  - Elastic Agent Builder Hackathon logo

---

## Post-production Checklist

- [ ] Total runtime ≤ 3:00
- [ ] Upload to YouTube (unlisted) or Loom
- [ ] Paste video URL into Devpost submission + replace `[VIDEO_URL_PLACEHOLDER]` in all docs
- [ ] Verify audio is clear and screen text is readable at 720p
- [ ] Add captions/subtitles if time permits (accessibility bonus)
