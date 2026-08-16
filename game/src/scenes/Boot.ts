import { Scene } from 'phaser';

export class Boot extends Scene
{
    constructor ()
    {
        super('Boot');
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    preload ()
    {
        //  Kenney Tiny Dungeon (CC0) — provenance in assets/manifest.json.
        //  Rebuild from the pack with game/tools/build_kenney_assets.py.
        this.load.image('dungeon-tiles', 'tilemaps/dungeon.png');
        this.load.image('player', 'sprites/player.png');
        this.load.image('key', 'sprites/key.png');
        this.load.image('door-closed', 'sprites/door-closed.png');
        this.load.image('door-open', 'sprites/door-open.png');
        this.load.image('exit-doorway', 'sprites/exit-doorway.png');
        this.load.tilemapTiledJSON('dungeon', 'maps/dungeon.json');
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    create ()
    {
        this.scene.start('Title');
    }
}
