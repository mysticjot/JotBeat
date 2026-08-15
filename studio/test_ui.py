#!/usr/bin/env python3
"""test_ui.py — Phase 3 Addendum C acceptance.

Boots the settings UI on a temp repo (git init + .env git-ignored) with a
temp copy of providers.json, then drives the HTTP endpoints end-to-end:
  set key -> .env updated -> add provider -> providers.json updated ->
  route set -> routing updated.
Asserts: stdlib-only boot, loopback binding + guard, and that NO response
body ever contains the planted secret value.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent
ROOT = STUDIO_DIR.parent
sys.path.insert(0, str(STUDIO_DIR))

FAILED = []
SECRET = "unit-test-secret-value-9f8e7d"


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(label)


def main() -> int:
    import models
    from tools import ui_server

    repo = Path(tempfile.mkdtemp(prefix="jotbeat-ui-"))
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    providers_copy = repo / "providers.json"
    shutil.copyfile(STUDIO_DIR / "providers.json", providers_copy)

    real_file = models.PROVIDERS_FILE
    models.PROVIDERS_FILE = providers_copy  # point the shared reader at the temp copy

    httpd = ui_server.make_server(repo)
    port = httpd.server_address[1]
    base = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    bodies: list[str] = []

    def get(path: str) -> tuple[int, dict | str]:
        with urllib.request.urlopen(base + path, timeout=10) as r:
            raw = r.read().decode("utf-8")
            bodies.append(raw)
            return r.status, raw

    def post(path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            base + path, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read().decode("utf-8")
                bodies.append(raw)
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            bodies.append(raw)
            return json.loads(raw)

    try:
        print("=== boot & binding ===")
        check("bound to loopback", httpd.server_address[0] == "127.0.0.1")
        check("loopback guard accepts 127.0.0.1", ui_server.is_loopback("127.0.0.1"))
        check("loopback guard refuses remote", not ui_server.is_loopback("10.0.0.5"))

        status, html = get("/")
        check("page serves", status == 200 and "JotBeat Studio" in html)
        check("onclick handlers well-formed (no terminated-string regression)",
              "saveKey(''" not in html and "saveKey(" in html)

        print("=== endpoint round-trip ===")
        r = post("/api/keys/set", {"name": "DUMMY_UI_KEY", "value": SECRET})
        check("keys set ok with char count", r.get("ok") and r.get("chars") == len(SECRET))
        check(".env written", SECRET in (repo / ".env").read_text(encoding="utf-8"))

        _, state_raw = get("/api/state")
        state = json.loads(state_raw)
        row = next(x for x in state["keys"] if x["name"] == "GROQ_API_KEY")
        check("state lists expected keys", "providers" in row and isinstance(row["set"], bool))
        check("ui key visible as stale", "DUMMY_UI_KEY" in state["stale_keys"])

        r = post("/api/providers/add", {
            "name": "dummy-ui", "env_key": "DUMMY_UI_KEY",
            "base_url": "http://localhost:9999/v1", "model": "dummy-7b",
            "family": "openai", "tier": "free",
            "price_in": 0, "price_out": 0, "free": True,
            "headers": {"X-Custom": "$DUMMY_UI_KEY"},
        })
        check("providers add ok", r.get("ok"), str(r))
        saved = json.loads(providers_copy.read_text(encoding="utf-8"))
        check("provider persisted with headers",
              saved["providers"]["dummy-ui"]["headers"] == {"X-Custom": "$DUMMY_UI_KEY"})

        r = post("/api/route/set", {"role": "triage", "primary": "dummy-ui", "fallback": ""})
        check("route set ok", r.get("ok"), str(r))
        saved = json.loads(providers_copy.read_text(encoding="utf-8"))
        check("chain updated", saved["roles"]["triage"]["chain"] == ["dummy-ui"])

        r = post("/api/providers/remove", {"name": "dummy-ui"})
        check("remove refused while chained", not r.get("ok") and "triage" in r.get("error", ""))

        r = post("/api/providers/test", {"name": "dummy-ui"})
        check("provider test fails clean (no real server)",
              r.get("ok") is False and "error" in r)

        r = post("/api/route/set", {"role": "triage", "primary": "groq-free-8b", "fallback": ""})
        check("route restored", r.get("ok"))
        r = post("/api/providers/remove", {"name": "dummy-ui"})
        check("remove ok after unroute", r.get("ok"))
        r = post("/api/keys/remove", {"name": "DUMMY_UI_KEY"})
        check("keys remove ok", r.get("ok") and r.get("removed"))

        print("=== secrecy ===")
        leaked = any(SECRET in b for b in bodies)
        check("no response body contains the key value", not leaked)
    finally:
        httpd.shutdown()
        httpd.server_close()
        models.PROVIDERS_FILE = real_file

    if FAILED:
        print(f"\n{len(FAILED)} FAILURES: {FAILED}")
        return 1
    print("\nall UI checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
