"""Shared role plumbing: context slice -> ModelAdapter, with an offline stub
when no provider keys are active. Stub calls are ledgered at the head-of-chain
price (free tier = $0.00) so cost math is exercised even without keys."""

from __future__ import annotations

from ledger import log_call
from models import ModelAdapter, active_providers, load_routing


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
