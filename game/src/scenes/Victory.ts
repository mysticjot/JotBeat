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

        this.cameras.main.setBackgroundColor('#1b1026');

        this.add.text(320, 180, 'You Win!', {
            fontFamily: 'Arial Black', fontSize: 64, color: '#d6ba6e',
            stroke: '#0d0812', strokeThickness: 8,
        }).setOrigin(0.5);

        const hint = this.add.text(320, 300, 'Press ENTER to play again', {
            fontFamily: 'Arial', fontSize: 24, color: '#8f6b3a',
        }).setOrigin(0.5);

        this.input.keyboard!.once('keydown-ENTER', () => {
            this.scene.start('Game');
        });
    }
}
