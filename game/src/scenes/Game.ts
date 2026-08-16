import { Scene } from 'phaser';
import { setPosition, setScene, addToInventory } from '../debug';
import { Player } from '../entities/Player';
import { Key } from '../entities/Key';

export class Game extends Scene
{
    private player!: Player;
    private key!: Key;

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
        // Place the key on a guaranteed floor tile at (9, 10) => pixel (304, 336)
        // Map row 10 (0-indexed): data[10*30+9] = 1 (floor), far from the wall at col 10
        this.key = new Key(this, 9 * 32 + 16, 10 * 32 + 16);

        this.physics.add.collider(this.player, layer);
        // Use overlap for pickup detection
        this.physics.add.overlap(this.player, this.key, this.pickUpKey, undefined, this);

        this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    update (): void
    {
        this.player.update();
        this.key.update();
        setPosition(this.player.x, this.player.y);
    }

    private pickUpKey (player: Phaser.GameObjects.GameObject, key: Phaser.GameObjects.GameObject)
    {
        if (!key.active) {
            return;
        }
        key.destroy();
        addToInventory('keys');
    }
}
