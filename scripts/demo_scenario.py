"""Run a deterministic incident scenario against local API."""

from __future__ import annotations

import json
import urllib.request


def main() -> None:
    payload = {
        "service": "checkout-api",
        "severity": "high",
        "summary": "Latency spikes after deploy",
        "signals": ["p95 latency > 2.5s", "error rate 7%"],
        "recent_deploy_sha": "abc1234",
    }

    req = urllib.request.Request(
        "http://localhost:8000/incidents/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()
