"""Auditor role — adversarial and independent (roadmap §2.4).

INPUT EXCLUSION IS LOAD-BEARING: audit() receives only the task, the build
digest, and the QA digest. It MUST NOT receive role_notes or any implementer's
self-assessment (HANDOFF-PHASE2.md §6b/§8). Do not add parameters.
"""

from __future__ import annotations

import re

from ledger import log_call
from models import ModelAdapter, active_providers, load_routing

VERDICT_RE = re.compile(
    r"verdict:\s*(MET|FAILED|UNVERIFIED|SKIPPED)", re.IGNORECASE
)
PATCH_RE = re.compile(r"patch:\s*(.+)", re.IGNORECASE | re.DOTALL)

AC_BLOCK_RE = re.compile(r"^## (AC-\d+):.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)


def _ac_prose(acceptance_ids: list[str]) -> str:
    from pathlib import Path

    plan_path = Path(__file__).resolve().parent.parent.parent / "docs" / "TEST_PLAN.md"
    if not plan_path.exists():
        return "(no TEST_PLAN.md)"
    plan = plan_path.read_text(encoding="utf-8")
    blocks = [
        m.group(0).strip()
        for m in AC_BLOCK_RE.finditer(plan)
        if m.group(1) in acceptance_ids
    ]
    return "\n\n".join(blocks) or "(no matching AC blocks)"


def audit(task: dict, build: dict, qa: dict) -> dict:
    """Return {"status": MET|FAILED|UNVERIFIED|SKIPPED, "evidence": [...],
    "patch_instructions": str}."""
    context = [
        f"task id: {task['id']}",
        f"acceptance criteria text:\n{_ac_prose(task.get('acceptance_ids', []))}",
        f"build digest: passed={build.get('passed')} steps={build.get('steps', [])}",
        f"qa digest: passed={qa.get('passed')} tests={qa.get('tests', [])}",
        # Ground truth: without the actual failure output the auditor can only
        # hallucinate patch instructions. Tail-capped to keep context lean.
        f"build log tail:\n{build.get('log_tail', '')[-1200:]}",
        f"qa log tail:\n{qa.get('log_tail', '')[-1500:]}",
    ]
    instructions = (
        "You are the JotBeat Auditor. You never saw the implementer's notes. "
        "Issue a verdict per acceptance criterion from the evidence only. "
        "Reply with EXACTLY this format, in this order:\n"
        "Reasoning: <one or two sentences grounded in the log tails above>\n"
        "Verdict: MET | FAILED | UNVERIFIED | SKIPPED\n"
        "Patch: <concrete fix instructions quoting the failing assertion — "
        "only when FAILED; must be the LAST line(s) of your reply>\n"
        "A verdict of MET requires build passed AND the AC's own scripted "
        "QA test passed. Never invent failure details not in the log tails."
    )

    if active_providers("auditor"):
        text = ModelAdapter("auditor").complete(
            instructions,
            context,
            task_id=task["id"],
        )
        verdict_m = VERDICT_RE.search(text)
        patch_m = PATCH_RE.search(text)
        return {
            "status": verdict_m.group(1).upper() if verdict_m else "UNVERIFIED",
            "evidence": context,
            "patch_instructions": patch_m.group(1).strip() if patch_m else "",
            "model_response": text,
        }

    # Offline stub: an auditor without a model cannot verify — honest UNVERIFIED.
    head = load_routing()["roles"]["auditor"]["chain"][0]
    log_call(
        task_id=task["id"],
        role="auditor",
        provider=head,
        model=load_routing()["providers"][head]["model"],
        tokens_in=(len(instructions) + sum(len(c) for c in context)) // 4,
        tokens_out=8,
        cached_in=0,
        retry=0,
        escalated=False,
        latency_ms=0,
    )
    return {
        "status": "UNVERIFIED",
        "evidence": context,
        "patch_instructions": "",
        "model_response": "[stub:auditor] no active providers — cannot certify; routing to human",
    }
