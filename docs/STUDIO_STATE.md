# Studio State

Living status doc — updated at every phase gate (AGENTS.md §1 continuous-loop clause). Short and factual; history lives in CHANGELOG.md, decisions in DECISIONS.md.

## Phase status

- Phases 0–3: closed (gates demonstrated, see CHANGELOG).
- **Phase 4 (QA & Cert): CLOSED / CERTIFIED.** Anti-slop enforcement chain live (guardrails + narrative role + auditor gate, zero API cost for mechanical checks).
- **Phase 5 (Art & Audio): STARTING** — bible-approved art pass in progress (Kenney CC0 integration + provenance manifest, per Roadmap §12.2 amendment).

## Gate evidence

- Last `jotbeat verify` green at commit `b48a2ed` (BVT + Playwright viewport matrix + §6 quality gate all PASS; cert report in `reports/cert/latest.md`).
- Export contract (D-0001) landed after that commit: `jotbeat export` green locally — `dist/web/jotbeat-web.zip` produced; CI asserts the zip on every push.

## Active holds

- None beyond the bible-approved Phase 5 art pass.

## Next actions

- Kenney CC0 asset integration with provenance manifest (pack, author, license, source URL).
- Zelda-style multi-room LDtk map rebuild + door-threshold fix.
- Re-shoot visual baselines, then `jotbeat verify` and close the Phase 5 art-pass gate.
- Desktop/mobile wrappers are built but NOT smoke-tested yet (FLAG by design) — smoke-test before Phase 6 (itch.io release).
