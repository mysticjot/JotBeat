import { Scene } from 'phaser';
import { setPosition, setScene, addToInventory, removeFromInventory, setVictory, setGameOver, setOxygen, debugSetOxygen } from '../debug';
import { Player } from '../entities/Player';
import { Key } from '../entities/Key';
import { Door } from '../entities/Door';

export class Game extends Scene
{
    private player!: Player;
    private key!: Key;
    private door!: Door;
    private doorOpened = false;
    private oxygen = 100;
    private oxygenTimer!: Phaser.Time.TimerEvent;

    constructor ()
    {
        super('Game');
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    create ()
    {
        setScene('Game');
        setOxygen(100);
        debugSetOxygen(100);
        this.oxygen = 100;

        const map = this.make.tilemap({ key: 'dungeon' });
        const tiles = map.addTilesetImage('greybox', 'greybox');
        const layer = map.createLayer('Dungeon', tiles!, 0, 0)!;

        //  Greybox tileset: gid 1 = floor, gid 2 = wall.
        map.setCollisionBetween(2, 2, true, false, 'Dungeon');

        //  Arcade world bounds default to the CANVAS size (640x480), not the
        //  map — with collideWorldBounds the player hits an invisible wall at
        //  x=630 and can never reach the exit at x=656 (blocked BL-006).
        this.physics.world.setBounds(0, 0, map.widthInPixels, map.heightInPixels);

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

        // Exit trigger: an invisible zone on the far east of the map.
        // Choose a wide-open floor tile not blocked by any wall — tile (20, 8)
        // is on the row-8 corridor, far past the door at (12, 8) and fully open.
        const exitTileCol = 20;
        const exitTileRow = 8;
        const exitZone = this.add.zone(exitTileCol * 32 + 16, exitTileRow * 32 + 16, 32, 32);
        this.physics.add.existing(exitZone, true);  // immovable static body
        this.physics.add.overlap(this.player, exitZone, this.triggerVictory, undefined, this);

        // Oxygen timer: drain 1 unit per second. When it hits 0, game over.
        this.oxygenTimer = this.time.addEvent({
            delay: 1000,
            callback: () => {
                const query = new URLSearchParams(window.location.search);
                const fastOxygen = query.get('fastOxygen');
                const drainRate = fastOxygen === '1' ? 10 : 1;
                this.oxygen = Math.max(0, this.oxygen - drainRate);
                setOxygen(this.oxygen);
                debugSetOxygen(this.oxygen);
                if (this.oxygen <= 0) {
                    this.triggerGameOver();
                }
            },
            loop: true
        });

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

    private triggerVictory (player: Phaser.GameObjects.GameObject, exit: Phaser.GameObjects.GameObject)
    {
        if (!this.doorOpened) {
            // The exit should only trigger after the door is unlocked/open.
            return;
        }
        // Stop the oxygen timer when the game ends
        this.oxygenTimer.remove();
        // Transition to the Victory scene and mark it in the debug state.
        setVictory();
        this.scene.start('Victory');
    }

    private triggerGameOver ()
    {
        // Stop the oxygen timer to prevent re-triggering
        this.oxygenTimer.remove();
        setGameOver();
        this.scene.start('GameOver');
    }
}
