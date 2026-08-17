"""tools/cert.py — cert report writer (HANDOFF-PHASE4 §2.4).

`jotbeat verify` emits one report per run into reports/cert/: one section per
AC — verdict (MET/FAILED/UNVERIFIED), evidence links (spec file, failure
screenshot dir, latest auditor event), and for FAILED the auditor's patch
instructions when a prior loop audit exists. Deterministic: NO model calls —
verdicts derive from the Playwright matrix results; auditor input is read
from the ledger (events.jsonl), never invoked here.

Every cert also carries a Commercial Baseline section
(docs/COMMERCIAL_BASELINE.md): one PASS/FAIL per checklist item with evidence
pointers. A cert without it is invalid (auditor rule), so the section is
always emitted — missing evidence reports FAIL, never omission.

Readable by a human in 2 minutes: header verdicts first, per-AC sections
second, machine digest last.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RESULT_RE = re.compile(
    r"^(?P<mark>[✓✘x-])\s+\d+\s+\[(?P<project>[^\]]+)\]\s+›\s+"
    r"(?P<spec>tests[\\/][^\s:]+?\.spec\.ts)"
)
AC_RE = re.compile(r"ac-(\d+)", re.IGNORECASE)

# Baseline spec lines carry the checklist item in the test title:
# "... › tests/baseline.spec.ts:… › Commercial Baseline › baseline frame: …"
BASELINE_RE = re.compile(
    r"^(?P<mark>[✓✘x-])\s+\d+\s+\[(?P<project>[^\]]+)\]\s+›\s+"
    r"tests[\\/]baseline\.spec\.ts.*?›\s*baseline\s+(?P<item>[a-z-]+)\s*:",
    re.IGNORECASE,
)

# Checklist item order + which spec prefix feeds each (docs/COMMERCIAL_BASELINE.md).
# "text" is covered by the aislop slop gate, "provenance" by
# tools/provenance.py, "design match" by tools/design_match.py.
BASELINE_ITEMS = [
    ("Frame", "frame"),
    ("Character/craft", "character"),
    ("Audio", "audio"),
    ("Onboarding", "onboarding"),
    ("Text", None),
    ("Provenance", None),
    ("Design match", None),
    ("Player-mode pre-flight", "frame"),  # the walkthrough IS the pre-flight
]

SCREENSHOT_DIR = "artifacts/screenshots/baseline"


def _git_sha(root: Path) -> str:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            or "unknown"
        )
    except Exception:
        return "unknown"


def _latest_audits(events_path: Path) -> dict[str, dict]:
    """Latest audit event per task id from the ledger (read-only)."""
    audits: dict[str, dict] = {}
    if not events_path.exists():
        return audits
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "audit" and e.get("task"):
            audits[e["task"]] = e
    return audits


def parse_results(results: list[str]) -> dict[str, dict]:
    """Group ✓/✘ result lines by AC id -> per-project pass/fail + spec file."""
    acs: dict[str, dict] = {}
    for line in results:
        m = RESULT_RE.match(line.strip())
        if not m:
            continue
        ac_m = AC_RE.search(m.group("spec"))
        if not ac_m:
            continue  # smoke/visual specs carry no AC id
        ac_id = f"AC-{int(ac_m.group(1)):03d}"
        entry = acs.setdefault(ac_id, {"spec": m.group("spec"), "projects": {}})
        # A spec is green for the AC only if ALL its project runs are green.
        passed = m.group("mark") == "✓"
        prev = entry["projects"].get(m.group("project"), True)
        entry["projects"][m.group("project")] = prev and passed
    return acs


def parse_baseline(results: list[str]) -> dict[str, dict]:
    """Group baseline spec lines by checklist item prefix -> per-project
    pass/fail + failing titles. Empty when the QA run has no baseline
    evidence — the auditor rule makes that an automatic FAIL per item."""
    items: dict[str, dict] = {}
    for line in results:
        m = BASELINE_RE.match(line.strip())
        if not m:
            continue
        item = m.group("item").lower()
        entry = items.setdefault(item, {"projects": {}, "failures": []})
        passed = m.group("mark") == "✓"
        prev = entry["projects"].get(m.group("project"), True)
        entry["projects"][m.group("project")] = prev and passed
        if not passed:
            entry["failures"].append(line.strip())
    return items


def baseline_items(
    qa: dict, provenance: dict, quality_rc: int, root: Path, design: dict
) -> list[dict]:
    """One verdict per Commercial Baseline checklist item.

    Returns [{"name", "passed", "evidence"}]. A cert without this list is
    invalid (auditor rule), so the section is ALWAYS emitted — missing
    evidence reports FAIL, never omission."""
    spec_items = parse_baseline(qa.get("results", []))
    shots = Path(root) / SCREENSHOT_DIR
    shot_count = len(list(shots.glob("*.png"))) if shots.is_dir() else 0

    verdicts: list[dict] = []
    for name, prefix in BASELINE_ITEMS:
        if prefix is not None:
            entry = spec_items.get(prefix)
            passed = (
                entry is not None
                and bool(entry["projects"])
                and all(entry["projects"].values())
            )
            evidence = f"screenshots: `{SCREENSHOT_DIR}/` ({shot_count} states captured)"
            if entry and entry["failures"]:
                evidence += f"; failing: {entry['failures'][0]}"
            if name == "Player-mode pre-flight":
                passed = passed and shot_count >= 5
                evidence += "; defect list: `reports/triage/`"
        elif name == "Text":
            passed = quality_rc == 0
            evidence = "aislop slop gate (quality gate); narrative review is process, not scanner"
        elif name == "Design match":
            passed = bool(design.get("passed"))
            failed = [c for c in design.get("checks", []) if not c["passed"]]
            evidence = (
                f"build matches {len(design.get('checks', []))} design checks"
                if passed
                else "docs/GAME_DESIGN.md content checklist — failing: "
                + "; ".join(f"{c['name']} ({c['detail']})" for c in failed)
            )
        else:  # Provenance
            passed = bool(provenance.get("passed"))
            evidence = (
                f"manifest covers {provenance.get('checked', 0)} files"
                if passed
                else "missing entries: "
                + ", ".join(provenance.get("missing", []) + provenance.get("incomplete", []))
            )
        verdicts.append({"name": name, "passed": passed, "evidence": evidence})
    return verdicts


def write_cert_report(
    build: dict, qa: dict, quality_rc: int, root: Path, provenance: dict, design: dict
) -> Path:
    root = Path(root)
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d-%H%M%S")
    acs = parse_results(qa.get("results", []))
    audits = _latest_audits(root / "state" / "events.jsonl")
    baseline = baseline_items(qa, provenance, quality_rc, root, design)
    baseline_ok = all(item["passed"] for item in baseline)
    certified = (
        build.get("passed") and qa.get("passed") and quality_rc == 0 and baseline_ok
    )

    lines = [
        f"# JotBeat Cert — {now.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        f"- commit: `{_git_sha(root)}`",
        f"- BVT: {'PASS' if build.get('passed') else 'FAIL'}"
        f" · QA (viewport matrix): {'PASS' if qa.get('passed') else 'FAIL'}"
        f" · quality gate: {'PASS' if quality_rc == 0 else 'FAIL'}"
        f" · commercial baseline: {'PASS' if baseline_ok else 'FAIL'}",
        f"- overall: **{'CERTIFIED' if certified else 'NOT CERTIFIED'}**",
        "",
        "## Commercial Baseline",
        "",
        "Gate-blocking checklist (docs/COMMERCIAL_BASELINE.md) — any FAIL blocks",
        "the gate. Auditor rule: a cert without this section is invalid; this",
        "section is always emitted, and missing evidence reports FAIL.",
        "",
    ]
    for item in baseline:
        lines.append(
            f"- **{item['name']}: {'PASS' if item['passed'] else 'FAIL'}**"
            f" — {item['evidence']}"
        )
    lines.append("")
    lines.append("## Acceptance criteria")
    lines.append("")
    for ac_id in sorted(acs):
        entry = acs[ac_id]
        projects = entry["projects"]
        all_green = all(projects.values()) and len(projects) > 0
        verdict = "MET" if all_green else "FAILED"
        bl_id = "BL-" + ac_id.split("-")[1]
        audit = audits.get(bl_id)
        lines.append(f"### {ac_id} — {verdict}")
        lines.append(f"- spec: `game/{entry['spec']}`")
        lines.append(
            "- viewports: "
            + ", ".join(
                f"{p} {'✓' if ok else '✘'}" for p, ok in sorted(projects.items())
            )
        )
        if audit:
            lines.append(
                f"- auditor: {audit.get('status', '?')} at {audit.get('ts', '?')}"
            )
        if not all_green:
            lines.append("- failure screenshots: `game/test-results/`")
            lines.append(
                "- patch instructions: "
                + (
                    audit.get("patch_instructions")
                    if audit and audit.get("patch_instructions")
                    else "none on ledger — rerun `jotbeat run-next` for an auditor pass"
                )
            )
        lines.append("")
    if not acs:
        lines.append("_no AC-tagged specs found in the QA run_")
        lines.append("")

    out_dir = root / "reports" / "cert"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / f"cert-{stamp}.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "latest.md").write_text("\n".join(lines), encoding="utf-8")
    return report
