# Decision Log

Numbered, dated, locked. New decisions append; old ones are amended, never rewritten. ADR.md stays for architecture records; this log is for Creative Director product/pipeline decisions.

## D-0001 — Every JotBeat game is exportable to any platform from day one (2026-08-16, locked)

**Decision:** Exportability is a standing contract, not a release-phase scramble. `python studio/cli.py export` must always produce, from the repo root:

- `dist/web/` — the Vite static build (from `game/dist/`) plus `dist/web/jotbeat-web.zip`, itch.io-ready with `index.html` at the ZIP ROOT. The zip path + size is a required printed output.
- `dist/desktop/` — an Electron thin shell that loads the web build (Windows first; mac/Linux same pipeline).
- `dist/mobile/` — a Capacitor thin shell (`webDir` → web build, Android first).

The web build is the single artifact and always works standalone; wrappers are thin shells around it. Exit 0 requires only web build + zip — wrapper failures degrade to printed FLAGs, never hard failures. CI runs export with `JOTBEAT_EXPORT_WRAPPERS=0` (scaffold-only, keeps CI fast) and asserts the zip exists and is non-empty.

## D-0002 — Wrapper tool choices and the platform adapter rule (2026-08-16, locked)

**Decision:**

- **Desktop: Electron.** Tauri was considered only if a Rust toolchain (`cargo`) is present; Electron is the locked default because it needs nothing beyond npm. Wrapper deps live in repo-root `desktop/`, never in `game/package.json` (would bloat every CI `npm ci`).
- **Mobile: Capacitor** (`@capacitor/core` + `cli` + `android` in repo-root `mobile/`), `webDir` pointing at the web build. Same rule: not in `game/package.json`.
- **Platform adapter rule:** game code must NEVER import wrapper APIs (Electron, Capacitor) directly. All platform features go through `game/src/platform/` (`save`, `load`, `requestFullscreen`, `haptic`), whose WEB implementation (localStorage, Fullscreen API, `navigator.vibrate`) is the always-working default fallback. Wrappers inject their own implementation via `setPlatformAdapter()` at boot. The adapter is the contract.

## D-0003 — Door-threshold: opening a door requires a square approach (2026-08-16, locked)

**Decision:** The locked door's physics body stays a full-tile static blocker, but the open trigger is gated: `Game.openDoor` only fires when the player's center is aligned with the door's center within `DOOR_APPROACH_TOLERANCE` (12px) on the approach axis. A diagonal graze clipping the door body's corner no longer consumes the key. On open, the door swaps to the `door-open` texture and its body disables cleanly.

## D-0004 — Map layout is generated, not hand-edited (2026-08-16, locked)

**Decision:** `game/maps/build_map.py` is the single source of truth for the dungeon layout (floor rects + derived wall shell + gameplay anchors) and emits BOTH `game/maps/dungeon.ldtk` (LDtk 1.5.3, for viewing) and `game/assets/maps/dungeon.json` (Tiled, for Phaser) — the two cannot drift. Hand-editing either output is void. Gameplay anchors move only by moving them in the generator and syncing `LAYOUT` in `Game.ts` and the spec waypoints.
