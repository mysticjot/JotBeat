import { Scene } from 'phaser';
import { setPosition, setScene, addToInventory, removeFromInventory } from '../debug';
import { Player } from '../entities/Player';
import { Key } from '../entities/Key';
import { Door } from '../entities/Door';

export class Game extends Scene
{
    private player!: Player;
    private key!: Key;
    private door!: Door;
    private doorOpened = false;

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
        // Key on the row-8 main corridor (fully open floor, crosses the
        // col-9 wall strip through its only gap) — human-approved greybox
        // layout fix: the old (9,10) spot wedged the door approach behind
        // the col-10 wall column and blocked BL-005 twice.
        this.key = new Key(this, 7 * 32 + 16, 8 * 32 + 16);
        // Locked door further along the same corridor at tile (12, 8).
        this.door = new Door(this, 12 * 32 + 16, 8 * 32 + 16);

        // Ensure the door is positioned at the exact tile boundary so it fully blocks the tile
        const doorBody = this.door.body as Phaser.Physics.Arcade.Body;
        doorBody.setSize(32, 32);
        doorBody.setOffset(0, 0);

        this.physics.add.collider(this.player, layer);
        this.physics.add.collider(this.player, this.door, this.openDoor, undefined, this);
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
        this.door.update();
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

    private openDoor (player: Phaser.GameObjects.GameObject, door: Phaser.GameObjects.GameObject)
    {
        const doorSprite = door as Door;
        if (doorSprite.active && !this.doorOpened)
        {
            // Check if the player has a key
            const state = (window as any).__game?.state;
            if (state && state.inventory.keys > 0)
            {
                // Open the door and consume the key
                this.doorOpened = true;
                doorSprite.open();
                removeFromInventory('keys');
            }
        }
    }
}
