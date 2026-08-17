# Baseline initial run — Commercial Baseline vs current build

First player-mode pre-flight of `docs/COMMERCIAL_BASELINE.md` (build task BT-1).
Run: `jotbeat verify` at commit `9916ad2` (+ BT-1 wiring), cert
`reports/cert/cert-20260817-001606.md`, screenshots
`artifacts/screenshots/baseline/` (8 states captured). QA matrix:
62 passed / 4 baseline failures × 3 viewports; BVT PASS; quality gate PASS.

This file is QA's filed defect list per checklist §8 (player-mode pre-flight).

## Per-item verdicts

| Item | Verdict | Evidence |
| --- | --- | --- |
| 1. Frame | **FAIL** | Victory screen is a dead end — Enter does nothing (`05-victory.png`, spec line 54 assertion). Game-over path PASS: GameOver → Enter → Title (`06-gameover.png`, `07-title-after-gameover.png`). |
| 2. Character/craft | **FAIL** | Player is a static tile: animations `idle`, `walk-up/down/left/right` all missing (`03-gameplay.png`). Camera sub-check PASS: `roundPixels=true` already set via `startFollow(player, true, …)` in `game/src/scenes/Game.ts:122`; no deadzone. |
| 3. Audio | **FAIL** | Zero audio coverage — all 8 contract sounds missing from the cache (`sfx-footstep`, `sfx-key-pickup`, `sfx-door-locked`, `sfx-door-open`, `sfx-low-oxygen`, `sfx-victory`, `sfx-gameover`, `music-ambient`). No volume config exists. |
| 4. Onboarding | **FAIL** | No orientation/objective text within 10s of Start (`08-onboarding.png`); Game scene shows only the `Keys: 0` HUD. Title subtitle ("The Sunken Seal") is the only framing the player gets, and it says where-ish, not why. |
| 5. Text | **PASS** | Quality gate green (aislop 0 errors); existing player-facing strings are plain and specific. Narrative Designer routing is process, not scanner. |
| 6. Provenance | **PASS** | `game/assets/manifest.json` covers all 8 binary assets with license + source (favicon.png entry added in BT-1 — Phaser template, MIT). |
| 7. Design match | **FAIL** (expected — mechanic-test build) | `docs/GAME_DESIGN.md` content checklist vs build, via `studio/tools/design_match.py`: state frame missing `Intro.ts`; enemies Drowner + Silt Eel not built; no `Lungstone` in game/src (oxygen is a bare timer); 1/3 verbatim card lines present (missing the Curator handoff + hook card); 1 map built for 3 areas + finale. Item added 2026-08-17 per Creative Director directive — a build that doesn't match its GAME_DESIGN.md fails the gate by definition. |
| 8. Player-mode pre-flight | **FAIL** | Walkthrough incomplete (Victory dead end). Screenshots captured at all 8 states; this report is the defect list. |
| 9. Auditor rule | wiring verified | `reports/cert/latest.md` always carries the Commercial Baseline section; verify exits 1 when any item fails. |

Expected failures confirmed, not assumed: static player tile ✔, zero audio ✔.
Expected "possible camera jitter" did NOT reproduce at the config level —
`roundPixels` is already on; BT-2's 10s movement capture is still owed as
evidence of pixel stability under motion.

## Additional defects observed during the playthrough

- **Pause is invisible.** `04-paused.png` is indistinguishable from live
  gameplay — no overlay, dim, or "Paused" text. The player cannot tell the
  game is paused (frame checklist: pause offers resume/settings/quit;
  currently it offers an unlabeled Space toggle only).
- **No settings anywhere.** Title has Start only; pause has no menu. Frame
  checklist calls for start/settings on title and resume/settings/quit on
  pause.
- **No intro beat.** Title → Enter drops straight into the dungeon with no
  transition or framing (frame checklist: title → intro → play).

## Fix queue (priority order)

1. **Victory dead end (Blocker).** Victory scene accepts Enter → Title,
   mirroring GameOver. One-line class of fix; unblocks the whole frame item.
   Regression test already exists: `baseline frame: victory path`.
2. **BT-3 — animated player sprite (Blocker).** CC0 4-direction walk + idle
   sheet, wired to the animation contract keys in §2 (`idle`, `walk-*`).
3. **BT-4 — audio coverage (Blocker).** CC0 sounds for the 8 contract keys;
   volumes in config; manifest provenance entries.
4. **Onboarding line (Major).** One plain, specific objective line on game
   start (through Narrative Designer; slop rules apply). New build task.
5. **Pause affordance + menu (Major).** Visible paused state; resume /
   settings / quit. New build task.
6. **Title settings + intro transition (Minor).** Completes the frame
   checklist's full chain. New build task.
7. **BT-2 — camera movement capture (Minor).** 10s no-drift capture as
   evidence; config already passes the roundPixels/deadzone check.
8. **Design match (Blocker, umbrella).** The vertical-slice build queue closes
   this by construction: Intro scene + restart flow, Drowner + Silt Eel
   entities, lungstone relic replacing the bare oxygen timer, Curator handoff
   + hook card lines (Narrative Designer owns the verbatim text), 3 area maps
   + finale. Until then every cert reads Design match FAIL — that is correct.
