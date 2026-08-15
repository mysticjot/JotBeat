#!/usr/bin/env python3
"""JotBeat CLI — the studio control surface.

Commands:
    init      generate the JotBeat tree from templates (Phase 0)
    brief     "..." -> director drafts GDD + milestone plan
    plan      parse docs/BACKLOG.md into state/task-queue.json
    run-next  run the orchestrator graph over ready backlog items
    verify    deterministic BVT + scripted QA (no model calls)
    report    ledger cost report (per role, per provider, per verified task)

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
        f"# Brief: {text}\n\n"
        f"## Director draft\n\n{result['notes']}\n",
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
        deps = [] if not dep_m or dep_m.group(1).strip() == "none" else re.findall(r"BL-\d+", dep_m.group(1))
        items.append({
            "id": m.group(1),
            "title": m.group(2).strip(),
            "role": role_m.group(1) if role_m else "coder",
            "status": status_m.group(1) if status_m else "BACKLOG",
            "acceptance_ids": acs,
            "depends_on": deps,
            "attempts": 0,
            "escalation_level": 0,
            "artifacts": [],
        })

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


def main(argv: list[str] | None = None) -> int:
    load_env()

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

    return 1


if __name__ == "__main__":
    sys.exit(main())
