#!/usr/bin/env python3
"""test_provider_cli.py — Phase 3 Addendum A acceptance.

Round-trips a dummy provider end-to-end through the real CLI:
  add -> route set -> remove (refused while chained) -> unroute -> remove.
Also: duplicate add refused; `provider test` with a missing key fails
cleanly (exit 1, no traceback, entry stays registered).
The real providers.json is backed up and restored no matter what.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent
ROOT = STUDIO_DIR.parent
CLI = STUDIO_DIR / "cli.py"
PROVIDERS = STUDIO_DIR / "providers.json"

FAILED = []


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def check(label: str, cond: bool, detail: str = "") -> None:
    print(
        f"  {'PASS' if cond else 'FAIL'}  {label}"
        + (f"  ({detail})" if detail and not cond else "")
    )
    if not cond:
        FAILED.append(label)


def main() -> int:
    backup = PROVIDERS.read_text(encoding="utf-8")
    try:
        print("=== provider CLI round-trip ===")

        r = run("provider", "list")
        check("provider list exits 0", r.returncode == 0, r.stderr[-300:])
        check(
            "list prints key presence only", "set" in r.stdout or "MISSING" in r.stdout
        )

        r = run(
            "provider",
            "add",
            "dummy-local",
            "--env-key",
            "DUMMY_LOCAL_KEY",
            "--base-url",
            "http://localhost:9999/v1",
            "--model",
            "dummy-7b",
            "--family",
            "openai",
            "--tier",
            "free",
            "--price-in",
            "0",
            "--price-out",
            "0",
            "--free",
        )
        check("provider add exits 0", r.returncode == 0, r.stderr[-300:])
        entry = json.loads(PROVIDERS.read_text(encoding="utf-8"))["providers"].get(
            "dummy-local"
        )
        check(
            "entry persisted with family",
            entry is not None and entry.get("family") == "openai",
        )

        r = run(
            "provider",
            "add",
            "dummy-local",
            "--env-key",
            "DUMMY_LOCAL_KEY",
            "--base-url",
            "http://localhost:9999/v1",
            "--model",
            "dummy-7b",
            "--family",
            "openai",
            "--tier",
            "free",
            "--price-in",
            "0",
            "--price-out",
            "0",
        )
        check(
            "duplicate add refused", r.returncode != 0 and "already exists" in r.stdout
        )

        r = run("provider", "test", "dummy-local")
        check(
            "test w/o key fails clean (exit 1, no crash)",
            r.returncode == 1 and "FAIL" in r.stdout and "Traceback" not in r.stderr,
            (r.stdout + r.stderr)[-300:],
        )

        r = run("route", "set", "triage", "dummy-local")
        check("route set exits 0", r.returncode == 0, r.stderr[-300:])
        chain = json.loads(PROVIDERS.read_text(encoding="utf-8"))["roles"]["triage"][
            "chain"
        ]
        check("chain replaced", chain == ["dummy-local"])

        r = run("provider", "remove", "dummy-local")
        check(
            "remove refused while chained",
            r.returncode != 0 and "triage" in r.stdout,
            r.stdout[-200:],
        )

        r = run("route", "set", "triage", "groq-free-8b")
        check("route restored", r.returncode == 0)

        r = run("provider", "remove", "dummy-local")
        check("remove succeeds after unroute", r.returncode == 0, r.stdout[-200:])
        gone = (
            "dummy-local"
            not in json.loads(PROVIDERS.read_text(encoding="utf-8"))["providers"]
        )
        check("entry gone", gone)

        r = run("route", "set", "triage", "no-such-provider")
        check("route set refuses unknown provider", r.returncode != 0)

        # Keyless preset path (litellm — no server probe, CI-safe): preset
        # auto-fills, entry needs no env key, remove succeeds unchained.
        r = run("provider", "add", "litellm", "--model", "dummy-7b")
        check("keyless preset add exits 0", r.returncode == 0, (r.stdout + r.stderr)[-300:])
        entry = json.loads(PROVIDERS.read_text(encoding="utf-8"))["providers"].get(
            "litellm"
        )
        check(
            "keyless entry has empty env_key and free=true",
            entry is not None and entry.get("env_key") == "" and entry.get("free") is True,
        )
        r = run("provider", "remove", "litellm")
        check("keyless remove succeeds", r.returncode == 0, r.stdout[-200:])
    finally:
        PROVIDERS.write_text(backup, encoding="utf-8")

    restored = json.loads(PROVIDERS.read_text(encoding="utf-8"))
    check("providers.json restored", "dummy-local" not in restored["providers"])

    if FAILED:
        print(f"\n{len(FAILED)} FAILURES: {FAILED}")
        return 1
    print("\nall provider CLI checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
