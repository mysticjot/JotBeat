import { Physics, Scene } from 'phaser';

export class Key extends Physics.Arcade.Sprite
{
    constructor (scene: Scene, x: number, y: number)
    {
        super(scene, x, y, 'greybox');
        scene.add.existing(this);
        scene.physics.add.existing(this);
        this.body.allowGravity = false;
        this.body.immovable = true;
        this.body.setSize(24, 24);
        this.setDisplaySize(24, 24);
        this.setTint(0xffd700); // Gold/yellow key color
    }

    update (): void
    {
    }
}
