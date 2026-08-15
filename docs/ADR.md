# Architecture Decision Records

> Format: one entry per decision. Newest at the top. Entries are immutable once accepted — supersede, don't rewrite.

## Format

```markdown
## ADR-NNNN: <title>
- Status: proposed | accepted | superseded by ADR-NNNN
- Date: YYYY-MM-DD
- Context: <forces at play>
- Decision: <what we decided>
- Consequences: <what this makes easier / harder>
```

---

## ADR-0001: The QA debug hook is load-bearing — do not remove it

- Status: accepted
- Date: 2026-08-15
- Context: In Phase 1 the game exposes `window.__game.state` (scene, position, inventory, door states) plus a deterministic RNG seed hook. During Phase 1–3 this looks like unused dead code, and coding agents tend to "clean up" unused-looking code.
- Decision: The debug hook is a permanent, required part of the game build. It is the interface the entire scripted QA harness (Phase 4: Playwright fake input + state assertions) hangs off. Removing or renaming it is a breaking change requiring a new ADR that supersedes this one.
- Consequences: `window.__game.state` ships in production builds. The QA suite can assert game state deterministically; without it, Phase 4 verification is impossible.
