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

## ADR-0002: No Phaser runtime global in ESM builds — always explicit imports

- Status: accepted
- Date: 2026-08-15
- Context: The Phaser 4 npm package (`phaser.esm.js`) exports named modules only — there is no `window.Phaser` global at runtime. But the shipped type definitions declare a UMD global namespace, so `extends Phaser.Physics.Arcade.Sprite` (or any runtime `Phaser.*` value reference) **compiles clean under `tsc` and then dies at runtime** with `Phaser is not defined`. Type-position uses like `Phaser.Types.Core.GameConfig` are safe; value-position uses are not. This trap cost a real debugging cycle in Phase 1 and will recur, because Phaser 3 examples rely on the global everywhere.
- Decision: In `game/`, every Phaser class used at runtime is imported explicitly from `'phaser'` (e.g. `import { Physics, Scene } from 'phaser'`). Bare `Phaser.*` is allowed only in type positions. Any new runtime `Phaser.*` reference in a diff is a review rejection, same class as v3 API patterns.
- Consequences: Slightly more verbose imports. The compiler can no longer "validate" broken code, so a green `tsc` is trustworthy again. The Coder role must read this entry before writing scene code.

---

## ADR-0001: The QA debug hook is load-bearing — do not remove it

- Status: accepted
- Date: 2026-08-15
- Context: In Phase 1 the game exposes `window.__game.state` (scene, position, inventory, door states) plus a deterministic RNG seed hook. During Phase 1–3 this looks like unused dead code, and coding agents tend to "clean up" unused-looking code.
- Decision: The debug hook is a permanent, required part of the game build. It is the interface the entire scripted QA harness (Phase 4: Playwright fake input + state assertions) hangs off. Removing or renaming it is a breaking change requiring a new ADR that supersedes this one.
- Consequences: `window.__game.state` ships in production builds. The QA suite can assert game state deterministically; without it, Phase 4 verification is impossible.
