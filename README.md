# JotBeat

**An auditable AI game-production system: it plans, builds, tests, verifies, remembers, and explains every beat of development.**

Agents create — the system verifies. JotBeat turns a pitch into a milestone plan, builds each backlog item, proves it against acceptance criteria, and keeps the whole production ownable. The repo is the product: local-first, git-backed, human-readable, runnable without JotBeat.

Status: **Pre-production — Phase 0 (Foundation) complete.** See `JotBeat-Studio-Roadmap.md` for the full plan.

## Layout

```
game/        Phaser 4 + TypeScript game (Phase 1+)
studio/      Orchestration system (Python) — cli.py, providers.json, templates/
docs/        The codified context: GDD, TEST_PLAN, ART_BIBLE, NARRATIVE_BIBLE,
             BACKLOG, ADR, DECISIONS, STUDIO_STATE, BUDGET, CHANGELOG
state/       project-state.json, task-queue.json, events.jsonl (ledger)
artifacts/   screenshots, audio, builds, traces (git-lfs)
reports/     bvt, regression, cert, triage
```

## Quick start

```bash
# Materialize/regenerate the project tree from templates (Phase 0 gate)
python studio/cli.py init            # add --force to overwrite, --path DIR to target elsewhere

# Set up provider keys (never commit .env)
cp .env.example .env                 # fill in the slots you have; empty = provider inactive
```

## Working contract

`AGENTS.md` pins the rules for all work in this repo:

1. **Phase gates are the contract** — a phase is done when its gate is demonstrated, not asserted.
2. **Docs before code** — the agents read `docs/` and `state/`; skipping them means rebuilding the orchestrator twice.
3. **Phaser 4, not 3** — v3 API patterns are rejected on sight.
4. **The debug hook is non-negotiable** — `window.__game.state` is pinned in ADR-0001; the Phase 4 QA harness hangs off it.
5. **Keys stay out** — `.env` is gitignored; the ledger logs provider names, never credentials.

## Roadmap

| Phase | Contents | Gate |
|---|---|---|
| 0 — Foundation ✅ | repo tree, docs, state schemas, providers.json, CI | `jotbeat init` reproduces tree; CI green on empty build |
| 1 — Game Scaffold | Phaser 4 + Vite, LDtk greybox map, debug hook | Playwright reads `window.__game.state` headless; BVT green |
| 2 — Orchestrator Core | LangGraph state machine, model adapter, ledger, CLI | stub task flows through the loop with cost attached |
| 3 — Vertical Slice | 10 acceptance criteria (key/door/exit dungeon) | all ACs implemented, playable in placeholder art |
| 4 — QA & Cert | scripted Playwright QA, regression, adversarial audit | cert passes; planted bug gets kicked back |
| 5 — Art & Audio | Art Bible lock, Kaggle GPU batch, provenance manifest | slice looks/sounds coherent; every asset validates |
| 6 — Release Candidate | polish, semver, itch.io via butler | playable on itch.io; cost measured |
| 7 — Post-launch | dashboard, live ops, new genres | deferred |

## Cost model

Provider-routed model calls with per-role token caps and an escalation ceiling
(cheap model → 2 failures → frontier with shrunk context → 2 more → human ticket).
Target: **$0.36–0.54 cash per finished game**; free-chain best case $0.00. Art/audio
runs on Kaggle's free 30 GPU-hours/week in a weekly batch. Every call is ledgered
to `state/events.jsonl` — cost per game is a measured fact, not an estimate.

## License

Component licenses are tracked in the roadmap's License Matrix (§23); every generated
asset carries provenance (model + license) in `game/assets/manifest.json`.
