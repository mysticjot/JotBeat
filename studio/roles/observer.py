"""roles/observer.py — the AI observer (HANDOFF-PHASE4 §2.3).

On a scripted-QA failure, the vision chain (glm-4.6v-flash -> glm-4.6v) gets
the failure screenshot + state digest and returns:
  - classification: layout | logic | timing | harness
  - hypothesis: one paragraph — what likely broke and why
  - proposals: 0-2 edge-case scenario candidates

The classification + hypothesis feed the kickback evidence (the retrying role
sees them; the auditor still never sees role_notes). Proposals are filed to
docs/BACKLOG.md marked PROPOSED — never auto-queued; the human approves
additions. The observer is advisory: it NEVER blocks the loop, and any
observer failure degrades to "no observer input" (the loop ran fine without
it for all of Phase 3).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKLOG = ROOT / "docs" / "BACKLOG.md"

INSTRUCTIONS = """You are the JotBeat QA observer. A scripted Playwright acceptance test just \
failed against the deterministic debug hook (window.__game.state). You receive a \
state digest (test error + final game state) and, when available, the failure \
screenshot.

Classify the failure into EXACTLY ONE of:
- layout   — visual/viewport problem (cropping, overlap, off-screen element)
- logic    — game rules wrong (door opens without key, inventory miscount, wrong scene)
- timing   — race/animation/frame-timing issue, likely flaky under load
- harness  — the test/scaffold is wrong, not the game (bad selector, bad route, stale server)

Then ONE paragraph hypothesis: what broke, why, and the first thing to check.
Optionally propose up to 2 edge-case scenarios worth adding to the backlog
(empty list if none).

Return ONLY a JSON object:
{"classification": "layout|logic|timing|harness",
 "hypothesis": "...",
 "proposals": ["...", "..."]}"""

PROPOSED_HEADER = "## Proposed (observer candidates — awaiting human approval)"


def classify_failure(
    task_id: str, state_digest: str, screenshot: str | None = None
) -> dict:
    """Vision-classify one QA failure. Returns
    {"classification", "hypothesis", "proposals": [...]}."""
    from models import ModelAdapter

    adapter = ModelAdapter("vision")
    images = [screenshot] if screenshot else []
    text = adapter.complete(
        INSTRUCTIONS,
        [f"State digest:\n{state_digest}"],
        task_id,
        output_schema={"type": "json_object"},
        images=images,
    )
    m = re.search(r"\{.*\}", text, re.DOTALL)
    data = json.loads(m.group(0)) if m else {}
    classification = str(data.get("classification", "")).lower()
    if classification not in ("layout", "logic", "timing", "harness"):
        classification = "harness"  # unknown -> suspect the harness, not the game
    proposals = [str(p)[:200] for p in data.get("proposals", [])][:2]
    return {
        "classification": classification,
        "hypothesis": str(data.get("hypothesis", ""))[:800],
        "proposals": proposals,
    }


def file_proposals(proposals: list[str]) -> int:
    """Append observer edge-case candidates to BACKLOG.md marked PROPOSED.
    Deduped against existing text; never queued into task-queue.json.
    Returns the count actually filed."""
    if not proposals:
        return 0
    text = BACKLOG.read_text(encoding="utf-8") if BACKLOG.exists() else "# Backlog\n"
    if PROPOSED_HEADER not in text:
        text = text.rstrip() + f"\n\n{PROPOSED_HEADER}\n"
    filed = 0
    for p in proposals:
        key = p.strip().lower()[:60]
        if key and key not in text.lower():
            text = text.rstrip() + f"\n- [ ] PROPOSED: {p.strip()}\n"
            filed += 1
    if filed:
        BACKLOG.write_text(text, encoding="utf-8")
    return filed
