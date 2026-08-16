import { Scene } from 'phaser';
import { setScene } from '../debug';

export class GameOver extends Scene
{
    constructor ()
    {
        super('GameOver');
    }

    //  Phaser scene lifecycle — invoked by the Scene Manager, no direct call site.
    //  fallow-ignore-next-line unused-class-member
    create ()
    {
        setScene('GameOver');

        this.cameras.main.setBackgroundColor('#1b1026');

        this.add.text(320, 180, 'GAME OVER', {
            fontFamily: 'Arial Black', fontSize: 64, color: '#d63a2e',
            stroke: '#0d0812', strokeThickness: 8,
        }).setOrigin(0.5);

        const hint = this.add.text(320, 300, 'Press ENTER to return to Title', {
            fontFamily: 'Arial', fontSize: 24, color: '#8f6b3a',
        }).setOrigin(0.5);

        this.tweens.add({
            targets: hint, alpha: 0.3, duration: 700,
            yoyo: true, repeat: -1,
        });

        this.input.keyboard!.once('keydown-ENTER', () => {
            this.scene.start('Title');
        });
    }
}
