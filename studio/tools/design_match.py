"""tools/design_match.py — commercial-baseline design-match check
(docs/COMMERCIAL_BASELINE.md §8).

The build must match docs/GAME_DESIGN.md's content list (area count, enemy
types, narrative beats, state frame). A build that doesn't match its
GAME_DESIGN.md is not a game and fails the gate by definition.

Deterministic, no model calls: parses the GAME_DESIGN.md "Content checklist"
section and verifies each element against the game source:
  - state frame  -> scene files exist under game/src/scenes/
  - enemy types  -> entity classes exist under game/src/entities/
  - lungstone    -> referenced in game/src/
  - card lines   -> lines marked `verbatim` appear verbatim in game/src/
  - area count   -> map files under game/assets/maps/

Called by `jotbeat verify`; the cert writer embeds the verdict in the
Commercial Baseline section. Expected to FAIL on the mechanic-test build
until the vertical slice catches up to the design.
"""

from __future__ import annotations

import re
from pathlib import Path

DESIGN_DOC = "docs/GAME_DESIGN.md"

# State-frame token -> scene file. The frame lists play as "play"; the scene
# is named Game. Everything else maps 1:1 by capitalization.
STATE_FRAME_SCENES = {
    "boot": "Boot.ts",
    "title": "Title.ts",
    "intro": "Intro.ts",
    "play": "Game.ts",
    "pause": None,  # overlay in the Game scene, not a scene file
    "victory": "Victory.ts",
    "game over": "GameOver.ts",
    "restart": None,  # a transition, not a scene
}


def _read_sources(root: Path) -> str:
    """All game TS source, for verbatim line + symbol searches."""
    src = root / "game" / "src"
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace") for p in src.rglob("*.ts")
    )


def run_design_match(root: Path) -> dict:
    """Check build vs GAME_DESIGN.md. Returns
    {"passed": bool, "checks": [{"name", "passed", "detail"}]}."""
    root = Path(root)
    doc_path = root / DESIGN_DOC
    if not doc_path.exists():
        return {
            "passed": False,
            "checks": [
                {
                    "name": "design doc",
                    "passed": False,
                    "detail": f"{DESIGN_DOC} is missing — nothing to match against",
                }
            ],
        }
    doc = doc_path.read_text(encoding="utf-8")
    checks: list[dict] = []

    # --- state frame: scenes from the checklist's "State frame:" line exist
    scenes_dir = root / "game" / "src" / "scenes"
    missing_scenes = [
        f"{token} ({fname})"
        for token, fname in STATE_FRAME_SCENES.items()
        if fname and f"{token} " in doc + " " and not (scenes_dir / fname).exists()
    ]
    checks.append(
        {
            "name": "state frame",
            "passed": not missing_scenes,
            "detail": (
                "all state-frame scenes exist"
                if not missing_scenes
                else "missing scenes: " + ", ".join(missing_scenes)
            ),
        }
    )

    # --- enemy types: "(Drowner, Silt Eel)" on the enemy checklist line
    enemies: list[str] = []
    m = re.search(r"enemy types?[^\n]*\(([^)]+)\)", doc, re.IGNORECASE)
    if m:
        enemies = [e.strip() for e in m.group(1).split(",") if e.strip()]
    entities_dir = root / "game" / "src" / "entities"
    missing_enemies = [
        e for e in enemies if not (entities_dir / f"{e.replace(' ', '')}.ts").exists()
    ]
    checks.append(
        {
            "name": "enemy types",
            "passed": bool(enemies) and not missing_enemies,
            "detail": (
                f"{len(enemies)} enemy types built"
                if enemies and not missing_enemies
                else f"required {enemies or '(none parsed)'}; missing: {missing_enemies}"
            ),
        }
    )

    # --- lungstone (oxygen-as-relic is mechanical canon)
    source = _read_sources(root)
    has_lungstone = "Lungstone" in source
    checks.append(
        {
            "name": "lungstone relic",
            "passed": has_lungstone,
            "detail": (
                "lungstone referenced in game source"
                if has_lungstone
                else "no Lungstone in game/src — oxygen is a bare timer, not the relic"
            ),
        }
    )

    # --- verbatim card lines: "..." quotes on lines marked verbatim
    cards = []
    for line in doc.splitlines():
        if "verbatim" in line.lower():
            cards += re.findall(r'"([^"]{10,})"', line)
            cards += re.findall(r"(?<!\*)\*([A-Z][^*\"]{10,})\*(?!\*)", line)
    missing_cards = [c for c in cards if c not in source]
    checks.append(
        {
            "name": "narrative beats (card lines)",
            "passed": bool(cards) and not missing_cards,
            "detail": (
                f"all {len(cards)} verbatim card lines in game source"
                if cards and not missing_cards
                else f"{len(cards) - len(missing_cards)}/{len(cards)} card lines present; "
                f"missing: {missing_cards or cards}"
            ),
        }
    )

    # --- area count: "N areas" on the checklist vs built maps
    areas_req = 0
    m = re.search(r"(\d+) areas?", doc)
    if m:
        areas_req = int(m.group(1))
    maps_dir = root / "game" / "assets" / "maps"
    maps_built = len(list(maps_dir.glob("*.json"))) if maps_dir.is_dir() else 0
    checks.append(
        {
            "name": "area count",
            "passed": areas_req > 0 and maps_built >= areas_req,
            "detail": (
                f"{maps_built} maps built for {areas_req} areas"
                + (" (heuristic: one map per area)" if maps_built < areas_req else "")
            ),
        }
    )

    return {"passed": all(c["passed"] for c in checks), "checks": checks}


if __name__ == "__main__":
    import sys

    result = run_design_match(Path(__file__).resolve().parent.parent.parent)
    print(f"design match: {'PASS' if result['passed'] else 'FAIL'}")
    for c in result["checks"]:
        print(f"  {'PASS' if c['passed'] else 'FAIL'}  {c['name']}: {c['detail']}")
    sys.exit(0 if result["passed"] else 1)
