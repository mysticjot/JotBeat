"""tools/browser.py — scripted QA via Playwright. Fake input + state
assertions against window.__game.state (ADR-0001). $0 infra."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GAME_DIR = ROOT / "game"


def run_ac_suite(acceptance_ids: list[str]) -> dict:
    """Run the Playwright suite, optionally filtered to tests whose names
    carry the given AC ids. Returns {"passed": bool, "tests": [...]}."""
    env = dict(os.environ)
    # Browsers installed into game/node_modules (repo-local, gitignored).
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")
    # Never reuse an existing webServer: playwright.config sets
    # reuseExistingServer when CI is unset, which silently tests STALE bytes
    # if a previous `vite preview` is still on the port (blocked BL-005 four
    # times against a pre-relocation build while the code was already fixed).
    # With CI set, playwright always runs the configured command (fresh build
    # + preview) and fails loudly if the port is occupied.
    env["CI"] = "1"

    cmd = "npx playwright test --reporter=list"
    if acceptance_ids:
        cmd += " --grep " + "|".join(acceptance_ids)

    proc = subprocess.run(
        cmd,
        cwd=GAME_DIR,
        shell=True,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    lines = [
        l.strip()
        for l in out.splitlines()
        if l.strip().startswith(("✓", "✘", "x ", "-"))
    ]

    return {
        "passed": proc.returncode == 0,
        "tests": acceptance_ids or ["all"],
        "results": lines,
        "log_tail": "\n".join(out.splitlines()[-50:]),
    }
