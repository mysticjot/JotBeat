"""tools/keys.py — the ONLY writer for .env (HANDOFF-PHASE3 Addendum B).

Shared by the CLI (`jotbeat keys ...`) and the settings UI (`jotbeat ui`) —
one writer module, one file shape. Rules enforced here:
  - .env must be git-ignored before ANY write (fail closed).
  - Writes are atomic (temp file + os.replace); unrelated lines and comments
    are preserved verbatim.
  - Values are never printed, logged, or returned — only char counts.
  - Nothing here touches the ledger (events.jsonl).
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path

KEY_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class KeysError(Exception):
    """Refusal — loud, safe, no partial state."""


def assert_env_gitignored(root: Path) -> None:
    """Refuse to run unless `git check-ignore .env` confirms ignore status.
    Fails CLOSED: no git repo / git error / not ignored -> refusal."""
    proc = subprocess.run(
        ["git", "-C", str(root), "check-ignore", ".env"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise KeysError(
            f"REFUSED: .env is not git-ignored in {root} "
            "(git check-ignore failed or not a repo). "
            "Add '.env' to .gitignore before any key can be written — "
            "keys must never be committable."
        )


def _env_path(root: Path) -> Path:
    return root / ".env"


def _read_lines(root: Path) -> list[str]:
    path = _env_path(root)
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _atomic_write(root: Path, lines: list[str]) -> None:
    path = _env_path(root)
    fd, tmp = tempfile.mkstemp(dir=root, prefix=".env.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, path)
    except BaseException:
        # best-effort temp cleanup; the original exception always wins
        with suppress(OSError):
            os.unlink(tmp)
        raise


def _is_key_line(line: str, name: str) -> bool:
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        return False
    return s.split("=", 1)[0].strip() == name


def set_key(root: Path, name: str, value: str) -> int:
    """Write/update NAME=value in .env. Returns the value length.
    Raises KeysError on empty value, bad name, or un-ignored .env."""
    name = name.strip()
    value = value.strip()
    if not KEY_NAME_RE.match(name):
        raise KeysError(f"invalid variable name: {name!r}")
    if not value:
        raise KeysError(f"refused: empty value for {name}")
    assert_env_gitignored(root)

    lines = _read_lines(root)
    for i, line in enumerate(lines):
        if _is_key_line(line, name):
            lines[i] = f"{name}={value}"
            break
    else:
        lines.append(f"{name}={value}")
    _atomic_write(root, lines)
    return len(value)


def remove_key(root: Path, name: str) -> bool:
    """Delete NAME from .env. Returns True if a line was removed."""
    name = name.strip()
    assert_env_gitignored(root)
    lines = _read_lines(root)
    kept = [l for l in lines if not _is_key_line(l, name)]
    if len(kept) == len(lines):
        return False
    _atomic_write(root, kept)
    return True


def key_status(root: Path, routing: dict) -> dict:
    """Presence-only status. Derives expected key NAMES from providers.json
    env_key fields (agnostic — no hardcoded list). Flags stale lines.
    Returns {"expected": [{name, providers, set, chars}], "stale": [names]}.
    Never contains values."""
    expected: dict[str, list[str]] = {}
    for pname, p in routing["providers"].items():
        if not p.get("env_key"):
            continue  # keyless local server (Ollama, LiteLLM) — no key to track
        expected.setdefault(p["env_key"], []).append(pname)

    present: dict[str, int] = {}
    all_names: set[str] = set()
    for line in _read_lines(root):
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        name, _, value = s.partition("=")
        name = name.strip()
        all_names.add(name)
        v = value.split(" #", 1)[0].strip()
        if v:
            present[name] = len(v)

    rows = [
        {
            "name": name,
            "providers": sorted(providers),
            "set": name in present,
            "chars": present.get(name, 0),
        }
        for name, providers in sorted(expected.items())
    ]
    stale = sorted(n for n in all_names if n not in expected)
    return {"expected": rows, "stale": stale}
