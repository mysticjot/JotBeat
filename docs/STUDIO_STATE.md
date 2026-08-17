# Studio State

Living status doc — updated at every phase gate (AGENTS.md §1 continuous-loop clause). Short and factual; history lives in CHANGELOG.md, decisions in DECISIONS.md.

## Phase status

- Phases 0–3: closed (gates demonstrated, see CHANGELOG).
- **Phase 4 (QA & Cert): CLOSED / CERTIFIED.** Anti-slop enforcement chain live (guardrails + narrative role + auditor gate, zero API cost for mechanical checks).
- **Phase 5 (Art & Audio): art pass COMPLETE, verify GREEN** — Kenney Tiny Dungeon (CC0) integrated with provenance manifest; Zelda-style multi-room map (46×40, 3 rooms + corridors, generator-built per D-0004); door-threshold fix (D-0003); all 10 ACs + oxygen timer green; baselines re-shot. Committed as `afcd486`.

## Terminology (Creative Director ruling)

SALTBOUND is in **vertical-slice construction**. Nothing in current work is a "patch" — all work items are **build tasks** in the phase backlog against `docs/COMMERCIAL_BASELINE.md`. The game does not yet exist in its intended form, so there is nothing to patch. "Patch" is reserved strictly for post-ship fixes.

## Gate evidence

- Art-pass gate green: `jotbeat verify` PASS (BVT + QA viewport matrix + quality) at commit `afcd486`, cert `reports/cert/cert-20260816-202705.md`. Functional suite: 19/19 Playwright specs on the new map + visual baselines re-shot against the Kenney look; vault door open/closed visually verified (`artifacts/screenshots/vault-door-*.png`). LDtk output validated against the official 1.5.3 JSON schema (0 errors).
- Export contract (D-0001): `jotbeat export` green locally — `dist/web/jotbeat-web.zip` produced; CI asserts the zip on every push.
- (superseded) Phase 4 verify green at commit `b48a2ed`.

## Active holds

- **CONSTRUCTION HOLD (Creative Director ruling):** the current build is a mechanic test, not the game. All construction is held until `docs/GAME_DESIGN.md` (Game 1 scope: 3 areas + finale, ≥2 enemy types, canon beats, 15–25 min target) is approved by the Creative Director. On approval, COMMERCIAL_BASELINE.md gains the "matches GAME_DESIGN.md content list" bar and the build queue re-derives from GAME_DESIGN.md — every task maps to a beat or area. The JotBeat Console deliverable is also held (see BACKLOG Queued).

## Next actions (baseline build queue — HELD, see Active holds)

- BT-0 (gate, in flight): GAME_DESIGN.md written, awaiting Creative Director approval.
- BT-1 (in flight): `docs/COMMERCIAL_BASELINE.md` + gate wiring in `jotbeat verify` (QA runs it, Auditor blocks certs without it).
- BT-2: Camera stability under movement (roundPixels / deadzone / lerp) + 10s no-drift capture.
- BT-3: Animated character sprite sheet (CC0, idle + walk × 4 directions) wired to Phaser animation states.
- BT-4: CC0 audio coverage (ambient, footsteps, door locked/open, key pickup, low-oxygen warning, victory/game-over stings); volumes in config; manifest provenance.
- BT-5: Phase 5 generated-art pass owns overall asset-quality upgrade (CC0 set is the interim look).
- Desktop/mobile wrappers are built but NOT smoke-tested yet (FLAG by design) — smoke-test before Phase 6 (itch.io release).
