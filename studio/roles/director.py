"""Director role. Brief tasks (id starts with "brief-") use the Phase 3
prompt in studio/prompts/director_brief.md and receive the pitch as context;
anything else falls back to the shared plumbing."""

from pathlib import Path

from models import ModelAdapter, active_providers

from ._base import run_role

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "director_brief.md"


def run(task: dict, escalation_level: int = 0) -> dict:
    if not task["id"].startswith("brief-") or not active_providers("director"):
        return run_role("director", task, escalation_level=escalation_level)

    instructions = PROMPT_PATH.read_text(encoding="utf-8")
    context = [f"pitch: {task['title']}"]
    text = ModelAdapter("director").complete(
        instructions,
        context,
        task_id=task["id"],
        escalation_level=escalation_level,
    )
    return {"artifacts": [], "notes": text, "instructions": instructions}
