"""Coder role — Phase 3: emits real artifacts via the === FILE: === contract
(studio/prompts/coder.md), applied by _base.apply_artifacts (game/ only)."""

from __future__ import annotations

import re

from models import ModelAdapter, active_providers

from ._base import REPO_ROOT, apply_artifacts, run_role

PROMPT_PATH = REPO_ROOT / "studio" / "prompts" / "coder.md"
GAME = REPO_ROOT / "game"

# Files the coder always sees in full (small, load-bearing).
ALWAYS_INCLUDE = [
    "src/debug.ts",
    "src/game.ts",
    "src/main.ts",
    "src/scenes/Boot.ts",
    "src/scenes/Title.ts",
    "src/scenes/Game.ts",
    "src/entities/Player.ts",
    "tests/smoke.spec.ts",
    "assets/maps/dungeon.json",
    "package.json",
    "index.html",
]

AC_BLOCK_RE = re.compile(r"^## (AC-\d+):.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)


def _ac_prose(acceptance_ids: list[str]) -> str:
    plan_path = REPO_ROOT / "docs" / "TEST_PLAN.md"
    if not plan_path.exists():
        return "(no TEST_PLAN.md found)"
    plan = plan_path.read_text(encoding="utf-8")
    blocks = [
        m.group(0).strip()
        for m in AC_BLOCK_RE.finditer(plan)
        if m.group(1) in acceptance_ids
    ]
    return "\n\n".join(blocks) or "(no matching AC blocks)"


def _context(task: dict) -> list[str]:
    files = sorted(
        str(p.relative_to(GAME))
        for p in GAME.rglob("*")
        if p.is_file()
        and not {"node_modules", "dist", "test-results", ".git"} & set(p.parts)
    )
    parts = [
        f"backlog item: {task['id']}: {task.get('title', '')}",
        f"acceptance criteria:\n{_ac_prose(task.get('acceptance_ids', []))}",
        "repo map (game/):\n" + "\n".join(files),
    ]
    if task.get("_failure"):
        parts.append(
            "PREVIOUS ATTEMPT FAILED — fix this, do not repeat it:\n"
            + task["_failure"]
        )
    for rel in ALWAYS_INCLUDE:
        p = GAME / rel
        if p.exists():
            parts.append(f"--- current {rel} ---\n{p.read_text(encoding='utf-8')}")
    # Kickback retries must see their own previous artifacts or they patch
    # blind: this task's AC spec(s) plus every entity (small greybox files).
    seen = set(ALWAYS_INCLUDE)
    candidates = [
        p
        for p in sorted(GAME.glob("tests/*.spec.ts"))
        if any(ac.lower() in p.name.lower() for ac in task.get("acceptance_ids", []))
    ]
    candidates += sorted(GAME.glob("src/entities/*.ts"))
    for p in candidates:
        rel = str(p.relative_to(GAME))
        if rel not in seen:
            seen.add(rel)
            parts.append(f"--- current {rel} ---\n{p.read_text(encoding='utf-8')}")
    return parts


def run(task: dict, escalation_level: int = 0) -> dict:
    if not active_providers("coder"):
        return run_role("coder", task, escalation_level=escalation_level)

    instructions = PROMPT_PATH.read_text(encoding="utf-8")
    text = ModelAdapter("coder").complete(
        instructions,
        _context(task),
        task_id=task["id"],
        escalation_level=escalation_level,
    )
    artifacts, refused = apply_artifacts(text)
    if not artifacts:
        # Non-conforming emission (prose instead of file blocks): soft-fail
        # so the build/QA gates kick it back with evidence and the role
        # retries — never crash the graph on a model's formatting lapse.
        return {
            "artifacts": [],
            "notes": "emission error: model output contained no === FILE: === blocks"
            + (f"; refused paths: {refused}" if refused else ""),
            "instructions": instructions,
        }
    return {
        "artifacts": artifacts,
        "notes": f"wrote: {', '.join(artifacts)}"
        + (f"; refused paths: {refused}" if refused else ""),
        "instructions": instructions,
    }
