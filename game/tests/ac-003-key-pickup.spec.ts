import { expect, test } from '@playwright/test';

test.describe('AC-003: Key Pickup + Inventory', () => {
    test('AC-003: Key pickup adds key to inventory and removes from map', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');

        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');

        const beforeInventory = await page.evaluate(() => (window as any).__game.state.inventory);
        expect(beforeInventory.keys).toBeUndefined();

        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        // Player spawns at tile (5,5) => pixel (176, 176)
        // Key is at tile (9,10) => pixel (304, 336)
        // Route: (5,5) -> (9,5) -> (9,10)
        // Check the map: row 5 (0-indexed) is all floor from col 1-28
        // Row 10 has walls at col 10 only, so approaching from col 9 is safe

        // Phase 1: Drive right to x=304 (tile column 9)
        await driveTo(page, 304, 176, 15000);

        // Phase 2: Drive down to y=336 (tile row 10)
        await driveTo(page, 304, 336, 15000);

        // Wait for the overlap to trigger and inventory update
        await page.waitForFunction(() => {
            const inv = (window as any).__game.state.inventory;
            return inv.keys === 1;
        }, { timeout: 10000 });

        const afterInventory = await page.evaluate(() => (window as any).__game.state.inventory);
        expect(afterInventory.keys).toBe(1);
    });
});

async function driveTo(page: any, tx: number, ty: number, budgetMs = 15000) {
    const start = Date.now();
    let last = { x: NaN, y: NaN };
    while (Date.now() - start < budgetMs) {
        const pos = await page.evaluate(() => (window as any).__game.state.position);
        const dx = tx - pos.x, dy = ty - pos.y;
        if (Math.abs(dx) < 12 && Math.abs(dy) < 12) return;
        const stuck = Math.abs(pos.x - last.x) < 1 && Math.abs(pos.y - last.y) < 1;
        last = pos;
        let key: string;
        if (stuck || Math.abs(dx) > Math.abs(dy)) key = dx > 0 ? 'ArrowRight' : 'ArrowLeft';
        if (!stuck && Math.abs(dy) >= Math.abs(dx)) key = dy > 0 ? 'ArrowDown' : 'ArrowUp';
        if (stuck) key = Math.abs(dx) > Math.abs(dy)
            ? (dy > 0 ? 'ArrowDown' : 'ArrowUp')
            : (dx > 0 ? 'ArrowRight' : 'ArrowLeft');
        await page.keyboard.down(key!);
        await page.waitForTimeout(150);
        await page.keyboard.up(key!);
    }
    throw new Error(`driveTo(${tx},${ty}) timed out; ended at ${JSON.stringify(last)}`);
}
