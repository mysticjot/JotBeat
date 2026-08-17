"""tools/provenance.py — commercial-baseline provenance check
(docs/COMMERCIAL_BASELINE.md §6).

Every binary asset file under game/assets/ must have an entry in
game/assets/manifest.json with a non-empty `license` and `source`.
Fails hard on missing entries. Deterministic: no model calls, no network.

Called by `jotbeat verify`; the cert writer embeds the verdict in the
Commercial Baseline section.
"""

from __future__ import annotations

import json
from pathlib import Path

# Asset kinds the manifest must account for. Text/config files that are not
# licensed art (manifest.json itself, style.css) are not assets.
BINARY_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ogg", ".wav", ".mp3", ".json"}
SKIP_FILES = {"manifest.json", "style.css"}


def run_provenance(root: Path) -> dict:
    """Check asset provenance. Returns a verdict dict:
    {"passed": bool, "checked": int, "missing": [...], "incomplete": [...]}"""
    assets_dir = Path(root) / "game" / "assets"
    manifest_path = assets_dir / "manifest.json"
    if not manifest_path.exists():
        return {
            "passed": False,
            "checked": 0,
            "missing": ["<manifest.json itself is missing>"],
            "incomplete": [],
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {a.get("id"): a for a in manifest.get("assets", [])}

    missing: list[str] = []
    incomplete: list[str] = []
    checked = 0
    for f in sorted(assets_dir.rglob("*")):
        if not f.is_file() or f.name in SKIP_FILES:
            continue
        if f.suffix.lower() not in BINARY_EXTS:
            continue
        checked += 1
        rel = f.relative_to(assets_dir).as_posix()
        entry = entries.get(rel)
        if entry is None:
            missing.append(rel)
        elif not entry.get("license") or not entry.get("source"):
            incomplete.append(rel)

    return {
        "passed": not missing and not incomplete,
        "checked": checked,
        "missing": missing,
        "incomplete": incomplete,
    }


if __name__ == "__main__":
    import sys

    result = run_provenance(Path(__file__).resolve().parent.parent.parent)
    status = "PASS" if result["passed"] else "FAIL"
    print(f"provenance: {status} (checked={result['checked']})")
    for rel in result["missing"]:
        print(f"  missing manifest entry: {rel}")
    for rel in result["incomplete"]:
        print(f"  entry lacks license/source: {rel}")
    sys.exit(0 if result["passed"] else 1)
