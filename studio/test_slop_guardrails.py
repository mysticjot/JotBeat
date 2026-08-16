#!/usr/bin/env python3
"""test_slop_guardrails.py — Creative Director anti-slop directive (2026-08-16).

1. A known-slop string fails the mechanical check (binary contrast).
2. A NARRATIVE_BIBLE voice-guide line passes on its own merits.
3. The vendored pattern file is non-empty (phrases + structural patterns).
4. The canon exemption holds: the verbatim reveal line matches the
   binary-contrast regex but MUST pass because the bible fixes it verbatim —
   the auditor must never kick back canon.
"""

from __future__ import annotations

import sys
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(STUDIO_DIR))

from tools.slop import check_string, load_patterns  # noqa: E402

FAILED = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(label)


def main() -> int:
    print("=== slop guardrails ===")

    hits = check_string("It's not a door. It's a threshold.")
    check(
        "known-slop string fails (binary contrast)",
        any(h["pattern"] == "binary-contrast" for h in hits),
        f"findings: {hits}",
    )

    hits = check_string("The lungstone is quiet.")
    check("voice-guide line passes on its merits", hits == [], f"findings: {hits}")

    pats = load_patterns()
    check(
        "pattern file non-empty",
        bool(pats["banned_phrases"]) and bool(pats["structural_patterns"]),
    )

    hits = check_string("The door you opened wasn't the exit. It was the lock.")
    check("canon reveal line exempt (bible-verbatim)", hits == [], f"findings: {hits}")

    if FAILED:
        print(f"\n{len(FAILED)} FAILURES: {FAILED}")
        return 1
    print("\nall slop guardrail checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
