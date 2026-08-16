import { Physics, Scene } from 'phaser';

export class Key extends Physics.Arcade.Sprite
{
    constructor (scene: Scene, x: number, y: number)
    {
        super(scene, x, y, 'key');
        scene.add.existing(this);
        scene.physics.add.existing(this);
        this.body.allowGravity = false;
        this.body.immovable = true;
        this.body.setSize(24, 24);
    }

    update (): void
    {
    }
}
