# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [semver](https://semver.org/).

## [Unreleased]

### Added
- Phase 1 game scaffold: Phaser 4 + TypeScript + Vite from the official `template-vite-ts` (phaser 4.0.0).
- Boot → Title → Game scenes; greybox dungeon (LDtk project validated against official 1.5.3 schema, Tiled JSON export served from `assets/maps/`); wall collision; player movement; camera follow.
- `src/debug.ts`: `window.__game.state` + deterministic seed hook (ADR-0001).
- Playwright smoke suite (`game/tests/smoke.spec.ts`) asserting game state headless; CI runs build + tests.
- Phase 0 foundation: repository tree, document templates, state schemas, provider routing table, CI skeleton.
