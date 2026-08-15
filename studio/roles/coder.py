"""Coder role — Phase 2 stub. Real prompt engineering is Phase 3 (studio/prompts/)."""

from ._base import run_role


def run(task: dict, escalation_level: int = 0) -> dict:
    return run_role("coder", task, escalation_level=escalation_level)
