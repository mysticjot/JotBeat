"""Narrative Designer role (Creative Director directive, 2026-08-16 —
activated ahead of Phase 7). Owns docs/NARRATIVE_BIBLE.md and ALL
player-facing text: cards, UI strings, every screen.

Every string passes TWO gates here before it can ship:
  1. mechanical — tools/slop.check_string (zero API cost)
  2. judgment — the narrative model with the slop standard + voice guide
     (slop_patterns.json is appended to its instructions)

dispatch() entry point: run(task). Direct review of the game's current
strings: review_game_strings(task_id).
"""

from __future__ import annotations

import re
from pathlib import Path

from ledger import log_call
from models import ModelAdapter, active_providers, load_routing
from tools.slop import check_string, collect_strings

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"

BLOCK_RE = re.compile(
    r"STRING:\s*(.+?)\s*\n\s*VERDICT:\s*(APPROVED|SLOP|CANON-VIOLATION)"
    r"(?:\s*\n\s*FIX:\s*(.+?))?(?=\s*\n\s*STRING:|\s*\n?\s*```|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def _load_prompts() -> tuple[str, str, str]:
    def read(name: str) -> str:
        p = PROMPTS / name
        return p.read_text(encoding="utf-8") if p.exists() else ""

    bible = (
        Path(__file__).resolve().parent.parent.parent / "docs" / "NARRATIVE_BIBLE.md"
    )
    return (
        read("narrative.md"),
        read("slop-standard.md"),
        bible.read_text(encoding="utf-8") if bible.exists() else "",
    )


def review_strings(strings: list[str], task_id: str = "NARRATIVE-REVIEW") -> dict:
    """Review player-facing strings. Mechanical pass first; anything the
    mechanical pass flags is reported WITHOUT spending a model call (it is
    already dead). Clean strings go to the judgment pass."""
    mechanical = {s: check_string(s) for s in strings}
    flagged = {s: f for s, f in mechanical.items() if f}
    clean = [s for s in strings if not mechanical[s]]

    judgments: dict[str, dict] = {}
    if clean and active_providers("narrative"):
        narrative_prompt, slop_standard, bible = _load_prompts()
        import json

        patterns = json.loads(
            (PROMPTS.parent / "guardrails" / "slop_patterns.json").read_text(
                encoding="utf-8"
            )
        )
        instructions = (
            narrative_prompt
            + "\n\n--- SLOP STANDARD ---\n"
            + slop_standard
            + "\n\n--- MACHINE PATTERN LIST (already applied mechanically; your job "
            "is what it cannot catch — voice, generic fantasy cadence, "
            "'any AI game ever made' test) ---\n"
            + json.dumps(
                {k: patterns[k] for k in ("banned_phrases", "banned_words")}, indent=1
            )
            + "\n--- SCORING RUBRIC ---\n"
            + json.dumps(patterns["scoring_rubric"], indent=1)
        )
        context = [
            "--- NARRATIVE BIBLE (canon + voice guide) ---",
            bible[:4000],
            "--- STRINGS UNDER REVIEW ---",
            *[f"STRING: {s}" for s in clean],
        ]
        text = ModelAdapter("narrative").complete(
            instructions, context, task_id=task_id
        )
        # Parse STRING/VERDICT/FIX blocks; match back to input strings by
        # quoted content so reordering can't silently misassign a verdict.
        by_string: dict[str, dict] = {}
        for m in BLOCK_RE.finditer(text):
            raw = m.group(1).strip().strip('"').strip("'")
            fix = (m.group(3) or "").strip().strip('"').strip("'")
            by_string[raw] = {
                "verdict": m.group(2).upper(),
                **({"fix": fix} if fix and m.group(2).upper() != "APPROVED" else {}),
            }
        for s in clean:
            judgments[s] = (
                by_string.get(s)
                or by_string.get(s.replace("${keys}", "1"))
                or {"verdict": "UNPARSED", "raw_tail": text[-400:]}
            )
    elif clean:
        head = load_routing()["roles"]["narrative"]["chain"][0]
        log_call(
            task_id=task_id,
            role="narrative",
            provider=head,
            model=load_routing()["providers"][head]["model"],
            tokens_in=sum(len(s) for s in clean) // 4,
            tokens_out=8,
            cached_in=0,
            retry=0,
            escalated=False,
            latency_ms=0,
        )
        for s in clean:
            judgments[s] = {"verdict": "UNVERIFIED", "note": "no active providers"}

    return {"mechanical_flags": flagged, "judgments": judgments}


def review_game_strings(task_id: str = "NARRATIVE-REVIEW") -> dict:
    """The standing pass: every player-facing string in game/src."""
    items = collect_strings()
    strings = [i["string"] for i in items]
    result = review_strings(strings, task_id=task_id)
    result["locations"] = {i["string"]: f"{i['file']}:{i['line']}" for i in items}
    return result


def run(task: dict, escalation_level: int = 0) -> dict:
    """dispatch() entry — a backlog item for the narrative role."""
    from roles._base import run_role

    return run_role("narrative", task, escalation_level=escalation_level)
