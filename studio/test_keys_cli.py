#!/usr/bin/env python3
"""test_keys_cli.py — Phase 3 Addendum B acceptance.

Round-trip: set a dummy var -> list shows it set with correct char count ->
remove clears it. Uses a TEMP git repo + temp .env (never the real one).
Also: the git-ignore guard fails closed (no repo / not ignored -> refusal),
stale detection works, and the CLI `keys list` wiring responds.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent
ROOT = STUDIO_DIR.parent
sys.path.insert(0, str(STUDIO_DIR))

from tools.keys import KeysError, key_status, remove_key, set_key  # noqa: E402

FAILED = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(label)


def make_repo(with_gitignore: bool) -> Path:
    root = Path(tempfile.mkdtemp(prefix="jotbeat-keys-"))
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    if with_gitignore:
        (root / ".gitignore").write_text(".env\n", encoding="utf-8")
    return root


def main() -> int:
    routing = json.loads((STUDIO_DIR / "providers.json").read_text(encoding="utf-8"))

    print("=== keys round-trip (temp repo) ===")
    repo = make_repo(with_gitignore=True)

    n = set_key(repo, "DUMMY_TEST_KEY", "  abc123xyz  ")  # whitespace stripped
    check("set_key returns char count", n == 9)
    env_text = (repo / ".env").read_text(encoding="utf-8")
    check("value written stripped", "DUMMY_TEST_KEY=abc123xyz" in env_text)

    st = key_status(repo, routing)
    row = next(r for r in st["expected"] if r["name"] == "GROQ_API_KEY")
    check("missing expected key shows MISSING", not row["set"] and row["chars"] == 0)
    check("dummy key flagged stale", "DUMMY_TEST_KEY" in st["stale"])

    n = set_key(repo, "DUMMY_TEST_KEY", "replaced-value")
    check("update in place (no dup)",
          env_text.count("DUMMY_TEST_KEY") == 0 or
          (repo / ".env").read_text(encoding="utf-8").count("DUMMY_TEST_KEY") == 1)

    removed = remove_key(repo, "DUMMY_TEST_KEY")
    check("remove_key clears the line", removed and "DUMMY_TEST_KEY"
          not in (repo / ".env").read_text(encoding="utf-8"))
    check("remove missing key is a no-op", remove_key(repo, "NOPE") is False)

    print("=== guard fails closed ===")
    bare = Path(tempfile.mkdtemp(prefix="jotbeat-nogit-"))
    try:
        set_key(bare, "X", "y")
        check("refuses without git repo", False)
    except KeysError:
        check("refuses without git repo", True)

    repo2 = make_repo(with_gitignore=False)
    try:
        set_key(repo2, "X", "y")
        check("refuses when .env not ignored", False)
    except KeysError:
        check("refuses when .env not ignored", True)
    check("no .env written on refusal", not (repo2 / ".env").exists())

    try:
        set_key(repo, "EMPTY_KEY", "   ")
        check("refuses empty value", False)
    except KeysError:
        check("refuses empty value", True)

    print("=== comments/unrelated lines preserved ===")
    (repo / ".env").write_text("# my comment\nUNRELATED=keepme\n", encoding="utf-8")
    set_key(repo, "DUMMY_TEST_KEY", "v1")
    text = (repo / ".env").read_text(encoding="utf-8")
    check("comment preserved", "# my comment" in text)
    check("unrelated line preserved", "UNRELATED=keepme" in text)

    print("=== CLI wiring ===")
    r = subprocess.run([sys.executable, str(STUDIO_DIR / "cli.py"), "keys", "list"],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    check("keys list exits 0", r.returncode == 0, r.stderr[-300:])
    check("lists derived key names", "GROQ_API_KEY" in r.stdout and "ZAI_API_KEY" in r.stdout)

    if FAILED:
        print(f"\n{len(FAILED)} FAILURES: {FAILED}")
        return 1
    print("\nall keys CLI checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
