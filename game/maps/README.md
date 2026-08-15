# Maps

- `dungeon.ldtk` — the LDtk project (source of truth, edited in the [LDtk](https://ldtk.io) app by the Level Designer).
- `../assets/maps/dungeon.json` — the Tiled-format export that Vite serves and Phaser loads via `this.load.tilemapTiledJSON`.

Workflow: edit `dungeon.ldtk` in LDtk → export Tiled JSON → place it in `game/assets/maps/`.
The Phase 1 greybox was generated programmatically and validated against the official LDtk 1.5.3 JSON schema.
