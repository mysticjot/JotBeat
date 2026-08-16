"""Generate the SALTBOUND dungeon map — single source of truth for BOTH
game/maps/dungeon.ldtk (LDtk project, for the Level Designer to view) and
game/assets/maps/dungeon.json (Tiled format, loaded by Phaser).

Run from the repo root:

    python game/maps/build_map.py

Layout is declared as floor rectangles below; the wall shell is derived
(every void tile 8-adjacent to floor becomes wall), so the two outputs can
never drift. gid contract is documented in game/tools/build_kenney_assets.py.

Map graph (Zelda LttP-style room-corridor-room):

    Room A (spawn) --corridor--> Room B (Seal-Key)
                                    |
                                 corridor
                                    |
    Room C (vault):  west half --[LOCKED DOOR]-- east half (exit)
"""

import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LDTK_PATH = REPO_ROOT / "game" / "maps" / "dungeon.ldtk"
TILED_PATH = REPO_ROOT / "game" / "assets" / "maps" / "dungeon.json"

TILE = 32
WIDTH, HEIGHT = 46, 40

GID_FLOOR, GID_WALL, GID_VOID = 1, 2, 3
GID_FLOOR_VARIANTS = [4, 5, 6]

# Floor rectangles, inclusive tile coords: (x0, y0, x1, y1).
ROOM_A = (2, 15, 11, 23)
CORRIDOR_1 = (12, 18, 27, 19)
CONNECTOR = (27, 12, 28, 17)
ROOM_B = (24, 4, 37, 12)
CORRIDOR_2 = (24, 13, 25, 27)
ROOM_C = (26, 27, 41, 35)

FLOOR_RECTS = [ROOM_A, CORRIDOR_1, CONNECTOR, ROOM_B, CORRIDOR_2, ROOM_C]

# Vault split: solid wall column inside Room C with one door gap.
VAULT_WALL_X = 34
DOOR_TILE = (34, 31)

# Gameplay anchors — Game.ts and the Playwright specs import these numbers
# from here conceptually; if you move them, update LAYOUT in Game.ts and
# WAYPOINTS in game/tests/helpers.ts to match.
SPAWN_TILE = (7, 19)
KEY_TILE = (31, 8)
EXIT_TILE = (37, 31)

VARIANT_FRACTION = 0.12
VARIANT_SEED = 20260816  # fixed: same map every build


def build_grid() -> list[list[int]]:
    grid = [[GID_VOID] * WIDTH for _ in range(HEIGHT)]

    def carve(rect):
        x0, y0, x1, y1 = rect
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                grid[y][x] = GID_FLOOR

    for rect in FLOOR_RECTS:
        carve(rect)

    # Wall shell: void tiles 8-adjacent to floor become wall.
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if grid[y][x] != GID_VOID:
                continue
            if any(
                0 <= y + dy < HEIGHT and 0 <= x + dx < WIDTH
                and grid[y + dy][x + dx] == GID_FLOOR
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dx, dy) != (0, 0)
            ):
                grid[y][x] = GID_WALL

    # Vault split wall (the whole point of the locked door: without it the
    # exit is reachable without the key).
    for y in range(ROOM_C[1], ROOM_C[3] + 1):
        grid[y][VAULT_WALL_X] = GID_WALL

    # The door gap is walkable floor beneath the door sprite (the Door
    # entity is the blocker until opened).
    grid[DOOR_TILE[1]][DOOR_TILE[0]] = GID_FLOOR

    # Deterministic floor variants for texture.
    rng = random.Random(VARIANT_SEED)
    anchors = {SPAWN_TILE, KEY_TILE, DOOR_TILE, EXIT_TILE}
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (
                grid[y][x] == GID_FLOOR
                and (x, y) not in anchors
                and rng.random() < VARIANT_FRACTION
            ):
                grid[y][x] = rng.choice(GID_FLOOR_VARIANTS)
    return grid


