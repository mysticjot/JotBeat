"""
orchestrator.py — the studio's brain. A LangGraph state machine.

This is deliberately a STATE MACHINE, not a chatroom:
  - Nodes are production stages. Edges are gates.
  - Agents never talk to each other. They emit artifacts; the graph routes them.
  - Deterministic stages (build, scripted QA) cost $0 and gate the AI stages.
  - The Auditor is adversarial and independent: it never sees the Coder's
    self-assessment, only the acceptance criteria and the evidence.
  - Retries are bounded. The ceiling is structural, not a hope.

Graph:
  select_task -> execute_role -> build_verify -> scripted_qa -> cert_audit
  cert_audit --MET--------> commit -> select_task (next) or END
  cert_audit --FAILED-----> patch (attempts+1) -> build_verify   [<=2 attempts]
  cert_audit --FAILED-----> escalate (shrunk context, frontier)  [<=2 more]
  cert_audit --still bad--> human_ticket -> END (stops, never burns budget)
  any stage --UNVERIFIED--> human_ticket
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ledger import log_event
from state import get_next_ready_task, set_task_status

MAX_ATTEMPTS_BEFORE_ESCALATION = 2
MAX_ESCALATIONS_BEFORE_HUMAN = 2


class StudioState(TypedDict, total=False):
    task: dict
    instructions: str           # what the role was asked to do
    artifacts: list[str]        # files the role produced
    role_notes: str             # the role's own notes (never shown to auditor)
    build_result: dict          # deterministic BVT output
    qa_result: dict             # Playwright suite output
    audit: dict                 # auditor verdict: MET | FAILED | UNVERIFIED | SKIPPED
    attempts: int
    escalations: int
    done: bool


# ---------------------------------------------------------------- nodes

def select_task(state: StudioState) -> dict:
    task = get_next_ready_task()
    if task is None:
        return {"done": True}
    set_task_status(task["id"], "IN_DEVELOPMENT")
    log_event("task_started", task=task["id"], role=task["role"])
    return {"task": task, "attempts": 0, "escalations": 0, "done": False}


def execute_role(state: StudioState) -> dict:
    """Dispatch to the role module. Roles live in studio/roles/ and each
    receives ONLY its context slice (BUDGET.md context budgets)."""
    from roles import dispatch  # roles/director.py, coder.py, qa.py, ...
    result = dispatch(state["task"], escalation_level=state.get("escalations", 0))
    return {
        "artifacts": result["artifacts"],
        "role_notes": result.get("notes", ""),
        "instructions": result["instructions"],
    }


def build_verify(state: StudioState) -> dict:
    """Deterministic BVT: install, compile, lint, bundle, asset validation.
    Pure subprocess. Zero model calls. Failure here short-circuits QA."""
    from tools.shell import run_bvt
    result = run_bvt()
    log_event("bvt", task=state["task"]["id"], passed=result["passed"])
    return {"build_result": result}


def scripted_qa(state: StudioState) -> dict:
    """Playwright suite for this task's acceptance criteria.
    Fake input + window.__game.state assertions + screenshots. $0 infra."""
    from tools.browser import run_ac_suite
    result = run_ac_suite(state["task"].get("acceptance_ids", []))
    log_event("qa_run", task=state["task"]["id"], passed=result["passed"])
    return {"qa_result": result}


def cert_audit(state: StudioState) -> dict:
    """Adversarial audit. Inputs: AC + build/qa EVIDENCE DIGESTS only.
    Explicitly excluded: role_notes (the coder's self-assessment)."""
    from roles.auditor import audit
    verdict = audit(
        task=state["task"],
        build=state["build_result"],
        qa=state["qa_result"],
    )
    log_event("audit", task=state["task"]["id"], status=verdict["status"])
    return {"audit": verdict}


def commit(state: StudioState) -> dict:
    from tools.git import commit_changes
    commit_changes(state["task"], state["artifacts"])
    set_task_status(state["task"]["id"], "DONE")
    log_event("task_verified", task=state["task"]["id"])
    return {}


def patch(state: StudioState) -> dict:
    """Kickback: same role tries again with the auditor's patch instructions.
    Bounded — the escalation ceiling lives in the edges below.
    Note: patch is also reached from build/QA gate failures, before any audit
    exists — hence the defensive .get on state["audit"]."""
    attempts = state.get("attempts", 0) + 1
    set_task_status(state["task"]["id"], "KICKED_BACK",
                    reason=state.get("audit", {}).get("patch_instructions", ""))
    log_event("kickback", task=state["task"]["id"], attempt=attempts)
    return {"attempts": attempts}


def escalate(state: StudioState) -> dict:
    """Frontier model, SHRUNK context (failing function + error only).
    Escalation is a surgeon's call, not a bigger one."""
    escalations = state.get("escalations", 0) + 1
    log_event("escalation", task=state["task"]["id"], level=escalations)
    return {"escalations": escalations, "attempts": 0}


def human_ticket(state: StudioState) -> dict:
    """The budget ceiling. The machine stops and asks a human.
    It never, ever retries past this point on its own."""
    set_task_status(state["task"]["id"], "BLOCKED_HUMAN")
    log_event("human_ticket", task=state["task"]["id"],
              audit=state.get("audit", {}))
    return {"done": True}


# ---------------------------------------------------------------- edges

def after_select(state: StudioState) -> str:
    return END if state.get("done") else "execute_role"


def after_build(state: StudioState) -> str:
    return "scripted_qa" if state["build_result"]["passed"] else "patch"


def after_qa(state: StudioState) -> str:
    return "cert_audit" if state["qa_result"]["passed"] else "patch"


def after_audit(state: StudioState) -> str:
    status = state["audit"]["status"]
    if status == "MET":
        return "commit"
    if status in ("UNVERIFIED", "SKIPPED"):
        return "human_ticket"
    # FAILED — the ceiling logic
    if state.get("attempts", 0) < MAX_ATTEMPTS_BEFORE_ESCALATION:
        return "patch"
    if state.get("escalations", 0) < MAX_ESCALATIONS_BEFORE_HUMAN:
        return "escalate"
    return "human_ticket"


def after_commit(state: StudioState) -> str:
    return "select_task"  # loop to the next ready backlog item


# ---------------------------------------------------------------- graph

def build_graph(checkpointer=None):
    g = StateGraph(StudioState)
    g.add_node("select_task", select_task)
    g.add_node("execute_role", execute_role)
    g.add_node("build_verify", build_verify)
    g.add_node("scripted_qa", scripted_qa)
    g.add_node("cert_audit", cert_audit)
    g.add_node("commit", commit)
    g.add_node("patch", patch)
    g.add_node("escalate", escalate)
    g.add_node("human_ticket", human_ticket)

    g.add_edge(START, "select_task")
    g.add_conditional_edges("select_task", after_select, {END: END, "execute_role": "execute_role"})
    g.add_edge("execute_role", "build_verify")
    g.add_conditional_edges("build_verify", after_build, {"scripted_qa": "scripted_qa", "patch": "patch"})
    g.add_conditional_edges("scripted_qa", after_qa, {"cert_audit": "cert_audit", "patch": "patch"})
    g.add_conditional_edges("cert_audit", after_audit, {
        "commit": "commit", "patch": "patch",
        "escalate": "escalate", "human_ticket": "human_ticket",
    })
    g.add_edge("patch", "build_verify")      # retry re-enters at the gate, not the model
    g.add_edge("escalate", "execute_role")   # escalation re-runs the role with shrunk context
    g.add_conditional_edges("commit", after_commit, {"select_task": "select_task"})
    g.add_edge("human_ticket", END)

    return g.compile(checkpointer=checkpointer)


def run() -> None:
    from langgraph.checkpoint.sqlite import SqliteSaver
    # from_conn_string returns a context manager in langgraph-checkpoint-sqlite 3.x
    with SqliteSaver.from_conn_string("state/graph-checkpoints.db") as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer=checkpointer)
        graph.invoke({}, {"configurable": {"thread_id": "production"}})
