import { Scene } from 'phaser';

export class Boot extends Scene
{
    constructor ()
    {
        super('Boot');
    }

    preload ()
    {
        //  Greybox assets only — real art arrives in Phase 5 behind the manifest.
        this.load.image('greybox', 'tiles/greybox.png');
        this.load.image('player', 'sprites/player.png');
        this.load.tilemapTiledJSON('dungeon', 'maps/dungeon.json');
    }

    create ()
    {
        this.scene.start('Title');
    }
}
