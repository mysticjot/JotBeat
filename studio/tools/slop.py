"""tools/slop.py — mechanical anti-slop check (Creative Director directive,
2026-08-16). Zero API cost: regex/substring matching against the vendored
pattern list (studio/guardrails/slop_patterns.json). The auditor runs this
FIRST on every player-facing string; anything it can't catch goes to the
LLM judgment pass. Either fail = FAILED verdict, offending line quoted.

CANON EXEMPTION: lines fixed verbatim in docs/NARRATIVE_BIBLE.md (the
*\"...\"* sample lines) are exempt — the bible is the authority, not the
pattern list. Exemptions are parsed from the bible, never hardcoded here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PATTERNS_FILE = Path(__file__).resolve().parent.parent / "guardrails" / "slop_patterns.json"
BIBLE_FILE = ROOT / "docs" / "NARRATIVE_BIBLE.md"
GAME_SRC = ROOT / "game" / "src"

_BIBLE_LINE_RE = re.compile(r'\*"([^"]+)"\*')
# this.add.text(x, y, 'STRING', ...) and setText(`TEMPLATE`) / setText('STRING')
_TEXT_RE = re.compile(r"\.(?:text|setText)\([^,]*,[^,]*,\s*([`'\"])(.*?)\1", re.DOTALL)
_SETTEXT_RE = re.compile(r"\.setText\(\s*([`'\"])(.*?)\1\s*\)", re.DOTALL)

_cache: dict | None = None


def load_patterns() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
    return _cache


def canon_exemptions() -> set[str]:
    """Verbatim *\"...\"* lines from the narrative bible — fixed by the
    Creative Director, exempt from every check (see slop_patterns.json)."""
    if not BIBLE_FILE.exists():
        return set()
    return {
        m.group(1).strip()
        for m in _BIBLE_LINE_RE.finditer(BIBLE_FILE.read_text(encoding="utf-8"))
    }


def check_string(s: str) -> list[dict]:
    """Mechanical pass over one string. Returns findings:
    [{"pattern": name, "match": matched text, "fix": hint}].
    Empty list = clean. Canon-exempt strings return clean."""
    if s.strip() in canon_exemptions():
        return []
    pats = load_patterns()
    findings: list[dict] = []
    low = s.lower()
    for phrase in pats["banned_phrases"]:
        if phrase in low:
            findings.append(
                {"pattern": "banned-phrase", "match": phrase,
                 "fix": "Banned outright (slop_patterns.json)."}
            )
    for word in pats["banned_words"]:
        if re.search(rf"\b{re.escape(word)}\b", low):
            findings.append(
                {"pattern": "banned-word", "match": word,
                 "fix": "Banned outright (slop_patterns.json)."}
            )
    for sp in pats["structural_patterns"]:
        m = re.search(sp["regex"], s, re.IGNORECASE | re.MULTILINE)
        if m:
            findings.append(
                {"pattern": sp["name"], "match": m.group(0), "fix": sp["fix"]}
            )
    return findings


def collect_strings() -> list[dict]:
    """Player-facing strings from game/src scene files — add.text(...) third
    argument and setText(...) argument. Deterministic; no model involved.
    Returns [{"file": rel path, "line": n, "string": s}]."""
    out: list[dict] = []
    for path in sorted(GAME_SRC.rglob("*.ts")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        for m in list(_TEXT_RE.finditer(text)) + list(_SETTEXT_RE.finditer(text)):
            s = m.group(2).strip()
            if not s:
                continue
            line = text[: m.start(2)].count("\n") + 1
            out.append({"file": rel, "line": line, "string": s})
    return out
