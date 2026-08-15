"""tools/shell.py — deterministic build verification (BVT). $0, no model calls."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GAME_DIR = ROOT / "game"


def _run(cmd: str, cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        cmd, cwd=cwd, shell=True,
        capture_output=True, text=True, timeout=600,
        encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _log_tail(text: str, lines: int = 50) -> str:
    """Log tails, not logs (docs/BUDGET.md rationing rule 3)."""
    return "\n".join(text.splitlines()[-lines:])


def run_bvt() -> dict:
    """Install (if needed) + production build of game/.
    Returns {"passed": bool, "steps": [...], "log_tail": str}."""
    steps: list[str] = []
    logs: list[str] = []

    if not (GAME_DIR / "node_modules").exists():
        rc, out = _run("npm ci", GAME_DIR)
        steps.append("install")
        logs.append(out)
        if rc != 0:
            return {"passed": False, "steps": steps, "log_tail": _log_tail("".join(logs))}

    rc, out = _run("npm run build-nolog", GAME_DIR)
    steps.append("build")
    logs.append(out)

    return {
        "passed": rc == 0 and (GAME_DIR / "dist" / "index.html").exists(),
        "steps": steps,
        "log_tail": _log_tail("".join(logs)),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_bvt(), indent=2))
