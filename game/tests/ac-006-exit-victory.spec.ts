import { expect, test } from '@playwright/test';

//  Drive the player to (tx, ty); reads position each step and presses
//  toward the largest remaining axis. Corridor-safe: keeps the cross
//  axis within tolerance before/while travelling the dominant axis.
async function driveTo(page: any, tx: number, ty: number, budgetMs = 20000) {
    const start = Date.now();
    let last = { x: NaN, y: NaN };
    let stuckStreak = 0;
    const pressMs = (delta: number) => Math.min(200, Math.max(30, Math.abs(delta) / 160 * 900));
    while (Date.now() - start < budgetMs) {
        const pos = await page.evaluate(() => (window as any).__game.state.position);
        const dx = tx - pos.x, dy = ty - pos.y;
        if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
        // Hysteresis: a single immobile sample can be a timing artifact —
        // sidestep only after TWO consecutive immobile samples (a real wall).
        const immobile = Math.abs(pos.x - last.x) < 0.5 && Math.abs(pos.y - last.y) < 0.5;
        stuckStreak = immobile ? stuckStreak + 1 : 0;
        last = pos;
        let key: string;
        let ms: number;
        if (stuckStreak >= 2) {
            key = Math.abs(dx) > Math.abs(dy)
                ? (dy >= 0 ? 'ArrowDown' : 'ArrowUp')   // sidestep around the wall
                : (dx >= 0 ? 'ArrowRight' : 'ArrowLeft');
            ms = 120;
            stuckStreak = 0;
        } else if (Math.abs(dy) > 4) {
            key = dy > 0 ? 'ArrowDown' : 'ArrowUp';
            ms = pressMs(dy);
        } else {
            key = dx > 0 ? 'ArrowRight' : 'ArrowLeft';
            ms = pressMs(dx);
        }
        await page.keyboard.down(key!);
        await page.waitForTimeout(ms);
        await page.keyboard.up(key!);
    }
    throw new Error(`driveTo(${tx},${ty}) timed out; ended at ${JSON.stringify(last)}`);
}

test.describe('BL-006: Exit Triggers Victory Scene', () => {

    test('AC-006: crossing the exit tile after unlocking the door transitions to Victory', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');

        //  Boot → Title
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');

        //  Title → Game
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        //  Collect the key at tile (7, 8) — center (7*32+16, 8*32+16) = (240, 272).
        //  Player spawns at tile (5, 5) — center (176, 176).
        await driveTo(page, 240, 272);
        let inventory = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
        expect(inventory.keys).toBe(1);

        //  Move to the tile just before the door: door is at (12, 8) and blocks that tile;
        //  drive to the tile to the left of it, (11, 8) — center (368, 272).
        await driveTo(page, 11 * 32 + 16, 8 * 32 + 16);
        //  The player is at (368±, 272±). Hold Right through the door tile to trigger the open.
        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(600);
        await page.keyboard.up('ArrowRight');

        //  Door should now be open and key consumed.
        inventory = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
        expect(inventory.keys).toBeUndefined();
        const doors = await page.evaluate(() => ({ ...(window as any).__game.state.doors }));
        expect(doors['main']).toBe('open');

        //  The exit zone at tile (20, 8) fires its overlap on EDGE contact
        //  (player x≈630), and the scene transition freezes the player
        //  mid-corridor — so NEVER driveTo a point past the zone: hold
        //  Right and wait for the scene flip instead.
        await page.keyboard.down('ArrowRight');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Victory', undefined, { timeout: 10000 });
        await page.keyboard.up('ArrowRight');

        const state = await page.evaluate(() => ({ ...(window as any).__game.state }));
        expect(state.scene).toBe('Victory');
    });

});
