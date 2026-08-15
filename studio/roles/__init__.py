"""Roles package — one module per discipline, routed by dispatch().

Agents never talk to each other (roadmap §2.1): the orchestrator calls
dispatch(task) and routes the returned artifacts. Phase 2 role bodies are
stubs that call ModelAdapter with the role's context slice; real prompt
engineering is Phase 3 (studio/prompts/).
"""

from __future__ import annotations

import importlib

ROLE_MODULE_NAMES = {
    "director", "producer", "coder", "designer", "level",
    "artist", "sound", "qa", "publisher",
}


def dispatch(task: dict, escalation_level: int = 0) -> dict:
    """Route a backlog item to its role module. Returns
    {"artifacts": [...], "notes": str, "instructions": str}."""
    role = task["role"]
    if role not in ROLE_MODULE_NAMES:
        raise ValueError(f"unknown role: {role}")
    module = importlib.import_module(f"roles.{role}")
    return module.run(task, escalation_level=escalation_level)
