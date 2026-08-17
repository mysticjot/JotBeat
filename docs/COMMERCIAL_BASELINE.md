# Commercial Baseline

Gate-blocking checklist. QA runs this on **every** `jotbeat verify` from now on.
Any FAIL blocks the gate — no exceptions, no "known issue" waivers. Work items
against this checklist are **build tasks** (BT-n), never "patches" (Creative
Director ruling, docs/STUDIO_STATE.md).

How it is enforced (deterministic, no model calls):

- **Player-mode pre-flight** — `game/tests/baseline.spec.ts` (Playwright, part
  of the verify viewport matrix). Drives the built game as a player and
  captures a screenshot at every state into `artifacts/screenshots/baseline/`.
- **Provenance** — `studio/tools/provenance.py`, run by `jotbeat verify`.
- **Design match** — `studio/tools/design_match.py`, run by `jotbeat verify`.
- **Text** — the aislop slop gate (AGENTS.md §6) covers player-facing strings.
- **Cert** — every cert report carries a "Commercial Baseline" section with one
  PASS/FAIL line per item and evidence pointers.

## 1. Frame

boot → title (start/settings) → intro → play → pause (resume/settings/quit) →
transitions on both victory and game over → **no dead ends anywhere**.

Every state offers the player a way forward. A screen the player cannot leave
is a gate-blocking defect, no matter how good it looks.

Checked by: `baseline frame:` tests in `game/tests/baseline.spec.ts`.

## 2. Character/craft

- Animated sprite: idle + walk × direction. Animation contract: keys
  `idle`, `walk-up`, `walk-down`, `walk-left`, `walk-right` on the player.
- No static-tile actors.
- Camera stable under movement (roundPixels/deadzone).
- No placeholder assets past vertical slice (manifest `placeholder: false`
  must be honest).

Checked by: `baseline character:` tests in `game/tests/baseline.spec.ts`.

## 3. Audio

Every player action and state change has a sound; volumes in config.

Expected keys in the audio cache: `sfx-footstep`, `sfx-key-pickup`,
`sfx-door-locked`, `sfx-door-open`, `sfx-low-oxygen`, `sfx-victory`,
`sfx-gameover`, `music-ambient`.

Checked by: `baseline audio:` test in `game/tests/baseline.spec.ts`.

## 4. Onboarding

Player knows where they are and why within 10 seconds of Start.

Checked by: `baseline onboarding:` test in `game/tests/baseline.spec.ts` —
an orientation/objective line must be on screen in the Game scene within 10s
of pressing Start (the HUD key counter alone does not count).

## 5. Text

All player-facing strings through Narrative Designer + slop check.

Checked by: the aislop slop gate in `jotbeat verify` (quality gate green =
PASS). New player-facing strings go through the Narrative Designer role before
they land; canonical lines pinned in docs/NARRATIVE_BIBLE.md are not edited by
code tasks.

## 6. Provenance

Every asset in `game/assets/manifest.json` with license.

Checked by: `studio/tools/provenance.py` — every binary asset file under
`game/assets/` must have a manifest entry with a non-empty `license` and
`source`. Fails hard on missing entries.

## 7. Player-mode pre-flight

Before any build reaches the Creative Director, QA must play it end-to-end as
a player (bot + screenshot capture at every state) and file its own defect
list. Human playtest is for feel and judgment, NOT for finding missing title
screens.

Checked by: the `baseline frame:` walkthroughs completing with a screenshot
at every state (`artifacts/screenshots/baseline/`), plus the filed defect list
(`reports/triage/`).

## 8. Design match

The build must match `docs/GAME_DESIGN.md`'s content list (area count, enemy
types, narrative beats, state frame). A build that doesn't match its
GAME_DESIGN.md is not a game and fails the gate by definition.

Checked by: `studio/tools/design_match.py` — parses the GAME_DESIGN.md
content checklist and verifies, deterministically: the state-frame scenes
exist, the named enemy types and the lungstone exist as game code, the
verbatim card lines appear in the game source, and the area count is built.
Expected to FAIL on the mechanic-test build until the vertical slice catches
up to the design.

## 9. Auditor rule

A gate cert without a completed baseline section is invalid.

Enforced by: `studio/tools/cert.py` always emits the "Commercial Baseline"
section; if the QA run produced no baseline evidence, every item reports FAIL
and the run is NOT CERTIFIED.
