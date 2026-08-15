"""tools/git.py — commit verified work. Called by the orchestrator ONLY after
an audit lands MET — the graph is the gate, this is just the pen."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def commit_changes(task: dict, artifacts: list[str]) -> str | None:
    """git add the task's artifacts + commit with a conventional message.
    Returns the commit hash, or None if the commit failed."""
    existing = [a for a in artifacts if (ROOT / a).exists()]
    if existing:
        _git(["add", "--", *existing])

    title = task.get("title", task["id"])
    msg = f"feat({task.get('role', 'studio')}): {title} [{task['id']}]"
    proc = _git(["commit", "--allow-empty", "-m", msg])
    if proc.returncode != 0:
        return None

    head = _git(["rev-parse", "--short", "HEAD"])
    return head.stdout.strip() or None
