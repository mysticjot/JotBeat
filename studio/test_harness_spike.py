"""test_harness_spike.py — D-0006 proof gate: the auditor runs one full audit
loop THROUGH the Deep Agents harness.

The auditor sub-agent gets a tiny, real target (reports/cert/latest.md),
verifies it against the repo state with its READ-ONLY harness tools
(no write, no shell — scopes.py), and emits a verdict. Every model call is
ledgered by harness/model.py -> ledger.log_call, and the verdict lands via
ledger.log_event — both in the REAL state/events.jsonl.

Run from the repo root:
    python studio/test_harness_spike.py

A live model call is expected and approved. Keys load from .env via
cli.load_env() — they are never read, printed, or stored by this script.
"""

import json
import os
import sys
from pathlib import Path

# --- LangSmith kill-switch BEFORE any langchain/deepagents import ---------
# D-0006 (docs/DECISIONS.md): LangSmith is REJECTED — redundant with
# state/events.jsonl. Its env keys must never be set. harness/__init__.py
# repeats this, but imports must be safe no matter the entry order.
os.environ["LANGCHAIN_TRACING_V2"] = "false"
for _k in (
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_ENDPOINT",
    "LANGCHAIN_TRACING",
    "LANGCHAIN_PROJECT",
    "LANGCHAIN_CALLBACKS_BACKGROUND",
):
    os.environ.pop(_k, None)
# --------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli import load_env  # noqa: E402 — populates os.environ from .env

load_env()

from langchain_core.messages import HumanMessage  # noqa: E402

from harness import build_harness  # noqa: E402
from ledger import EVENTS, log_event  # noqa: E402
from roles.auditor import PATCH_RE, VERDICT_RE  # noqa: E402 — the brain's own parsing

TASK_ID = "HARNESS-SPIKE-001"
TARGET = "/reports/cert/latest.md"

AUDIT_TASK = f"""Audit the cert report at {TARGET} against the actual repo state.

1. Read the report.
2. List every repo path it references (e.g. artifacts/screenshots/baseline/,
   reports/triage/, docs/COMMERCIAL_BASELINE.md, game/tests/... spec files).
3. Verify with your read-only tools (ls / glob / read_file) whether each
   referenced path exists in this repo.
4. Verdict MET if the report exists, is well-formed, and every referenced
   path you checked exists; FAILED if anything referenced is missing (quote
   it in Patch); UNVERIFIED if you cannot determine.

Keep the reply short. Remember your required output format (Reasoning /
Verdict / Patch)."""


def _flatten(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "") for b in content if isinstance(b, dict)
        )
    return ""


def main() -> int:
    before = EVENTS.read_text(encoding="utf-8").splitlines() if EVENTS.exists() else []

    print(f"=== harness spike: auditor audits {TARGET} (task {TASK_ID}) ===")
    agent = build_harness("auditor", TASK_ID)
    result = agent.invoke(
        {"messages": [HumanMessage(content=AUDIT_TASK)]},
        config={"recursion_limit": 60},
    )

    # Evidence the auditor actually USED its harness tools (not hallucinated):
    # the tool-call trajectory from the agent loop.
    print("=== harness tool trajectory ===")
    for m in result["messages"]:
        for tc in getattr(m, "tool_calls", []) or []:
            args = json.dumps(tc["args"])
            print(f"  {tc['name']}({args[:140]})")
    print()

    # The ROLE's verdict is the sub-agent's own final output (the task tool's
    # result), not the dispatcher's relay — the dispatcher is plumbing and is
    # free to reformat. Fall back to the final message if no task ran.
    text = ""
    for m in reversed(result["messages"]):
        if getattr(m, "type", None) == "tool" and getattr(m, "name", "") == "task":
            text = _flatten(m.content)
            break
    if not text:
        text = _flatten(result["messages"][-1].content)
    verdict_m = VERDICT_RE.search(text)
    patch_m = PATCH_RE.search(text)
    status = verdict_m.group(1).upper() if verdict_m else "UNVERIFIED"
    patch = patch_m.group(1).strip() if patch_m else ""

    # The verdict lands in the ledger, same as a brain-era audit event.
    log_event(
        "harness_audit",
        task=TASK_ID,
        role="auditor",
        status=status,
        target=TARGET,
        harness="deepagents",
        patch_instructions=patch[:300],
    )

    print(f"\n=== auditor sub-agent final reply ===\n{text}\n")
    print(f"=== verdict: {status} ===")

    after = EVENTS.read_text(encoding="utf-8").splitlines()
    new_events = [json.loads(line) for line in after[len(before):]]
    print(f"\n=== new state/events.jsonl entries ({len(new_events)}) ===")
    for e in new_events:
        print(json.dumps(e))

    calls = [e for e in new_events if e.get("type") == "model_call"]
    cost = sum(e["cost_usd"] for e in calls)
    tin = sum(e["tokens_in"] for e in calls)
    tout = sum(e["tokens_out"] for e in calls)
    print(
        f"\n=== spike cost: {len(calls)} model calls, "
        f"{tin} in / {tout} out tokens, ${cost:.6f} ==="
    )
    return 0 if status in ("MET", "FAILED") else 1


if __name__ == "__main__":
    sys.exit(main())