def ascii_preview(grid: list[list[int]]) -> str:
    glyphs = {GID_FLOOR: ".", GID_WALL: "#", GID_VOID: " ", 4: ",", 5: ",", 6: ","}
    lines = []
    for y, row in enumerate(grid):
        line = "".join(glyphs[g] for g in row)
        for (tx, ty), ch in [
            (SPAWN_TILE, "P"), (KEY_TILE, "K"), (DOOR_TILE, "D"), (EXIT_TILE, "X"),
        ]:
            if ty == y:
                line = line[:tx] + ch + line[tx + 1:]
        lines.append(line)
    return "\n".join(lines)


def write_tiled(grid: list[list[int]]) -> None:
    data = [gid for row in grid for gid in row]
    doc = {
        "compressionlevel": -1,
        "height": HEIGHT,
        "infinite": False,
        "layers": [
            {
                "data": data,
                "height": HEIGHT,
                "id": 1,
                "name": "Dungeon",
                "opacity": 1,
                "type": "tilelayer",
                "visible": True,
                "width": WIDTH,
                "x": 0,
                "y": 0,
            }
        ],
        "nextlayerid": 2,
        "nextobjectid": 1,
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "tiledversion": "1.10.2",
        "tileheight": TILE,
        "tilesets": [
            {
                "columns": 6,
                "firstgid": 1,
                "image": "../tilemaps/dungeon.png",
                "imageheight": 32,
                "imagewidth": 192,
                "margin": 0,
                "name": "dungeon",
                "spacing": 0,
                "tilecount": 6,
                "tileheight": TILE,
                "tilewidth": TILE,
            }
        ],
        "tilewidth": TILE,
        "type": "map",
        "version": "1.10",
        "width": WIDTH,
    }
    TILED_PATH.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")


