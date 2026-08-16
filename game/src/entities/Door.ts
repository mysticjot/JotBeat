import { Physics, Scene } from 'phaser';
import { setDoorState } from '../debug';

export class Door extends Physics.Arcade.Sprite
{
    private doorId: string;
    private opened = false;

    constructor (scene: Scene, x: number, y: number, doorId = 'main')
    {
        super(scene, x, y, 'greybox');
        this.doorId = doorId;
        scene.add.existing(this);
        scene.physics.add.existing(this);
        
        this.body.allowGravity = false;
        this.body.immovable = true;
        this.body.pushable = false;
        this.body.setSize(32, 32);
        this.body.setOffset(0, 0);
        
        this.setDisplaySize(32, 32);
        this.setTint(0x8b0000); // Dark red door color
        this.setImmovable(true);

        // Ensure the door starts locked in the debug state
        setDoorState(this.doorId, 'locked');
    }

    // Called from Game.openDoor via a GameObject->Door cast inside a physics
    // collider callback — static analysis can't see the reference.
    // fallow-ignore-next-line unused-class-member
    open (): void
    {
        if (this.opened) return;
        this.opened = true;
        this.setTint(0x3a3a3a);  // dim the door to show it's open
        this.disableBody(true, false);  // deactivate collision + physics on the next step
        setDoorState(this.doorId, 'open');
    }

    update (): void
    {
    }
}
