"""
test_graph_live.py — live proof that the LangGraph brain runs the studio loop.

Stubs the roles/tools layers (Phase 2 TODOs) and drives real backlog items
through the graph: a clean pass, a kickback-then-pass, and a full
escalation-to-human path. Run: python3 test_graph_live.py
"""

import json
import sys
import tempfile
import types
from pathlib import Path

# ---- sandbox state + ledger into a temp dir so the repo stays clean
TMP = Path(tempfile.mkdtemp(prefix="jotbeat-live-"))
import state, ledger  # noqa: E402
state.STATE_DIR = TMP
state.PROJECT_STATE = TMP / "project-state.json"
state.TASK_QUEUE = TMP / "task-queue.json"
ledger.EVENTS = TMP / "events.jsonl"
ledger.PROVIDERS_FILE = Path(__file__).parent / "providers.json"

# ---- seed a backlog: 3 items, one dependency chain
state.save_task_queue({"items": [
    {"id": "AC-002-walls", "role": "coder", "status": "BACKLOG",
     "depends_on": [], "acceptance_ids": ["AC-002"]},
    {"id": "AC-004-door", "role": "coder", "status": "BACKLOG",
     "depends_on": ["AC-002-walls"], "acceptance_ids": ["AC-004"]},
    {"id": "AC-009-hud", "role": "coder", "status": "BACKLOG",
     "depends_on": [], "acceptance_ids": ["AC-009"]},
]})

# ---- stub roles + tools (these are the Phase 2 TODOs)
calls = {"dispatch": 0, "audit": 0}

roles = types.ModuleType("roles")
def dispatch(task, escalation_level=0):
    calls["dispatch"] += 1
    lvl = f" (escalated L{escalation_level})" if escalation_level else ""
    print(f"  [coder{lvl}] implementing {task['id']}")
    return {"artifacts": [f"src/systems/{task['id']}.ts"],
            "notes": "looks good to me",  # auditor never sees this
            "instructions": task["id"]}
roles.dispatch = dispatch

auditor_mod = types.ModuleType("roles.auditor")
def audit(task, build, qa):
    calls["audit"] += 1
    # scripted verdicts: walls pass clean, door fails twice then passes, hud never passes
    if task["id"] == "AC-002-walls":
        v = "MET"
    elif task["id"] == "AC-004-door":
        v = "FAILED" if calls["audit"] < 4 else "MET"
    else:
        v = "FAILED"
    print(f"  [auditor] {task['id']}: {v}")
    return {"status": v, "evidence": ["reports/qa/ac.spec.ts"],
            "patch_instructions": "fix collision normal" if v == "FAILED" else ""}
auditor_mod.audit = audit
roles.auditor = auditor_mod

tools = types.ModuleType("tools")
shell = types.ModuleType("tools.shell")
shell.run_bvt = lambda: {"passed": True, "steps": ["compile", "lint", "bundle"]}
browser = types.ModuleType("tools.browser")
browser.run_ac_suite = lambda ids: {"passed": True, "tests": ids}
git = types.ModuleType("tools.git")
git.commit_changes = lambda task, arts: print(f"  [git] commit {task['id']}: {arts}")
tools.shell, tools.browser, tools.git = shell, browser, git

sys.modules.update({"roles": roles, "roles.auditor": auditor_mod,
                    "tools": tools, "tools.shell": shell,
                    "tools.browser": browser, "tools.git": git})

# ---- run the real graph
import orchestrator  # noqa: E402
from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402

print("=== JotBeat live graph run ===")
with SqliteSaver.from_conn_string(str(TMP / "cp.db")) as cp:
    cp.setup()
    graph = orchestrator.build_graph(cp)
    graph.invoke({}, {"configurable": {"thread_id": "live-demo"}})

print("\n=== ledger (events.jsonl) ===")
for line in ledger.EVENTS.read_text().splitlines():
    e = json.loads(line)
    if e["type"] == "model_call":
        continue
    print(f"  {e['type']:<14} {e.get('task','')}")

print("\n=== final queue state ===")
for item in state.load_task_queue()["items"]:
    print(f"  {item['id']:<14} {item['status']}")
