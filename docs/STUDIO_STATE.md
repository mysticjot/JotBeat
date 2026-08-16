# Studio State

Living status doc — updated at every phase gate (AGENTS.md §1 continuous-loop clause). Short and factual; history lives in CHANGELOG.md, decisions in DECISIONS.md.

## Phase status

- Phases 0–3: closed (gates demonstrated, see CHANGELOG).
- **Phase 4 (QA & Cert): CLOSED / CERTIFIED.** Anti-slop enforcement chain live (guardrails + narrative role + auditor gate, zero API cost for mechanical checks).
- **Phase 5 (Art & Audio): art pass COMPLETE pending final verify** — Kenney Tiny Dungeon (CC0) integrated with provenance manifest; Zelda-style multi-room map (46×40, 3 rooms + corridors, generator-built per D-0004); door-threshold fix (D-0003); all 10 ACs + oxygen timer green; baselines re-shot.

## Gate evidence

- Art-pass functional suite green locally: 19/19 Playwright specs on the new map (BVT + full AC matrix) + visual baselines re-shot against the Kenney look; vault door open/closed visually verified (`artifacts/screenshots/vault-door-*.png`).
- Export contract (D-0001): `jotbeat export` green locally — `dist/web/jotbeat-web.zip` produced; CI asserts the zip on every push.
- (superseded) Phase 4 verify green at commit `b48a2ed`.

## Active holds

- None.

## Next actions

- `jotbeat verify` for the art-pass gate, then commit + dual push and watch CI.
- Desktop/mobile wrappers are built but NOT smoke-tested yet (FLAG by design) — smoke-test before Phase 6 (itch.io release).
