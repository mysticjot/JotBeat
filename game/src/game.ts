import { Boot } from './scenes/Boot';
import { Game as MainGame } from './scenes/Game';
import { Title } from './scenes/Title';
import { AUTO, Game } from 'phaser';
import { getSeed, installDebugHook } from './debug';

//  Find out more information about the Game Config at:
//  https://docs.phaser.io/api-documentation/typedef/types-core#gameconfig
const config: Phaser.Types.Core.GameConfig = {
    type: AUTO,
    width: 640,
    height: 480,
    parent: 'game-container',
    backgroundColor: '#1b1026',
    pixelArt: true,
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { x: 0, y: 0 },  // top-down; no gravity
            debug: false
        }
    },
    seed: [ getSeed() ],  // deterministic RNG hook — pinned by ADR-0001
    scene: [
        Boot,
        Title,
        MainGame
    ]
};

const StartGame = (parent: string) => {

    installDebugHook();

    return new Game({ ...config, parent });

}

export default StartGame;