def write_ldtk(grid: list[list[int]]) -> None:
    grid_tiles = []
    for y, row in enumerate(grid):
        for x, gid in enumerate(row):
            t = gid - 1
            grid_tiles.append(
                {"px": [x * TILE, y * TILE], "src": [t * TILE, 0], "f": 0, "t": t, "d": [y * WIDTH + x], "a": 1}
            )

    layer_instance = {
        "__identifier": "Dungeon",
        "__type": "Tiles",
        "__cWid": WIDTH,
        "__cHei": HEIGHT,
        "__gridSize": TILE,
        "__opacity": 1.0,
        "__pxTotalOffsetX": 0,
        "__pxTotalOffsetY": 0,
        "__tilesetDefUid": 1,
        "__tilesetRelPath": "../assets/tilemaps/dungeon.png",
        "iid": "d396b30e-66b0-45ad-8811-208d0be82492",
        "levelId": 1,
        "layerDefUid": 1,
        "pxOffsetX": 0,
        "pxOffsetY": 0,
        "visible": True,
        "optionalRules": [],
        "seed": 0,
        "autoLayerTiles": [],
        "entityInstances": [],
        "gridTiles": grid_tiles,
        "intGridCsv": [0] * (WIDTH * HEIGHT),
        "overrideTilesetUid": None,
    }
    level = {
        "identifier": "Dungeon",
        "iid": "dc358492-b40c-4765-9516-58ff2e3a63b5",
        "uid": 1,
        "worldX": 0,
        "worldY": 0,
        "worldDepth": 0,
        "pxWid": WIDTH * TILE,
        "pxHei": HEIGHT * TILE,
        "__bgColor": "#1b1026",
        "bgColor": None,
        "useAutoIdentifier": True,
        "bgPivotX": 0,
        "bgPivotY": 0,
        "__smartColor": "#3b2d4d",
        "__bgPos": None,
        "externalRelPath": None,
        "fieldInstances": [],
        "__neighbours": [],
        "layerInstances": [layer_instance],
    }
    doc = {
        "$schema": "https://ldtk.io/files/JSON_SCHEMA.json",
        "__header__": {
            "fileType": "LDtk Project JSON",
            "app": "LDtk",
            "doc": "https://ldtk.io/json",
            "schemaVersion": "1.5.3",
            "appAuthor": "Sebastien Benard",
            "appVersion": "1.5.3",
            "url": "https://ldtk.io",
        },
        "iid": "40e550bc-87c8-4f32-8373-ab40b3ed27fc",
        "jsonVersion": "1.5.3",
        "appBuildId": 500000,
        "nextUid": 100,
        "identifierStyle": "Capitalize",
        "toc": [],
        "worlds": [
            {
                "identifier": "World",
                "iid": "cb4d4252-7155-430b-a51d-5dcd4b18c2b7",
                "levels": [level],
                "worldGridWidth": WIDTH * TILE,
                "worldGridHeight": HEIGHT * TILE,
                "worldLayout": "Free",
                "defaultLevelWidth": WIDTH * TILE,
                "defaultLevelHeight": HEIGHT * TILE,
            }
        ],
        "dummyWorldIid": "590202f8-ca0d-4a4a-8581-32492308c854",
        "worldLayout": "Free",
        "worldGridWidth": WIDTH * TILE,
        "worldGridHeight": HEIGHT * TILE,
        "defaultLevelWidth": WIDTH * TILE,
        "defaultLevelHeight": HEIGHT * TILE,
        "defaultPivotX": 0,
        "defaultPivotY": 0,
        "defaultGridSize": TILE,
        "defaultEntityWidth": 32,
        "defaultEntityHeight": 32,
        "bgColor": "#1b1026",
        "defaultLevelBgColor": "#1b1026",
        "exportLevelBg": False,
        "minifyJson": False,
        "backupOnSave": False,
        "backupLimit": 0,
        "exportTiled": False,
        "simplifiedExport": False,
        "imageExportMode": "None",
        "pngFilePattern": None,
        "levelNamePattern": "",
        "customCommands": [],
        "flags": [],
        "externalLevels": False,
        "defs": {
            "layers": [
                {
                    "__type": "Tiles",
                    "identifier": "Dungeon",
                    "type": "Tiles",
                    "uid": 1,
                    "gridSize": TILE,
                    "guideGridWid": 0,
                    "guideGridHei": 0,
                    "displayOpacity": 1.0,
                    "inactiveOpacity": 1.0,
                    "hideInList": False,
                    "hideFieldsWhenInactive": False,
                    "canSelectWhenInactive": True,
                    "renderInWorldView": True,
                    "pxOffsetX": 0,
                    "pxOffsetY": 0,
                    "parallaxFactorX": 0.0,
                    "parallaxFactorY": 0.0,
                    "parallaxScaling": False,
                    "requiredTags": [],
                    "excludedTags": [],
                    "intGridValues": [],
                    "intGridValuesGroups": [],
                    "autoRuleGroups": [],
                    "autoSourceLayerDefUid": None,
                    "tilesetDefUid": 1,
                    "tilePivotX": 0,
                    "tilePivotY": 0,
                    "uiFilterTags": [],
                    "useAsyncRender": False,
                }
            ],
            "entities": [],
            "tilesets": [
                {
                    "__cWid": 6,
                    "__cHei": 1,
                    "identifier": "Dungeon",
                    "uid": 1,
                    "relPath": "../assets/tilemaps/dungeon.png",
                    "pxWid": 192,
                    "pxHei": 32,
                    "tileGridSize": TILE,
                    "spacing": 0,
                    "padding": 0,
                    "tags": [],
                    "tagsSourceEnumUid": None,
                    "enumTags": [],
                    "customData": [],
                    "savedSelections": [],
                    "cachedPixelData": None,
                    "embedAtlas": None,
                }
            ],
            "enums": [],
            "externalEnums": [],
            "levelFields": [],
        },
        "levels": [level],
    }
    LDTK_PATH.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    grid = build_grid()
    write_tiled(grid)
    write_ldtk(grid)
    print(ascii_preview(grid))
    print(f"\nwrote {TILED_PATH} and {LDTK_PATH} ({WIDTH}x{HEIGHT} tiles)")
    print(f"spawn={SPAWN_TILE} key={KEY_TILE} door={DOOR_TILE} exit={EXIT_TILE}")


if __name__ == "__main__":
    main()
