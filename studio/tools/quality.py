"""tools/quality.py — the studio's post-coding quality gate (AGENTS.md §6).

Runs both deterministic scanners and fails on real problems:
  - aislop scan --json  (Python + TS slop, lint, security) — errors must be 0
  - fallow dead-code    (TS/JS module graph)               — must be clean
  - fallow dupes        (copy-paste detection)             — must be clean

`fallow health` is intentionally NOT gated yet: it flags Player.ts with a
CRAP estimate that assumes 0% test coverage; the Phase 4 QA harness is the
honest fix, not a threshold bump.

Both scanners go through npx so no global install is required (CI-friendly).
AISLOP_NO_HISTORY=1 keeps aislop from writing .aislop/history.jsonl on
machine runs. No credentials are involved — both tools are fully local and
deterministic (no LLM at runtime).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

NPX = "npx.cmd" if os.name == "nt" else "npx"


def _score_floor(root: Path) -> int | None:
    """Read ci.failBelow from .aislop/config.yml. Minimal parse on purpose —
    our own file, one key; avoids a yaml dependency for one integer."""
    import re

    cfg = Path(root) / ".aislop" / "config.yml"
    if not cfg.exists():
        return None
    m = re.search(
        r"^\s*failBelow:\s*(\d+)", cfg.read_text(encoding="utf-8"), re.MULTILINE
    )
    return int(m.group(1)) if m else None


def _run(
    cmd: list[str], root: Path, env_extra: dict | None = None
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(env_extra or {})
    return subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
    )


def run_quality(root: Path) -> int:
    """Run all quality gates. Returns 0 on pass, 1 on any failure."""
    root = Path(root)
    failures: list[str] = []

    # aislop: error-level findings must be zero
    proc = _run(
        [NPX, "-y", "aislop", "scan", "--json"], root, {"AISLOP_NO_HISTORY": "1"}
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("aislop: could not parse JSON output (scanner broken?)")
        print((proc.stdout or "")[-1500:])
        print((proc.stderr or "")[-1500:])
        return 1
    diags = report.get("diagnostics", [])
    errors = [d for d in diags if str(d.get("severity", "")).lower() == "error"]
    warnings = len(diags) - len(errors)
    score = report.get("score")
    print(f"aislop: score {score}/100 · {len(errors)} errors · {warnings} warnings")
    for d in errors:
        print(
            f"  [ERROR] {d.get('filePath')}:{d.get('line')} "
            f"[{d.get('rule')}] {d.get('message')}"
        )
    if errors:
        failures.append(f"aislop: {len(errors)} error-level findings")

    # score floor from .aislop/config.yml (ci.failBelow) — ratchet up only
    floor = _score_floor(root)
    if floor is not None and isinstance(score, (int, float)) and score < floor:
        failures.append(f"aislop: score {score} below floor {floor}")

    # fallow: dead-code + dupes must exit clean
    for sub in ("dead-code", "dupes"):
        proc = _run([NPX, "-y", "fallow", sub], root)
        ok = proc.returncode == 0
        print(f"fallow {sub}: {'clean' if ok else 'ISSUES'}")
        if not ok:
            failures.append(f"fallow {sub}")
            for line in (proc.stdout or proc.stderr).strip().splitlines()[-15:]:
                print("  " + line)

    if failures:
        print("\nQUALITY GATE FAILED: " + "; ".join(failures))
        print("fix the findings for real; mechanical cleanup: aislop fix --safe")
        print("suppress only with a documented reason (see .fallowrc.json)")
        return 1
    print("\nquality gate passed")
    return 0
