import { Scene } from 'phaser';
import { setScene } from '../debug';

export class Victory extends Scene
{
    constructor ()
    {
        super('Victory');
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    create ()
    {
        setScene('Victory');

        this.cameras.main.setBackgroundColor('#0d0d0d');

        this.add.text(320, 180, 'VICTORY', {
            fontFamily: 'Arial Black', fontSize: 64, color: '#4ed64e',
            stroke: '#0d0812', strokeThickness: 8,
        }).setOrigin(0.5);

        const hint = this.add.text(320, 300, 'You escaped!', {
            fontFamily: 'Arial', fontSize: 24, color: '#8f6b3a',
        }).setOrigin(0.5);
    }
}
