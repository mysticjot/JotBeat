"""Auditor role — adversarial and independent (roadmap §2.4).

INPUT EXCLUSION IS LOAD-BEARING: audit() receives only the task, the build
digest, and the QA digest. It MUST NOT receive role_notes or any implementer's
self-assessment (HANDOFF-PHASE2.md §6b/§8). Do not add parameters.
"""

from __future__ import annotations

from ledger import log_call
from models import ModelAdapter, active_providers, load_routing


def audit(task: dict, build: dict, qa: dict) -> dict:
    """Return {"status": MET|FAILED|UNVERIFIED|SKIPPED, "evidence": [...],
    "patch_instructions": str}."""
    context = [
        f"task id: {task['id']}",
        f"acceptance criteria: {', '.join(task.get('acceptance_ids', [])) or 'none'}",
        f"build digest: passed={build.get('passed')} steps={build.get('steps', [])}",
        f"qa digest: passed={qa.get('passed')} tests={qa.get('tests', [])}",
    ]
    instructions = (
        "You are the JotBeat Auditor. You never saw the implementer's notes. "
        "Issue a verdict per acceptance criterion from the evidence only: "
        "MET, FAILED, UNVERIFIED, or SKIPPED, with patch instructions on FAILED."
    )

    if active_providers("auditor"):
        text = ModelAdapter("auditor").complete(
            instructions,
            context,
            task_id=task["id"],
        )
        # Phase 4 implements structured verdict parsing; Phase 2 passes it through.
        return {
            "status": "UNVERIFIED",
            "evidence": context,
            "patch_instructions": "",
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
