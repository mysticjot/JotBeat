"""harness/agent.py — build a Deep Agents harness for one JotBeat role.

Shape (D-0006): a thin DISPATCHER deep agent holds the role as a sub-agent
and delegates via the `task` tool. The role sub-agent gets the Deep Agents
capabilities (planning, repo-rooted virtual filesystem, optional sandboxed
shell) scoped by scopes.py. The dispatcher itself is deny-all: it routes,
it never touches the tree.

The harness WRAPS the brain — orchestrator.py topology, gates, ceilings,
and the auditor's input exclusions are unchanged.
"""

from __future__ import annotations

from deepagents import FilesystemPermission, SubAgent, create_deep_agent
from deepagents.backends import FilesystemBackend, LocalShellBackend

from harness.model import HarnessChatModel
from harness.scopes import SENSITIVE_DENY_PATHS, scope_for
from state import ROOT

# The dispatcher routes; it must not read or write anything itself.
_DISPATCHER_PERMISSIONS = [
    FilesystemPermission(operations=["read"], paths=["/**"], mode="deny"),
    FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
]

_DISPATCHER_PROMPT = (
    "You are the JotBeat harness dispatcher. You do NOT do the work yourself. "
    "Immediately delegate the user's entire task to the sub-agent named "
    "'{role}' using the task tool, then report that sub-agent's final output "
    "verbatim as your own final answer. You have no file access."
)


def permissions_for_scope(scope: dict) -> list[FilesystemPermission]:
    """Ordered rules; first match wins (deny-list beats allow-list, so the
    allow entries for write_paths must precede the catch-all write deny)."""
    rules = [
        FilesystemPermission(
            operations=["read"], paths=SENSITIVE_DENY_PATHS, mode="deny"
        ),
        FilesystemPermission(
            operations=["write"], paths=SENSITIVE_DENY_PATHS, mode="deny"
        ),
    ]
    if scope["write_paths"]:
        rules.append(
            FilesystemPermission(
                operations=["write"], paths=scope["write_paths"], mode="allow"
            )
        )
    rules.append(
        FilesystemPermission(operations=["write"], paths=["/**"], mode="deny")
    )
    return rules


def build_harness(
    role: str,
    task_id: str,
    *,
    escalation_level: int = 0,
):
    """Compile a deep agent whose single sub-agent is `role`, permission-
    scoped per scopes.py. Returns the compiled LangGraph graph."""
    scope = scope_for(role)
    backend_cls = LocalShellBackend if scope["shell"] else FilesystemBackend
    # virtual_mode anchors every path at the repo root and blocks traversal.
    backend = backend_cls(root_dir=str(ROOT), virtual_mode=True)

    role_model = HarnessChatModel(
        role=role, task_id=task_id, escalation_level=escalation_level
    )
    role_subagent: SubAgent = {
        "name": role,
        "description": scope["description"],
        "system_prompt": scope["system_prompt"],
        "model": role_model,
        # The sub-agent's rules REPLACE the parent's — the role's scope, not
        # the dispatcher's deny-all, applies inside the role.
        "permissions": permissions_for_scope(scope),
    }
    return create_deep_agent(
        model=HarnessChatModel(
            role=role, task_id=task_id, escalation_level=escalation_level
        ),
        system_prompt=_DISPATCHER_PROMPT.format(role=role),
        backend=backend,
        permissions=_DISPATCHER_PERMISSIONS,
        subagents=[role_subagent],
    )
