#!/usr/bin/env python3
"""JotBeat CLI — the studio control surface.

Phase 0 scope: `init` only. Later commands (brief, plan, run-next, verify,
report) arrive with the orchestrator core in Phase 2 (roadmap §16.4).

Usage:
    python studio/cli.py init [--path DIR] [--force]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = STUDIO_DIR / "templates"

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jotbeat", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="generate the JotBeat tree from templates")
    p_init.add_argument("--path", default=".", help="target directory (default: cwd)")
    p_init.add_argument("--force", action="store_true", help="overwrite existing files")

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

    return 1


if __name__ == "__main__":
    sys.exit(main())
