"""harness/scopes.py — per-role permission scoping. Config, not code.

Adding a role to the harness = adding one entry to ROLE_SCOPES. No new
code paths. Unknown roles FAIL CLOSED to DEFAULT_SCOPE (read-only, no shell).

Fields:
  write_paths: virtual-path globs the role may write/edit/delete under
      (repo-root-relative, leading "/"). Empty = read-only.
  shell:       True grants the sandboxed-shell tool (LocalShellBackend).
  description: one-liner for the dispatcher's task tool.
  system_prompt: the role's harness instructions. Short on purpose — real
      prompt engineering is Phase 3 (studio/prompts/).

Enforcement layers (both, belt and suspenders):
  1. deepagents FilesystemPermission rules (deny write outside write_paths,
     deny reads of .env/.git — AGENTS.md §5: keys stay out);
  2. backend choice: shell only when scope["shell"] is True.
"""

from __future__ import annotations

# Virtual-path prefixes every role is forbidden from even READING.
# .env holds the provider keys (AGENTS.md §5); .git holds nothing a role needs.
SENSITIVE_DENY_PATHS = ["/.env", "/.env.*", "/.git/**"]

AUDITOR_PROMPT = (
    "You are the JotBeat Auditor running inside the Deep Agents execution "
    "harness. You are adversarial and independent: you never saw the "
    "implementer's notes, only the task and the evidence you gather yourself. "
    "Your tools are READ-ONLY: ls, read_file, glob, grep. You cannot write, "
    "edit, delete, or run shell commands — do not attempt to.\n"
    "Verify claims against the actual repo state using your tools. Never "
    "invent failure details you did not observe.\n"
    "Reply in PLAIN TEXT — no markdown bold, italics, or headers; the brain's "
    "parser matches the labels literally. Use EXACTLY this format, in order:\n"
    "Reasoning: <one or two sentences grounded in files you actually read>\n"
    "Verdict: MET | FAILED | UNVERIFIED | SKIPPED\n"
    "Patch: <concrete fix instructions — only when FAILED; LAST line(s)>"
)

NARRATIVE_PROMPT = (
    "You are the JotBeat Narrative role running inside the Deep Agents "
    "execution harness. You may read anywhere in the repo, but you may WRITE "
    "text files under /docs/ only (NARRATIVE_BIBLE.md, dialogue, lore). "
    "You have no shell. Voice guide: spare, salt-rough, short declaratives — "
    "nothing that reads as generic AI game output "
    "(studio/prompts/slop-standard.md)."
)

ROLE_SCOPES: dict[str, dict] = {
    # The auditor proves the harness (D-0006): read-only tools, no shell,
    # no writes of any kind.
    "auditor": {
        "write_paths": [],
        "shell": False,
        "description": (
            "Adversarial cert auditor. Read-only evidence review of a target "
            "against repo state; verdicts MET | FAILED | UNVERIFIED | SKIPPED."
        ),
        "system_prompt": AUDITOR_PROMPT,
    },
    # Narrative writes text only, docs/ only.
    "narrative": {
        "write_paths": ["/docs/**"],
        "shell": False,
        "description": (
            "Narrative writer. Reads the repo; writes text under /docs/ only."
        ),
        "system_prompt": NARRATIVE_PROMPT,
    },
}

# Fail closed: a role with no scope entry gets read-only + no shell.
DEFAULT_SCOPE: dict = {
    "write_paths": [],
    "shell": False,
    "description": "Unscoped role — read-only, no shell (fail-closed default).",
    "system_prompt": (
        "You are a JotBeat studio role in the Deep Agents harness. "
        "You have read-only tools and no shell."
    ),
}


def scope_for(role: str) -> dict:
    return ROLE_SCOPES.get(role, DEFAULT_SCOPE)
