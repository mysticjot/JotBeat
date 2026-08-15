# JotBeat — Working Contract

These rules are the standing contract for all work in this repo. They come from the project owner and override agent habits. See `JotBeat-Studio-Roadmap.md` for the full roadmap; this file pins the enforcement rules.

## 1. Phase gates are the contract

Do NOT roll phases into one unverified blob. After each phase, run its gate check and stop:

- **Phase 0 done** ⟺ `jotbeat init` reproduces the tree from templates AND CI is green on an empty build.
- **Phase 1 done** ⟺ Playwright can read `window.__game.state` from a headless run AND BVT green in CI.
- **Phase 2 done** ⟺ a stub task flows through the full loop and lands in `events.jsonl` with a cost attached.
- Later phases: gate criteria are in the roadmap's phase sections. A phase is not complete until its gate is demonstrated, not asserted.

## 2. Docs before code

Never jump straight to a code scaffold. The agents read these later — skipping them means rebuilding the orchestrator twice:

- `docs/GDD.md`, `docs/TEST_PLAN.md`, `docs/ART_BIBLE.md`, `docs/NARRATIVE_BIBLE.md`, `docs/BACKLOG.md`, `docs/ADR.md`, `docs/BUDGET.md`, `docs/CHANGELOG.md`
- `studio/providers.json` (routing table)
- `state/project-state.json`, `state/task-queue.json`, `state/events.jsonl` (schemas)

## 3. Phaser 4, not 3

Coding agents have heavy Phaser 3 training-data bias and will silently write v3 APIs. The roadmap §7.1 stack is the guardrail. Tell-tale v3 patterns to reject: `this.physics.arcade` style calls or config shapes that don't match the Phaser 4 template from `npm create @phaserjs/game@latest`. When in doubt, check against the generated template, not memory.

## 4. The debug hook is non-negotiable

`window.__game.state` (scene, position, inventory, door states) plus a deterministic RNG seed hook look like dead weight in Phase 1, but the entire Phase 4 QA harness hangs off them. They are pinned in `docs/ADR.md` (ADR-0001). Do not "clean up" or remove them, even if they appear unused.

## 5. Keys stay out

- `.env` must be in `.gitignore` **before** any real keys go in.
- Keys live only in `.env` — never in the repo, never in prompts, never in `state/events.jsonl`.
- The ledger logs provider names, never credentials.
- `studio/models.py` activates only providers whose keys exist in `.env`.

## 6. Quality gates run after every coding phase

After ANY coding work — and always before declaring a phase gate passed — run:

```
python studio/cli.py quality
```

This runs both deterministic scanners (no LLM, no network calls with credentials):

- **aislop** (Python + slop patterns, lint, security) — error-level findings must be **0**.
- **fallow** (TS/JS module graph) — `dead-code` and `dupes` must be clean.

Rules:

- Fix findings for real. Mechanical cleanup: `aislop fix --safe` (reversible fixes only).
- Suppress only with a documented reason in the suppression itself — see `.fallowrc.json`
  for the pattern (e.g. `DebugState` is exempted because ADR-0001 pins it for Phase 4 QA).
- `fallow health` is informational until Phase 4 (its CRAP estimate assumes 0% coverage).
- CI runs this same gate; a failing quality gate blocks the build like any other gate.
- Never lower `.aislop/config.yml` `ci.failBelow` to make CI pass — ratchet up only.
