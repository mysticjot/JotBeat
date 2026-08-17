"""tools/console_data.py — read-mostly data layer for the JotBeat Console
(Creative Director deliverable: `jotbeat ui` console tabs).

Every function here is a PRESENTATION LAYER over state that already exists:
  - state/events.jsonl        (pipeline, costs, gate history)
  - state/project-state.json  (phase gates — the one writable file)
  - state/task-queue.json     (live task statuses)
  - docs/BACKLOG.md, docs/BUDGET.md, docs/DECISIONS.md (parsed, never edited)
  - reports/cert/latest.md    (commercial baseline pass/fail)
  - game/package.json         (stack line, D-0005)
  - artifacts/ + reports/ + game/maps + game/assets (evidence files)

The only write is decide_gate(): the human Creative Director's phase-gate
decision, recorded in project-state.json `gates` (state/SCHEMA.md:
pending | passed | failed) plus a `gate_decision` event appended to
events.jsonl via ledger.log_event. This module NEVER touches .env,
providers.json, or credentials of any kind.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

EVENTS_REL = Path("state") / "events.jsonl"
PROJECT_STATE_REL = Path("state") / "project-state.json"
TASK_QUEUE_REL = Path("state") / "task-queue.json"

# Roles shown on the Pipeline tab even when they have no events yet —
# the studio's standing roster (docs/BUDGET.md caps table). Any other role
# that appears in the ledger is appended after these.
ROSTER = [
    "director",
    "coder",
    "qa",
    "auditor",
    "narrative",
    "designer",
    "producer",
    "vision",
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
AUDIO_EXTS = {".mp3", ".ogg", ".wav"}
TEXT_EXTS = {".md", ".txt", ".py", ".json", ".ldtk"}


class ConsoleError(Exception):
    """Refusal — loud, safe, no partial state."""


def _read_json(root: Path, rel: Path) -> dict:
    path = root / rel
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def read_events(root: Path) -> list[dict]:
    """All ledger events, oldest first. Skips corrupt lines rather than
    dying — the ledger is append-only and a torn final line is possible."""
    path = root / EVENTS_REL
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        with suppress(json.JSONDecodeError):
            events.append(json.loads(line))
    return events


# ------------------------------------------------------------------ pipeline


def pipeline_state(root: Path) -> dict:
    """Most recent event per role + a tail feed of the latest events."""
    events = read_events(root)
    project = _read_json(root, PROJECT_STATE_REL)

    by_role: dict[str, dict] = {}
    for e in events:
        role = e.get("role")
        if role:
            by_role[role] = e  # last one wins

    order = [r for r in ROSTER if r in by_role]
    order += sorted(r for r in by_role if r not in ROSTER)
    roles = []
    for name in order:
        e = by_role[name]
        roles.append(
            {
                "role": name,
                "type": e.get("type"),
                "task": e.get("task"),
                "model": e.get("model"),
                "provider": e.get("provider"),
                "ts": e.get("ts"),
                "detail": e.get("error") or "",
            }
        )

    feed = []
    for e in events[-40:]:
        feed.append(
            {
                "ts": e.get("ts"),
                "type": e.get("type"),
                "task": e.get("task"),
                "role": e.get("role"),
                "model": e.get("model"),
                "provider": e.get("provider"),
                "passed": e.get("passed"),
                "cost_usd": e.get("cost_usd"),
                "detail": e.get("error") or "",
            }
        )
    feed.reverse()

    return {
        "current_task": project.get("current_task"),
        "phase": project.get("phase"),
        "phase_name": project.get("phase_name"),
        "roles": roles,
        "roles_without_events": [r for r in ROSTER if r not in by_role],
        "feed": feed,
        "event_count": len(events),
    }


# --------------------------------------------------------------------- gates


def _recent_screenshots(root: Path, limit: int = 6) -> list[dict]:
    base = root / "artifacts" / "screenshots"
    shots = []
    if base.is_dir():
        for p in base.rglob("*"):
            # the console's own gate-evidence captures are not game evidence
            if "console" in p.relative_to(base).parts:
                continue
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                shots.append(p)
    shots.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            "path": p.relative_to(root).as_posix(),
            "name": p.name,
            "mtime": datetime.fromtimestamp(
                p.stat().st_mtime, timezone.utc
            ).isoformat(),
        }
        for p in shots[:limit]
    ]


def gates_state(root: Path) -> dict:
    """Pending phase gates from project-state.json with evidence attached
    (latest cert + recent screenshots), plus the most recent decided gate."""
    project = _read_json(root, PROJECT_STATE_REL)
    gates = project.get("gates") or {}

    cert = root / "reports" / "cert" / "latest.md"
    evidence = {
        "cert": "reports/cert/latest.md" if cert.exists() else None,
        "cert_summary": cert_summary(root),
        "screenshots": _recent_screenshots(root),
        "counters": project.get("counters") or {},
    }

    pending = [
        {"gate": g, "status": s, "evidence": evidence}
        for g, s in gates.items()
        if s == "pending"
    ]

    # Most recent decision: prefer console-recorded gate_decision events;
    # fall back to the last decided gate in project-state.json.
    last_decided = None
    for e in reversed(read_events(root)):
        if e.get("type") == "gate_decision":
            last_decided = {
                "gate": e.get("gate"),
                "status": e.get("decision"),
                "ts": e.get("ts"),
                "source": "events.jsonl",
            }
            break
    if last_decided is None:
        for g in sorted(gates, reverse=True):
            if gates[g] != "pending":
                last_decided = {
                    "gate": g,
                    "status": gates[g],
                    "ts": None,
                    "source": "project-state.json",
                }
                break

    return {"pending": pending, "last_decided": last_decided, "all": gates}


def decide_gate(root: Path, gate: str, decision: str) -> dict:
    """Record the Creative Director's gate decision. Writes
    state/project-state.json (atomic temp+replace, same pattern as
    tools/keys.py) and appends a gate_decision event to the ledger."""
    if decision not in ("passed", "failed"):
        raise ConsoleError(f"invalid decision {decision!r} — passed | failed")
    state_file = root / PROJECT_STATE_REL
    if not state_file.exists():
        raise ConsoleError("state/project-state.json missing")
    data = json.loads(state_file.read_text(encoding="utf-8"))
    gates = data.setdefault("gates", {})
    if gate not in gates:
        raise ConsoleError(f"unknown gate {gate!r} — known: {sorted(gates)}")

    gates[gate] = decision
    fd, tmp = tempfile.mkstemp(dir=state_file.parent, prefix=".ps.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, indent=2) + "\n")
        os.replace(tmp, state_file)
    except BaseException:
        with suppress(OSError):
            os.unlink(tmp)
        raise

    # Append the ledger event to THIS root's events.jsonl. (ledger.log_event
    # targets the repo root baked into ledger.py — fine for the studio, wrong
    # for any non-repo root, so the console appends directly.)
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "gate_decision",
        "gate": gate,
        "decision": decision,
        "by": "creative_director",
        "via": "console",
    }
    with (root / EVENTS_REL).open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    return {"gate": gate, "decision": decision}


# --------------------------------------------------------------------- costs


def costs_state(root: Path) -> dict:
    """Ledger totals per game / role / provider vs the budget caps parsed
    from docs/BUDGET.md (the caps table is per-CALL; the cost/token targets
    are per-GAME). Missing budget numbers surface as None, never guessed."""
    events = read_events(root)
    calls = [e for e in events if e.get("type") == "model_call"]
    verified = {e.get("task") for e in events if e.get("type") == "task_verified"}

    total = sum(e.get("cost_usd", 0.0) for e in calls)
    tokens_in = sum(e.get("tokens_in", 0) for e in calls)
    tokens_out = sum(e.get("tokens_out", 0) for e in calls)

    def bucket(key: str) -> list[dict]:
        agg: dict[str, dict] = {}
        for e in calls:
            name = e.get(key) or "?"
            b = agg.setdefault(
                name,
                {
                    "name": name,
                    "cost_usd": 0.0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "calls": 0,
                },
            )
            b["cost_usd"] += e.get("cost_usd", 0.0)
            b["tokens_in"] += e.get("tokens_in", 0)
            b["tokens_out"] += e.get("tokens_out", 0)
            b["calls"] += 1
        return sorted(agg.values(), key=lambda b: -b["cost_usd"])

    by_role = bucket("role")
    caps = _budget_caps(root)
    for row in by_role:
        cap = caps["per_role"].get(row["name"])
        if cap:
            row["cap_in"] = cap["max_in"]
            row["cap_out"] = cap["max_out"]

    return {
        "total_usd": round(total, 4),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "calls": len(calls),
        "verified_tasks": len([t for t in verified if t]),
        "cost_per_verified_task": (
            round(total / len(verified), 4) if verified else None
        ),
        "by_role": by_role,
        "by_provider": bucket("provider"),
        "budget": caps,
    }


def _budget_caps(root: Path) -> dict:
    """Parse docs/BUDGET.md: per-role per-call token caps table + the
    per-game cost/token targets from the cost-model section."""
    budget_file = root / "docs" / "BUDGET.md"
    caps: dict = {
        "source": "docs/BUDGET.md",
        "per_role": {},
        "target_cost_per_game": None,
        "worst_case_per_game": None,
        "target_tokens_per_game": None,
        "drift_tokens_per_game": None,
    }
    if not budget_file.exists():
        caps["source"] = None
        return caps
    text = budget_file.read_text(encoding="utf-8")

    for m in re.finditer(
        r"^\| (\w[\w /]*) \| ([\d,]+) \| ([\d,]+) \|", text, re.MULTILINE
    ):
        role = m.group(1).strip()
        if role.lower() == "role":
            continue
        caps["per_role"][role] = {
            "max_in": int(m.group(2).replace(",", "")),
            "max_out": int(m.group(3).replace(",", "")),
        }

    m = re.search(r"\$([0-9]+(?:\.[0-9]+)?)/game", text)
    if m:
        caps["target_cost_per_game"] = float(m.group(1))
    m = re.search(r"worst case ~?\$([0-9]+(?:\.[0-9]+)?)", text)
    if m:
        caps["worst_case_per_game"] = float(m.group(1))
    m = re.search(r"[Rr]ationing: ~?([0-9.]+)M tokens/game", text)
    if m:
        caps["target_tokens_per_game"] = int(float(m.group(1)) * 1_000_000)
    m = re.search(r"above ~?([0-9.]+)M", text)
    if m:
        caps["drift_tokens_per_game"] = int(float(m.group(1)) * 1_000_000)
    return caps


# ----------------------------------------------------------------- artifacts


def _kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in TEXT_EXTS:
        return "text"
    return "other"


def _list_group(root: Path, rel: str, recursive: bool = True) -> list[dict]:
    base = root / rel
    if not base.is_dir():
        return []
    it = base.rglob("*") if recursive else base.glob("*")
    out = []
    for p in sorted(it):
        if not p.is_file() or p.name.startswith("."):
            continue
        st = p.stat()
        out.append(
            {
                "name": p.name,
                "path": p.relative_to(root).as_posix(),
                "size": st.st_size,
                "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                "kind": _kind(p),
            }
        )
    out.sort(key=lambda e: e["mtime"], reverse=True)
    return out


def artifacts_state(root: Path) -> dict:
    """The evidence browser: screenshots, cert reports, maps, audio."""
    return {
        "screenshots": _list_group(root, "artifacts/screenshots"),
        "cert": _list_group(root, "reports/cert", recursive=False),
        "maps": _list_group(root, "game/maps", recursive=False),
        "audio": _list_group(root, "game/assets/audio"),
    }


# ------------------------------------------------------------------- backlog


BL_RE = re.compile(
    r"^### (BL-\d+): (.+?)\n(?P<body>.*?)(?=^### |\Z)",
    re.MULTILINE | re.DOTALL,
)


def cert_summary(root: Path) -> dict:
    """Latest cert: overall verdict + commercial-baseline checklist + ACs."""
    cert = root / "reports" / "cert" / "latest.md"
    if not cert.exists():
        return {"exists": False}
    text = cert.read_text(encoding="utf-8")
    out: dict = {"exists": True, "file": "reports/cert/latest.md"}

    m = re.search(r"^# JotBeat Cert — (.+)$", text, re.MULTILINE)
    out["date"] = m.group(1).strip() if m else None
    m = re.search(r"overall: \*\*(.+?)\*\*", text)
    out["overall"] = m.group(1) if m else None

    baseline = []
    sec = re.search(
        r"## Commercial Baseline\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    if sec:
        for m in re.finditer(
            r"^- \*\*(.+?): (PASS|FAIL)\*\* — (.*)$", sec.group(1), re.MULTILINE
        ):
            detail = m.group(3).strip()
            baseline.append(
                {
                    "name": m.group(1).strip(),
                    "passed": m.group(2) == "PASS",
                    "detail": detail[:160] + ("…" if len(detail) > 160 else ""),
                }
            )
    out["baseline"] = baseline

    acs = re.findall(r"^### (AC-\d+) — (MET|UNMET|NOT MET)", text, re.MULTILINE)
    out["acs_met"] = sum(1 for _, s in acs if s == "MET")
    out["acs_total"] = len(acs)
    return out


def backlog_state(root: Path) -> dict:
    """docs/BACKLOG.md items with live status merged from
    state/task-queue.json (the orchestrator's truth), plus the current
    commercial-baseline verdict from reports/cert/latest.md."""
    backlog_file = root / "docs" / "BACKLOG.md"
    items = []
    if backlog_file.exists():
        text = backlog_file.read_text(encoding="utf-8")
        for m in BL_RE.finditer(text):
            body = m.group("body")

            def field(name: str, text: str = body) -> str | None:
                fm = re.search(rf"^{name}: (.+)$", text, re.MULTILINE)
                return fm.group(1).strip() if fm else None

            items.append(
                {
                    "id": m.group(1),
                    "title": m.group(2).strip(),
                    "role": field("Role") or "coder",
                    "status": field("Status") or "BACKLOG",
                    "milestone": field("Milestone"),
                    "priority": field("Priority"),
                    "depends_on": field("Depends on"),
                    "acs": re.findall(r"AC-\d+", field("ACs") or ""),
                }
            )

    queue = _read_json(root, TASK_QUEUE_REL)
    live = {i.get("id"): i for i in queue.get("items", [])}
    for item in items:
        q = live.get(item["id"])
        if q and q.get("status"):
            item["live_status"] = q["status"]
        else:
            item["live_status"] = None

    return {
        "items": items,
        "baseline": cert_summary(root),
        "queue_file": "state/task-queue.json" if queue else None,
    }


# --------------------------------------------------------------------- stack


def stack_state(root: Path) -> dict:
    """The stack line: exact versions from game/package.json, anchored to
    docs/DECISIONS.md D-0005 so nobody infers the stack from bug reports."""
    pkg_file = root / "game" / "package.json"
    pkg = {}
    if pkg_file.exists():
        with suppress(OSError, json.JSONDecodeError):
            pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
    deps = pkg.get("dependencies", {})
    dev = pkg.get("devDependencies", {})

    lines = [
        {"label": "Engine", "value": f"Phaser {deps.get('phaser', '?')} (NOT v3)"},
        {"label": "Language", "value": f"TypeScript {dev.get('typescript', '?')}"},
        {"label": "Build", "value": f"Vite {dev.get('vite', '?')}"},
        {
            "label": "Test",
            "value": f"Playwright {dev.get('@playwright/test', '?')} "
            f"+ pixelmatch {dev.get('pixelmatch', '?')}",
        },
        {"label": "Game version", "value": pkg.get("version", "?")},
        {
            "label": "Wrappers",
            "value": "Electron (desktop) + Capacitor (mobile) — D-0002",
        },
        {"label": "Studio", "value": "Python stdlib + LangGraph orchestrator"},
    ]

    d0005 = None
    decisions = root / "docs" / "DECISIONS.md"
    if decisions.exists():
        text = decisions.read_text(encoding="utf-8")
        m = re.search(
            r"## D-0005 — .*?\n\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        if m:
            d0005 = " ".join(m.group(1).split())
    return {
        "lines": lines,
        "source": "game/package.json + docs/DECISIONS.md D-0005",
        "d0005": d0005,
    }
