import { expect, test } from '@playwright/test';

test.describe('AC-002: Wall Collision', () => {

    test('player does not move when colliding with a wall', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');

        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');

        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        const before = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

        //  Map: game/maps/build_map.py — spawn (7,19) in Room A; the west
        //  wall column is x=1. Holding Left must stop at that wall.
        await page.keyboard.down('ArrowLeft');
        await page.waitForTimeout(3000);
        await page.keyboard.up('ArrowLeft');

        const after = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
        expect(after.x).toBeLessThan(before.x);      // moved
        expect(after.x).toBeGreaterThan(2 * 32);     // never entered the wall column
        expect(after.x).toBeLessThan(4 * 32);        // stopped at the wall, not through it
    });
});
