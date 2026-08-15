# Art Bible — Art Direction Document

> Template. Owned by the Artist / Technical Artist. Style lock is machine-checkable, not a mood board (roadmap §12.1).
> Pillow validators enforce every field of `style_lock` on every generated asset; failure = asset rejected before it reaches the repo.

## Style lock (machine-checkable)

```json
{
  "style_lock": "<e.g. 16-bit top-down dungeon>",
  "tile_size": 32,
  "palette": ["#000000"],
  "lighting": "<e.g. soft top-left>",
  "outline": "<e.g. 1px dark>",
  "camera": "<e.g. top-down>",
  "must_tile": true,
  "transparent_background": false
}
```

The palette is extracted from approved concept art with Color Thief, then locked. Do not hand-drift it.

## Asset specification

| Asset | Size | Palette-locked | Tiles | Transparent | Provenance |
|---|---|---|---|---|---|
| | | | | | model + license, recorded in `game/assets/manifest.json` |

## Do / Don't

- Do:
- Don't:

## Placeholder-first rule

Art starts as greybox/proxy assets behind the manifest interface. The pipeline proves itself on placeholders before any GPU session (roadmap §12.2).
