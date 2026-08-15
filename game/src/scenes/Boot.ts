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
        //  Greybox assets only — real art arrives in Phase 5 behind the manifest.
        this.load.image('greybox', 'tiles/greybox.png');
        this.load.image('player', 'sprites/player.png');
        this.load.tilemapTiledJSON('dungeon', 'maps/dungeon.json');
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    create ()
    {
        this.scene.start('Title');
    }
}
