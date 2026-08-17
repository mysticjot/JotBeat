import { expect, test } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { driveTo } from './drive';

//  Commercial Baseline — player-mode pre-flight (docs/COMMERCIAL_BASELINE.md).
//  QA plays the built game end-to-end as a player: boot → title → start →
//  play → pause/resume → victory AND (separately) game over, capturing a
//  screenshot at every state into artifacts/screenshots/baseline/ and
//  asserting no dead ends (every state offers a way forward).
//
//  Test titles carry "baseline <item>:" prefixes — studio/tools/cert.py parses
//  them from the list reporter into the cert's Commercial Baseline section.
//  Renaming a prefix breaks the cert mapping; keep doc + spec + cert in sync.
//
//  State assertions read window.__game.state (pinned by ADR-0001 — do not
//  remove the hook); scene-level checks use window.__game.game (same ADR).

const SEED = 'jotbeat-default-seed';
const SHOTS = path.resolve(process.cwd(), '..', 'artifacts', 'screenshots', 'baseline');

//  Audio contract (docs/COMMERCIAL_BASELINE.md §3): every player action and
//  state change has a sound. Keys must exist in the audio cache after boot.
const EXPECTED_SOUNDS = [
    'sfx-footstep',
    'sfx-key-pickup',
    'sfx-door-locked',
    'sfx-door-open',
    'sfx-low-oxygen',
    'sfx-victory',
    'sfx-gameover',
    'music-ambient',
];

//  Animation contract (§2): idle + walk x 4 directions on the player.
const EXPECTED_ANIMS = ['idle', 'walk-up', 'walk-down', 'walk-left', 'walk-right'];

async function shot (page: import('@playwright/test').Page, name: string)
{
    fs.mkdirSync(SHOTS, { recursive: true });
    await page.screenshot({ path: path.join(SHOTS, name) });
}

async function bootToGame (page: import('@playwright/test').Page, extraQuery = '')
{
    await page.goto(`/?seed=${SEED}${extraQuery}`);
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');
}

test.describe('Commercial Baseline', () => {

    test('baseline frame: victory path — title to victory with no dead ends', async ({ page }) => {
        test.setTimeout(120_000);

        //  Boot → Title.
        await page.goto(`/?seed=${SEED}`);
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await shot(page, '01-title.png');

        //  Title → (start) → Game.
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');
        await shot(page, '02-game-start.png');

        //  Play: walk a step in each direction like a new player would.
        for (const key of ['ArrowRight', 'ArrowUp', 'ArrowLeft', 'ArrowDown']) {
            await page.keyboard.down(key);
            await page.waitForTimeout(250);
            await page.keyboard.up(key);
        }
        await shot(page, '03-gameplay.png');

        //  Pause → resume (no dead end in pause).
        await page.keyboard.press('Space');
        await page.waitForFunction(() => (window as any).__game?.state?.paused === true);
        await shot(page, '04-paused.png');
        await page.keyboard.press('Space');
        await page.waitForFunction(() => (window as any).__game?.state?.paused === false);

        //  Play to victory: key -> door -> exit
        //  (route mirrors ac-006; map: game/maps/build_map.py).
        await driveTo(page, 27 * 32 + 16, 19 * 32 + 16, 20000);
        await driveTo(page, 27 * 32 + 16, 9 * 32 + 16, 20000);
        await driveTo(page, 31 * 32 + 16, 8 * 32 + 16, 20000);
        const pickedUp = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
        expect(pickedUp.keys).toBe(1);

        await driveTo(page, 25 * 32 + 16, 12 * 32 + 16, 20000);
        await driveTo(page, 25 * 32 + 16, 27 * 32 + 16, 20000);
        await driveTo(page, 28 * 32 + 16, 27 * 32 + 16, 20000);
        await driveTo(page, 32 * 32 + 16, 31 * 32 + 16, 20000);
        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(600);
        await page.keyboard.up('ArrowRight');
        const doors = await page.evaluate(() => ({ ...(window as any).__game.state.doors }));
        expect(doors['main']).toBe('open');

        //  Hold Right into the exit zone and wait for the scene flip.
        await page.keyboard.down('ArrowRight');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Victory', undefined, { timeout: 10000 });
        await page.keyboard.up('ArrowRight');
        await shot(page, '05-victory.png');

        //  Dead-end check: Victory must offer a way forward. Enter is the
        //  established "leave this screen" key (Title start, GameOver quit).
        await page.keyboard.press('Enter');
        await page.waitForTimeout(1500);
        const afterVictory = await page.evaluate(() => (window as any).__game.state.scene);
        expect(afterVictory, 'Victory screen is a dead end: no input leads out').not.toBe('Victory');
    });

    test('baseline frame: game-over path — no dead end back to title', async ({ page }) => {
        test.setTimeout(60_000);

        //  fastOxygen=1 drains 10/sec: game over in ~10s of play.
        await bootToGame(page, '&fastOxygen=1');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'GameOver', undefined, { timeout: 20000 });
        await shot(page, '06-gameover.png');

        //  Dead-end check: GameOver offers Enter -> Title.
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await shot(page, '07-title-after-gameover.png');
    });

    test('baseline character: player has idle + directional walk animations', async ({ page }) => {
        await bootToGame(page);

        const missing = await page.evaluate((keys) => {
            const game = (window as any).__game.game as any;
            const scene = game.scene.getScene('Game');
            return keys.filter((k) => !scene.anims.exists(k));
        }, EXPECTED_ANIMS);
        expect(
            missing,
            `player is a static tile — missing animations (contract: ${EXPECTED_ANIMS.join(', ')})`
        ).toEqual([]);
    });

    test('baseline character: camera is stable under movement (roundPixels or deadzone)', async ({ page }) => {
        await bootToGame(page);

        const cam = await page.evaluate(() => {
            const game = (window as any).__game.game as any;
            const c = game.scene.getScene('Game').cameras.main;
            return { roundPixels: c.roundPixels, hasDeadzone: c.deadzone != null };
        });
        expect(
            cam.roundPixels || cam.hasDeadzone,
            `camera has neither roundPixels nor a deadzone (got ${JSON.stringify(cam)})`
        ).toBe(true);
    });

    test('baseline audio: player actions and state changes have sounds', async ({ page }) => {
        await bootToGame(page);

        const missing = await page.evaluate((keys) => {
            const game = (window as any).__game.game as any;
            const loaded: string[] = game.scene.getScene('Game').cache.audio.getKeys();
            return keys.filter((k) => !loaded.includes(k));
        }, EXPECTED_SOUNDS);
        expect(
            missing,
            `no audio coverage — missing sounds (contract: ${EXPECTED_SOUNDS.join(', ')})`
        ).toEqual([]);
    });

    test('baseline onboarding: player knows where they are and why within 10s of Start', async ({ page }) => {
        test.setTimeout(45_000);

        await page.goto(`/?seed=${SEED}`);
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');

        //  Within 10s of Start, an orientation/objective line must be on
        //  screen in the Game scene. The HUD key counter alone does not count.
        const shown = await page.waitForFunction(() => {
            const game = (window as any).__game.game as any;
            const scene = game?.scene.getScene('Game');
            if (!scene) return false;
            return scene.children.list.some((o: any) =>
                o.type === 'Text' && o.visible && o.text.length > 12 && !o.text.startsWith('Keys:'));
        }, undefined, { timeout: 10000 }).then(() => true).catch(() => false);
        await shot(page, '08-onboarding.png');
        expect(shown, 'no orientation/objective text within 10s of Start').toBe(true);
    });

});
