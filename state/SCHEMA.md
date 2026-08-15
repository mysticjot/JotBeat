# State schemas

The agents have no memory. The files remember (roadmap §5).

## `project-state.json`

Current truth: phase, milestone, current task, aggregate counters, per-phase gate status (`pending | passed | failed`). All roles read; only the Producer writes.

## `task-queue.json`

Sprint backlog / task board. Each task carries: id, role, workflow status, `acceptance_ids`, `depends_on`, `attempts`, `escalation_level`, `artifacts`. The orchestrator consumes this. Workflow states (roadmap §6):

```text
BACKLOG → IN SPRINT → IN DEVELOPMENT → CODE REVIEW → QA
→ VERIFIED / KICKED BACK → CERT REVIEW → DONE
```

## `events.jsonl`

Append-only ledger — telemetry + cost. One JSON object per line; schema in `docs/BUDGET.md` (ledger section). Never contains credentials — provider names only.

## `balance-model.json`

Tuning data / economy sheet. Owned by the Designer, consumed by the Coder. Created in Phase 3 when there is something to tune.
