"""Shared role plumbing: context slice -> ModelAdapter, with an offline stub
when no provider keys are active. Stub calls are ledgered at the head-of-chain
price (free tier = $0.00) so cost math is exercised even without keys."""

from __future__ import annotations

import re
from pathlib import Path

from ledger import log_call
from models import ModelAdapter, active_providers, load_routing

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FILE_MARKER_RE = re.compile(r"^=== FILE: (.+?) ===\s*$", re.MULTILINE)


def apply_artifacts(
    text: str, allowed_prefix: str = "game/"
) -> tuple[list[str], list[str]]:
    """Parse `=== FILE: <path> ===` blocks out of a role's output and write
    them to disk. Returns (written repo-relative paths, refused paths).

    Paths may be emitted repo-relative ("game/src/x.ts") or relative to the
    allowed root ("src/x.ts") — both normalize to the same target. Loudly
    refuses (skips, never crashes the graph) absolute paths, `..`, and
    anything that escapes the allowed prefix."""
    parts = FILE_MARKER_RE.split(text)  # [pre, path, body, path, body, ...]
    written: list[str] = []
    refused: list[str] = []
    for i in range(1, len(parts) - 1, 2):
        rel = parts[i].strip().strip("`")
        body = parts[i + 1]
        # === END === terminator: anything after it is model prose, not file
        # content (models DO append commentary; without this it gets written
        # into the file — corrupted ac-003 spec, 2026-08-16). Accept the
        # common mutation families too (--- END ---, === END FILE ===).
        end = re.search(
            r"^[=\-]{2,}\s*END(?:\s+FILE)?\s*[=\-]{2,}\s*$", body, re.MULTILINE
        )
        if end:
            body = body[: end.start()]
        # strip a markdown fence if the model wrapped the content anyway
        body = re.sub(r"^\s*```[\w-]*\n", "", body.lstrip("\n"))
        body = re.sub(r"\n```\s*$", "", body.rstrip())
        # Refuse escapes on the RAW path first (absolute in any flavour,
        # `..` traversal), then normalize bare root-relative paths onto
        # the allowed prefix.
        raw = Path(rel)
        if (
            raw.is_absolute()
            or rel.startswith(("/", "\\"))
            or (len(rel) > 1 and rel[1] == ":")
            or ".." in raw.parts
        ):
            refused.append(rel)
            continue
        if not (rel + "/").startswith(allowed_prefix):
            rel = allowed_prefix + rel
        target = REPO_ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body.rstrip() + "\n", encoding="utf-8")
        written.append(rel)
    return written, refused


def context_slice(role: str, task: dict) -> list[str]:
    """Each role receives ONLY its slice (docs/BUDGET.md rationing rules).
    Phase 2 stub slice: the task itself. Phase 3 adds repo maps, doc excerpts."""
    return [
        f"task id: {task['id']}",
        f"acceptance criteria: {', '.join(task.get('acceptance_ids', [])) or 'none'}",
    ]


def run_role(role: str, task: dict, escalation_level: int = 0) -> dict:
    instructions = (
        f"You are the JotBeat {role}. Execute backlog item {task['id']} "
        f"and emit artifacts only — never converse with other agents."
    )
    context = context_slice(role, task)

    if active_providers(role):
        text = ModelAdapter(role).complete(
            instructions,
            context,
            task_id=task["id"],
            escalation_level=escalation_level,
        )
    else:
        # Offline stub: deterministic output, ledgered at chain-head price.
        head = load_routing()["roles"][role]["chain"][0]
        text = (
            f"[stub:{role}] no active providers — recorded placeholder for {task['id']}"
        )
        log_call(
            task_id=task["id"],
            role=role,
            provider=head,
            model=load_routing()["providers"][head]["model"],
            tokens_in=(len(instructions) + sum(len(c) for c in context)) // 4,
            tokens_out=len(text) // 4,
            cached_in=0,
            retry=0,
            escalated=escalation_level > 0,
            latency_ms=0,
        )

    return {"artifacts": [], "notes": text, "instructions": instructions}
