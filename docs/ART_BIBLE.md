# Art Bible — Art Direction Document

> Owned by the Artist / Technical Artist. Style lock is machine-checkable, not a mood board (roadmap §12.1).
> Pillow validators enforce every field of `style_lock` on every generated asset; failure = asset rejected before it reaches the repo.
>
> **Locked 2026-08-16 (Creative Director art pass):** SALTBOUND: The Sunken Seal uses the Kenney
> Tiny Dungeon pack (CC0) as its base art. Roadmap §12.2 amended: CC0 library art is legal at any
> phase. Palette below is extracted from the shipped assets (`game/assets/tilemaps/dungeon.png`,
> `game/assets/sprites/*.png`), built by `game/tools/build_kenney_assets.py`.

## Style lock (machine-checkable)

```json
{
  "style_lock": "16-bit top-down dungeon, Kenney Tiny Dungeon (CC0), upscaled 16->32px nearest",
  "tile_size": 32,
  "palette": ["#eaa56c", "#763b36", "#262b44", "#3f2631", "#8b9bb4", "#52607c", "#c0cbdc", "#bd6c4a", "#cf8254", "#25956a", "#f7c282"],
  "lighting": "flat, no directional shading (pack style)",
  "outline": "pack-native dark outline (#262b44 / #3f2631)",
  "camera": "top-down",
  "must_tile": true,
  "transparent_background": true
}
```

The palette is extracted from the shipped Kenney-derived assets, then locked. Do not hand-drift it.

## Asset specification

| Asset | Size | Palette-locked | Tiles | Transparent | Provenance |
|---|---|---|---|---|---|
| tilemaps/dungeon.png | 192×32 (6 tiles) | yes | yes | n/a | Kenney Tiny Dungeon CC0 — `game/assets/manifest.json` |
| sprites/player.png | 32×32 | yes | no | yes | Kenney Tiny Dungeon CC0 |
| sprites/key.png | 32×32 | yes | no | yes | Kenney Tiny Dungeon CC0 |
| sprites/door-closed.png / door-open.png | 32×32 | yes | no | no (full-tile) | Kenney Tiny Dungeon CC0 |
| sprites/exit-doorway.png | 32×32 | yes | no | yes | Kenney Tiny Dungeon CC0 |

## Do / Don't

- Do: build new tiles/sprites from the Kenney Tiny Dungeon pack first; keep the 32px grid; upscale 16px sources x2 NEAREST only.
- Don't: no anti-aliased rescales, no palette colors outside the lock, no mixing in a second pack's style without Creative Director sign-off.

## Placeholder-first rule

Art starts as greybox/proxy assets behind the manifest interface. The pipeline proves itself on placeholders before any GPU session (roadmap §12.2). Greybox was replaced by the Kenney pass on 2026-08-16; any future placeholder follows the same manifest interface.
