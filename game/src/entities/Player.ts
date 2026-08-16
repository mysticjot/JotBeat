import { Physics, Scene } from 'phaser';

const SPEED = 160;

export class Player extends Physics.Arcade.Sprite
{
    private cursors: Phaser.Types.Input.Keyboard.CursorKeys;

    constructor (scene: Scene, x: number, y: number)
    {
        super(scene, x, y, 'player');

        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.setCollideWorldBounds(true);
        // Body smaller than the 32px tile: a full-tile body has ZERO
        // clearance in one-tile corridors — 2px of drift wedges it on the
        // corner of a wall tile (blocked BL-005 thrice). 20px leaves 6px/side.
        const body = this.body as Phaser.Physics.Arcade.Body;
        body.setSize(20, 20);
        this.cursors = scene.input.keyboard!.createCursorKeys();
    }

    update (): void
    {
        const body = this.body as Phaser.Physics.Arcade.Body;
        body.setVelocity(0, 0);

        if (this.cursors.left.isDown)
        {
            body.setVelocityX(-SPEED);
        }
        else if (this.cursors.right.isDown)
        {
            body.setVelocityX(SPEED);
        }

        if (this.cursors.up.isDown)
        {
            body.setVelocityY(-SPEED);
        }
        else if (this.cursors.down.isDown)
        {
            body.setVelocityY(SPEED);
        }

        body.velocity.normalize().scale(SPEED);
    }
}
