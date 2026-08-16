"""Build the game's 32px tileset and entity sprites from the Kenney Tiny
Dungeon pack (CC0, provenance in game/assets/manifest.json).

Deterministic: same pack in -> same PNGs out. Run from the repo root:

    python game/tools/build_kenney_assets.py

Kenney tiles are 16x16; the game grid is 32px, so everything is upscaled
x2 with NEAREST (pixel art stays crisp). The tilemap gid contract used by
Game.ts and build_map.py:

    gid 1 = floor        gid 4 = floor variant
    gid 2 = wall         gid 5 = floor variant
    gid 3 = void (solid) gid 6 = floor variant

Collision is setCollisionBetween(2, 3) — wall and void block, every floor
gid walks.
"""

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_TILES = REPO_ROOT / "artifacts" / "asset-src" / "kenney-tiny-dungeon" / "Tiles"
ASSETS = REPO_ROOT / "game" / "assets"

# Kenney tile indices (see artifacts/asset-src/kenney-tiny-dungeon/Tiles/).
# Floor is the smooth tan set — the 36-39 planks are wall cladding and read
# as jail-bar banding when tiled over a room (verified visually).
TILESET_ORDER = [48, 14, 0, 49, 53, 42]  # floor, wall, void, 3 floor variants
SPRITES = {
    "player.png": 112,         # hooded tide-thief (Maren)
    "key.png": 101,            # sigil emblem — the Seal-Key
    "door-closed.png": 45,     # arched wooden door, stone frame
    "door-open.png": 33,       # same door, open
    "exit-doorway.png": 54,    # dark stone doorway behind the door
}


def load_tile(index: int) -> Image.Image:
    path = PACK_TILES / f"tile_{index:04d}.png"
    if not path.exists():
        raise FileNotFoundError(f"Kenney tile missing: {path}")
    return Image.open(path).convert("RGBA").resize((32, 32), Image.NEAREST)


def main() -> None:
    tileset = Image.new("RGBA", (32 * len(TILESET_ORDER), 32))
    for i, index in enumerate(TILESET_ORDER):
        tileset.paste(load_tile(index), (i * 32, 0))
    out_dir = ASSETS / "tilemaps"
    out_dir.mkdir(parents=True, exist_ok=True)
    tileset.save(out_dir / "dungeon.png")

    for name, index in SPRITES.items():
        load_tile(index).save(ASSETS / "sprites" / name)

    print(f"tileset: {out_dir / 'dungeon.png'} (gids 1-{len(TILESET_ORDER)})")
    for name in SPRITES:
        print(f"sprite:  {ASSETS / 'sprites' / name}")


if __name__ == "__main__":
    main()
