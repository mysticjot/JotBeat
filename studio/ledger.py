"""
ledger.py — the receipt. Every model call, its tokens, its cost.
Append-only. The Producer reads this; nobody else writes it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "state" / "events.jsonl"
PROVIDERS_FILE = ROOT / "studio" / "providers.json"


def _prices() -> dict:
    return json.loads(PROVIDERS_FILE.read_text(encoding="utf-8"))["providers"]


def log_call(
    *,
    task_id,
    role,
    provider,
    model,
    tokens_in,
    tokens_out,
    cached_in=0,
    retry=0,
    escalated=False,
    latency_ms=0,
) -> dict:
    p = _prices()[provider]
    cost = (
        (tokens_in - cached_in) / 1e6 * p["price_in"]
        + cached_in / 1e6 * p.get("price_cached_in", p["price_in"])
        + tokens_out / 1e6 * p["price_out"]
    )
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "model_call",
        "task": task_id,
        "role": role,
        "provider": provider,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cached_in": cached_in,
        "retry": retry,
        "escalated": escalated,
        "latency_ms": latency_ms,
        "cost_usd": round(cost, 6),
    }
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    return event


def log_event(kind: str, **fields) -> None:
    event = {"ts": datetime.now(timezone.utc).isoformat(), "type": kind, **fields}
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def cost_report() -> dict:
    """cost per game, per role, per provider, per verified task."""
    calls = []
    if EVENTS.exists():
        for line in EVENTS.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            if e.get("type") == "model_call":
                calls.append(e)
    total = sum(c["cost_usd"] for c in calls)
    verified = (
        {
            json.loads(l)["task"]
            for l in EVENTS.read_text(encoding="utf-8").splitlines()
            if '"type": "task_verified"' in l
        }
        if EVENTS.exists()
        else set()
    )
    by_role: dict[str, float] = {}
    by_provider: dict[str, float] = {}
    for c in calls:
        by_role[c["role"]] = by_role.get(c["role"], 0) + c["cost_usd"]
        by_provider[c["provider"]] = by_provider.get(c["provider"], 0) + c["cost_usd"]
    return {
        "total_usd": round(total, 4),
        "calls": len(calls),
        "tokens_in": sum(c["tokens_in"] for c in calls),
        "tokens_out": sum(c["tokens_out"] for c in calls),
        "by_role": {k: round(v, 4) for k, v in sorted(by_role.items())},
        "by_provider": {k: round(v, 4) for k, v in sorted(by_provider.items())},
        "cost_per_verified_task": round(total / len(verified), 4) if verified else None,
    }
