"""harness/ — the execution harness (D-0006, docs/DECISIONS.md).

The LangGraph brain (orchestrator.py) stays the control plane: task flow,
gates, escalation ceilings, ledger. This package is the EXECUTION layer —
roles run as LangChain Deep Agents sub-agents with planning, a virtual
filesystem rooted at the repo, and permission-scoped tools (scopes.py).

Models come ONLY from providers.json via models.py family dispatch
(model.py -> models.chat_completions). No hardcoded providers, no parallel
key stores.
"""

# --- LangSmith kill-switch ------------------------------------------------
# D-0006: LangSmith is REJECTED — redundant with state/events.jsonl. Its env
# keys must never be set; disable tracing BEFORE importing anything from
# langchain/deepagents (langsmith reads these at import/client-build time).
import os as _os

_os.environ["LANGCHAIN_TRACING_V2"] = "false"
for _k in (
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_ENDPOINT",
    "LANGCHAIN_TRACING",
    "LANGCHAIN_PROJECT",
    "LANGCHAIN_CALLBACKS_BACKGROUND",
):
    _os.environ.pop(_k, None)
# --------------------------------------------------------------------------

from harness.agent import build_harness  # noqa: E402
from harness.model import HarnessChatModel  # noqa: E402
from harness.scopes import ROLE_SCOPES  # noqa: E402

__all__ = ["ROLE_SCOPES", "HarnessChatModel", "build_harness"]
