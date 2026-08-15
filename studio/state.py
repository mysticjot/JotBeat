"""
state.py — the studio's memory. Agents have no memory; these files remember.

Owns: state/project-state.json, state/task-queue.json
All reads/writes go through here so the schema lives in exactly one place.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "state"

PROJECT_STATE = STATE_DIR / "project-state.json"
TASK_QUEUE = STATE_DIR / "task-queue.json"


def _load(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)  # atomic-ish: never leave a half-written state file


def load_project_state() -> dict:
    return _load(PROJECT_STATE, {
        "game": None,
        "phase": "pre-production",
        "milestone": None,
        "completed_items": [],
        "open_bugs": [],
        "routing_overrides": {},
    })


def save_project_state(state: dict) -> None:
    _save(PROJECT_STATE, state)


def load_task_queue() -> dict:
    return _load(TASK_QUEUE, {"items": []})


def save_task_queue(queue: dict) -> None:
    _save(TASK_QUEUE, queue)


def get_next_ready_task() -> dict | None:
    """First backlog item whose dependencies are all DONE."""
    queue = load_task_queue()
    done = {i["id"] for i in queue["items"] if i["status"] == "DONE"}
    for item in queue["items"]:
        if item["status"] == "BACKLOG" and all(d in done for d in item.get("depends_on", [])):
            return item
    return None


def set_task_status(task_id: str, status: str, **fields) -> None:
    """status: BACKLOG | IN_DEVELOPMENT | CODE_REVIEW | QA | VERIFIED | KICKED_BACK | DONE"""
    queue = load_task_queue()
    for item in queue["items"]:
        if item["id"] == task_id:
            item["status"] = status
            item.update(fields)
            break
    save_task_queue(queue)
