import { Physics, Scene } from 'phaser';

export class Door extends Physics.Arcade.Sprite
{
    constructor (scene: Scene, x: number, y: number)
    {
        super(scene, x, y, 'greybox');
        scene.add.existing(this);
        scene.physics.add.existing(this);
        
        const body = this.body as Phaser.Physics.Arcade.Body;
        body.allowGravity = false;
        body.immovable = true;
        body.pushable = false;
        body.setSize(32, 32);
        body.setOffset(0, 0);
        
        this.setDisplaySize(32, 32);
        this.setTint(0x8b0000); // Dark red door color
        this.setImmovable(true);
    }

    update (): void
    {
    }
}
