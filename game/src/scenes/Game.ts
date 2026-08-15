import { Scene } from 'phaser';
import { setPosition, setScene } from '../debug';
import { Player } from '../entities/Player';

export class Game extends Scene
{
    private player!: Player;

    constructor ()
    {
        super('Game');
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    create ()
    {
        setScene('Game');

        const map = this.make.tilemap({ key: 'dungeon' });
        const tiles = map.addTilesetImage('greybox', 'greybox');
        const layer = map.createLayer('Dungeon', tiles!, 0, 0)!;

        //  Greybox tileset: gid 1 = floor, gid 2 = wall.
        map.setCollisionBetween(2, 2, true, false, 'Dungeon');

        this.player = new Player(this, 5 * 32 + 16, 5 * 32 + 16);
        this.physics.add.collider(this.player, layer);

        this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    update (): void
    {
        this.player.update();
        setPosition(this.player.x, this.player.y);
    }
}
