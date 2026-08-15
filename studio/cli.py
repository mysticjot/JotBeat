#!/usr/bin/env python3
"""JotBeat CLI — the studio control surface.

Commands:
    init      generate the JotBeat tree from templates (Phase 0)
    brief     "..." -> director drafts GDD + milestone plan
    plan      parse docs/BACKLOG.md into state/task-queue.json
    run-next  run the orchestrator graph over ready backlog items
    verify    deterministic BVT + scripted QA (no model calls)
    report    ledger cost report (per role, per provider, per verified task)
    provider  list / add / remove / test provider entries
    route     set a role's provider chain
    keys      set / list / remove .env keys (masked input, atomic, guarded)
    ui        local settings panel (keys, providers, routing) at 127.0.0.1

Adding a provider (3 steps — never hand-edit JSON, never print key values):
    1. put the key in .env          (e.g. MYPROVIDER_API_KEY=...)
    2. jotbeat provider add --name NAME --env-key MYPROVIDER_API_KEY \
         --base-url https://... --model MODEL --family openai \
         --tier free --price-in 0 --price-out 0 --free
    3. jotbeat route set ROLE NAME [FALLBACK...]

Usage: python studio/cli.py <command>  (run from the repo root;
the studio/ dir is added to sys.path automatically)
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent
ROOT = STUDIO_DIR.parent
TEMPLATES_DIR = STUDIO_DIR / "templates"

if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))


def load_env() -> None:
    """Populate os.environ from .env (never committed). Keys only live here."""
    import os

    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            value = value.split(" #", 1)[0].strip()
            if value:
                os.environ.setdefault(key.strip(), value)


# ---------------------------------------------------------------- init (Phase 0)

# Directories that make up the JotBeat tree (roadmap §4). Files are copied
# from studio/templates/; directories are created even when empty.
DIRECTORIES = [
    "game",
    "game/src/scenes",
    "game/src/entities",
    "game/src/systems",
    "game/assets/sprites",
    "game/assets/tiles",
    "game/assets/audio",
    "game/maps",
    "game/tests",
    "studio/roles",
    "studio/tools",
    "studio/prompts",
    "docs",
    "state",
    "artifacts/screenshots",
    "artifacts/audio",
    "artifacts/builds",
    "artifacts/traces",
    "reports/bvt",
    "reports/regression",
    "reports/cert",
    "reports/triage",
    ".github/workflows",
]

# Files that must exist after init but have no template content.
EMPTY_FILES = [
    "state/events.jsonl",  # append-only ledger; starts empty
]


def init_tree(root: Path, force: bool = False) -> tuple[list[str], list[str]]:
    """Materialize the JotBeat tree from studio/templates into `root`.

    Returns (created, skipped). Existing files are never overwritten
    unless force=True.
    """
    if not TEMPLATES_DIR.is_dir():
        raise SystemExit(f"templates dir missing: {TEMPLATES_DIR}")

    created: list[str] = []
    skipped: list[str] = []

    for rel in DIRECTORIES:
        (root / rel).mkdir(parents=True, exist_ok=True)

    for rel in EMPTY_FILES:
        target = root / rel
        if not target.exists():
            target.touch()
            created.append(rel)

    for template in sorted(TEMPLATES_DIR.rglob("*")):
        if not template.is_file():
            continue
        rel = template.relative_to(TEMPLATES_DIR)
        target = root / rel
        if target.exists() and not force:
            skipped.append(str(rel))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(template, target)
        created.append(str(rel))

    # Git does not track empty directories — keep the tree intact in clones.
    for rel in DIRECTORIES:
        d = root / rel
        if not any(d.iterdir()):
            (d / ".gitkeep").touch()
            created.append(f"{rel}/.gitkeep")

    # Local .env from the committed scaffold (never tracked by git).
    env_file = root / ".env"
    env_example = root / ".env.example"
    if env_example.exists() and (force or not env_file.exists()):
        shutil.copyfile(env_example, env_file)
        created.append(".env")

    return created, skipped


# ---------------------------------------------------------------- Phase 2 commands


def cmd_brief(text: str) -> int:
    """Director drafts a GDD + milestone plan from a one-line pitch."""
    import roles

    task = {
        "id": f"brief-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "role": "director",
        "status": "IN_DEVELOPMENT",
        "acceptance_ids": [],
        "depends_on": [],
        "title": text[:80],
    }
    result = roles.dispatch(task)

    out_dir = ROOT / "docs" / "briefs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{task['id']}.md"
    out_file.write_text(
        f"# Brief: {text}\n\n## Director draft\n\n{result['notes']}\n",
        encoding="utf-8",
    )
    print(f"brief saved -> {out_file.relative_to(ROOT)}")
    print(result["notes"])
    return 0


BL_RE = re.compile(
    r"^### (BL-\d+): (.+?)\n"
    r"(?P<body>.*?)(?=^### |\Z)",
    re.MULTILINE | re.DOTALL,
)


def cmd_plan() -> int:
    """Parse docs/BACKLOG.md items into the task queue."""
    import state

    backlog_file = ROOT / "docs" / "BACKLOG.md"
    if not backlog_file.exists():
        print("docs/BACKLOG.md missing — nothing to plan")
        return 1

    items = []
    for m in BL_RE.finditer(backlog_file.read_text(encoding="utf-8")):
        body = m.group("body")
        role_m = re.search(r"^Role: (\w+)", body, re.MULTILINE)
        acs_m = re.search(r"^ACs: (.+)$", body, re.MULTILINE)
        dep_m = re.search(r"^Depends on: (.+)$", body, re.MULTILINE)
        status_m = re.search(r"^Status: (\w+)", body, re.MULTILINE)
        acs = re.findall(r"AC-\d+", acs_m.group(1)) if acs_m else []
        deps = (
            []
            if not dep_m or dep_m.group(1).strip() == "none"
            else re.findall(r"BL-\d+", dep_m.group(1))
        )
        items.append(
            {
                "id": m.group(1),
                "title": m.group(2).strip(),
                "role": role_m.group(1) if role_m else "coder",
                "status": status_m.group(1) if status_m else "BACKLOG",
                "acceptance_ids": acs,
                "depends_on": deps,
                "attempts": 0,
                "escalation_level": 0,
                "artifacts": [],
            }
        )

    state.save_task_queue({"schema_version": 2, "items": items})
    print(f"planned {len(items)} backlog items -> state/task-queue.json")
    for i in items:
        print(f"  {i['id']:<8} [{i['role']:<9}] {i['status']:<9} {i['title']}")
    return 0


def cmd_run_next() -> int:
    """Run the orchestrator graph over the ready backlog."""
    import orchestrator

    orchestrator.run()
    return 0


def cmd_verify() -> int:
    """Deterministic verification only — no model calls."""
    import json
    from tools.browser import run_ac_suite
    from tools.shell import run_bvt

    build = run_bvt()
    print(f"BVT:     {'PASS' if build['passed'] else 'FAIL'}  steps={build['steps']}")
    qa = run_ac_suite([])
    print(f"QA:      {'PASS' if qa['passed'] else 'FAIL'}  tests={qa['tests']}")
    if not build["passed"]:
        print("--- build log tail ---")
        print(build["log_tail"])
    if not qa["passed"]:
        print("--- qa log tail ---")
        print(qa["log_tail"])
    print(json.dumps({"bvt": build["passed"], "qa": qa["passed"]}))
    return 0 if build["passed"] and qa["passed"] else 1


def cmd_report() -> int:
    """Ledger cost report — cost per role, provider, verified task."""
    import json
    from ledger import cost_report

    print(json.dumps(cost_report(), indent=2))
    return 0


# ------------------------------------------------------- provider management
# (Phase 3, HANDOFF-PHASE3 Addendum A — full model agnosticism:
#  key in .env -> `provider add` -> `route set`. Never hand-edit JSON,
#  never print key values — presence only. All writes go through
#  tools/routing.py, the same module the settings UI uses.)


def _save_routing(routing: dict) -> None:
    import models
    from tools import routing as routing_mod

    routing_mod.save(routing, models.PROVIDERS_FILE)


def cmd_provider_list() -> int:
    import os
    import models
    from tools.routing import roles_using

    routing = models.load_routing()
    print(f"{'name':<28} {'tier':<10} {'family':<8} {'model':<34} {'roles':<22} key")
    for name, p in routing["providers"].items():
        roles = ",".join(roles_using(routing, name)) or "-"
        key = "set" if os.environ.get(p["env_key"]) else "MISSING"
        verified = "" if p.get("verified") else " (unverified)"
        print(
            f"{name:<28} {p.get('tier', '?'):<10} {p.get('family', '?'):<8} "
            f"{p.get('model', '?'):<34} {roles:<22} {key}{verified}"
        )
    return 0


def _parse_headers(pairs: list[str] | None) -> dict:
    """Parse repeated --header KEY=VALUE flags into a dict."""
    headers = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit(f"bad --header {pair!r} — expected KEY=VALUE")
        k, _, v = pair.partition("=")
        headers[k.strip()] = v.strip()
    return headers


def cmd_provider_add(args) -> int:
    import models
    from tools import routing as routing_mod

    routing = models.load_routing()
    try:
        entry = routing_mod.build_entry(
            name=args.name,
            env_key=args.env_key,
            base_url=args.base_url or None,
            model=args.model,
            family=args.family,
            tier=args.tier,
            price_in=args.price_in,
            price_out=args.price_out,
            price_cached_in=args.price_cached_in,
            free=args.free,
            headers=_parse_headers(args.header),
        )
        routing_mod.add_provider(routing, entry)
    except routing_mod.RoutingError as e:
        print(f"refused: {e}")
        return 1

    _save_routing(routing)
    print(f"added provider '{entry['name']}' (family={args.family}, tier={args.tier})")
    print(
        f"next: `jotbeat keys set {entry['env_key']}`, then `jotbeat provider test "
        f"{entry['name']}`, then `jotbeat route set ROLE {entry['name']} ...`"
    )
    return 0


def cmd_provider_remove(name: str) -> int:
    import models
    from tools import routing as routing_mod

    routing = models.load_routing()
    try:
        routing_mod.remove_provider(routing, name)
    except routing_mod.RoutingError as e:
        print(f"refused: {e}")
        return 1
    _save_routing(routing)
    print(f"removed provider '{name}'")
    return 0


def cmd_provider_test(name: str) -> int:
    import models

    routing = models.load_routing()
    if name not in routing["providers"]:
        print(f"unknown provider: {name}")
        return 1

    result = models.ping_provider(name)
    if result["ok"]:
        routing["providers"][name]["verified"] = True
        _save_routing(routing)
        print(
            f"OK   {name}  latency={result['latency_ms']}ms "
            f"tokens_in={result['tokens_in']} tokens_out={result['tokens_out']}"
        )
        return 0
    print(f"FAIL {name}  {result['error']}")
    print("entry stays registered but unverified — the loop never crashes on this")
    return 1


def cmd_route_set(role: str, chain: list[str]) -> int:
    import models
    from tools import routing as routing_mod

    routing = models.load_routing()
    try:
        warnings = routing_mod.set_role_chain(routing, role, chain)
    except routing_mod.RoutingError as e:
        print(f"refused: {e}")
        return 1
    _save_routing(routing)
    for w in warnings:
        print(f"warning: {w}")
    print(f"route set: {role} -> {' -> '.join(chain)}")
    return 0


# ------------------------------------------------------- keys (Addendum B)
# The human never edits .env by hand. Masked input, atomic writes,
# git-ignore guard — all enforced in tools/keys.py (shared with the UI).


def cmd_keys_set(name: str) -> int:
    import getpass
    from tools.keys import KeysError, set_key

    value = getpass.getpass(f"{name} (input hidden): ")
    try:
        n = set_key(ROOT, name, value)
    except KeysError as e:
        print(e)
        return 1
    print(f"{name.strip()} set ({n} chars)")
    return 0


def cmd_keys_list() -> int:
    import models
    from tools.keys import key_status

    status = key_status(ROOT, models.load_routing())
    print(f"{'key':<24} {'needed by':<44} status")
    for row in status["expected"]:
        s = f"set ({row['chars']} chars)" if row["set"] else "MISSING"
        print(f"{row['name']:<24} {','.join(row['providers']):<44} {s}")
    if status["stale"]:
        print("stale (no provider references them): " + ", ".join(status["stale"]))
    return 0


def cmd_keys_remove(name: str) -> int:
    from tools.keys import KeysError, remove_key

    try:
        removed = remove_key(ROOT, name)
    except KeysError as e:
        print(e)
        return 1
    print(f"{name.strip()} {'removed' if removed else 'was not set'}")
    return 0


# ------------------------------------------------------- settings UI (Addendum C)


def cmd_ui() -> int:
    from tools.ui_server import serve

    serve(ROOT)
    return 0


# ------------------------------------------------------- quality gate (AGENTS.md §6)


def cmd_quality() -> int:
    from tools.quality import run_quality

    return run_quality(ROOT)


def main(argv: list[str] | None = None) -> int:
    load_env()

    from tools.routing import PROVIDER_FAMILIES, PROVIDER_TIERS

    parser = argparse.ArgumentParser(prog="jotbeat", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="generate the JotBeat tree from templates")
    p_init.add_argument("--path", default=".", help="target directory (default: cwd)")
    p_init.add_argument("--force", action="store_true", help="overwrite existing files")

    p_brief = sub.add_parser("brief", help="director drafts GDD + milestone plan")
    p_brief.add_argument("text", help="the pitch")

    sub.add_parser("plan", help="parse docs/BACKLOG.md into the task queue")
    sub.add_parser("run-next", help="run the orchestrator over ready tasks")
    sub.add_parser("verify", help="deterministic BVT + scripted QA (no models)")
    sub.add_parser("report", help="ledger cost report")

    p_prov = sub.add_parser(
        "provider",
        help="manage providers (key in .env -> provider add -> route set)",
        description="Add flow: 1) key in .env  2) provider add  3) route set. "
        "Key values are never printed — presence only.",
    )
    prov_sub = p_prov.add_subparsers(dest="provider_command", required=True)

    prov_sub.add_parser(
        "list", help="name, tier, family, model, roles, key set/missing"
    )

    p_add = prov_sub.add_parser(
        "add",
        help="register a new provider entry",
        epilog="UNIVERSAL COMPATIBILITY RULE: almost everything is family "
        "'openai'. For APIs that aren't OpenAI-compatible, do NOT ask "
        "for per-vendor code — run a local LiteLLM proxy and point a "
        "family-openai entry at http://localhost:4000/v1.",
    )
    p_add.add_argument("--name", required=True)
    p_add.add_argument(
        "--env-key", required=True, help="env var NAME (never the value)"
    )
    p_add.add_argument("--base-url", default="", help="required for family=openai")
    p_add.add_argument("--model", required=True)
    p_add.add_argument("--family", required=True, choices=PROVIDER_FAMILIES)
    p_add.add_argument("--tier", required=True, choices=PROVIDER_TIERS)
    p_add.add_argument("--price-in", required=True, type=float)
    p_add.add_argument("--price-out", required=True, type=float)
    p_add.add_argument("--price-cached-in", type=float, default=None)
    p_add.add_argument("--free", action="store_true")
    p_add.add_argument(
        "--header",
        action="append",
        metavar="KEY=VALUE",
        help="extra request header; repeatable — covers api-key "
        "auth styles, referers, any provider quirk",
    )

    p_rm = prov_sub.add_parser("remove", help="remove a provider (refuses if chained)")
    p_rm.add_argument("name")

    p_test = prov_sub.add_parser("test", help="minimal live ping, ledgered")
    p_test.add_argument("name")

    p_route = sub.add_parser("route", help="role routing")
    route_sub = p_route.add_subparsers(dest="route_command", required=True)
    p_rset = route_sub.add_parser("set", help="replace a role's provider chain")
    p_rset.add_argument("role")
    p_rset.add_argument("providers", nargs="+")

    p_keys = sub.add_parser(
        "keys", help="manage .env keys (masked, atomic, git-ignore guarded)"
    )
    keys_sub = p_keys.add_subparsers(dest="keys_command", required=True)
    p_kset = keys_sub.add_parser("set", help="set a key with masked input")
    p_kset.add_argument("name")
    keys_sub.add_parser("list", help="expected keys, set/missing, char counts, stale")
    p_krm = keys_sub.add_parser("remove", help="remove a key from .env")
    p_krm.add_argument("name")

    sub.add_parser("ui", help="local settings UI (keys, providers, routing)")
    sub.add_parser(
        "quality",
        help="post-coding quality gate: aislop (errors=0) + fallow dead-code/dupes",
    )

    args = parser.parse_args(argv)

    if args.command == "init":
        root = Path(args.path).resolve()
        created, skipped = init_tree(root, force=args.force)
        print(f"jotbeat init -> {root}")
        print(f"  created/updated: {len(created)}")
        for rel in created:
            print(f"    + {rel}")
        if skipped:
            print(f"  kept existing (use --force to overwrite): {len(skipped)}")
            for rel in skipped:
                print(f"    = {rel}")
        return 0

    if args.command == "brief":
        return cmd_brief(args.text)
    if args.command == "plan":
        return cmd_plan()
    if args.command == "run-next":
        return cmd_run_next()
    if args.command == "verify":
        return cmd_verify()
    if args.command == "report":
        return cmd_report()
    if args.command == "provider":
        if args.provider_command == "list":
            return cmd_provider_list()
        if args.provider_command == "add":
            return cmd_provider_add(args)
        if args.provider_command == "remove":
            return cmd_provider_remove(args.name)
        if args.provider_command == "test":
            return cmd_provider_test(args.name)
    if args.command == "route" and args.route_command == "set":
        return cmd_route_set(args.role, args.providers)
    if args.command == "keys":
        if args.keys_command == "set":
            return cmd_keys_set(args.name)
        if args.keys_command == "list":
            return cmd_keys_list()
        if args.keys_command == "remove":
            return cmd_keys_remove(args.name)
    if args.command == "ui":
        return cmd_ui()
    if args.command == "quality":
        return cmd_quality()

    return 1


if __name__ == "__main__":
    sys.exit(main())
