import { expect, test } from '@playwright/test';

//  AC-005: Key Unlocks Door, Key Consumed
//  Independent driveTo helper — no cross-spec imports (QA harness runs each file standalone).

async function driveTo(page: import('@playwright/test').Page, tx: number, ty: number, budgetMs = 15000) {
  // tx/ty in TILES. Corridor-safe: keeps the cross axis within 4px of the
  // target line BEFORE and DURING dominant-axis travel, with press duration
  // proportional to the remaining delta — coarse 150ms presses overshoot the
  // ±8px usable band of a one-tile corridor and wedge the body on corners.
  const start = Date.now();
  let last = { x: NaN, y: NaN };
  let stuckStreak = 0;
  const pressMs = (delta: number) => Math.min(200, Math.max(30, Math.abs(delta) / 160 * 900));
  while (Date.now() - start < budgetMs) {
    const pos = await page.evaluate(() => (window as any).__game.state.position);
    const dx = tx * 32 + 16 - pos.x, dy = ty * 32 + 16 - pos.y;
    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
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

test.describe('AC-005: Key Unlocks Door, Key Consumed', () => {
    test('AC-005 player picks up key, then collides with door -> door opens and key removed from inventory', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');

        // wait for title and then start game
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');

        // wait until scene is Game (should spawn key and door)
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        // initial state: door should be locked after Game scene create() runs
        await page.waitForFunction(() => (window as any).__game?.state?.doors?.main === 'locked');

        const initialState = await page.evaluate(() => ({ ...(window as any).__game.state }));
        expect(initialState.inventory).toEqual({});
        expect(initialState.doors.main).toBe('locked');

        // drive to the key at tile (31, 8): east along corridor 1, then
        // north up the connector into Room B (map: game/maps/build_map.py)
        await driveTo(page, 27, 19);
        await driveTo(page, 31, 8);

        // overlap picks up key -> inventory.keys becomes 1
        await page.waitForFunction(() => (window as any).__game?.state?.inventory?.keys === 1);

        const afterPickup = await page.evaluate(() => ({ ...(window as any).__game.state }));
        expect(afterPickup.inventory.keys).toBe(1);

        // drive to the tile squarely WEST of the vault door (34, 31): south
        // down corridor 2, into the vault west half, up to the door row. The
        // door body blocks its own tile, so we target (32, 31) then bump
        // right into the door to trigger the unlock.
        await driveTo(page, 25, 12, 15000);
        await driveTo(page, 25, 27, 15000);
        await driveTo(page, 28, 27, 15000);
        await driveTo(page, 32, 31, 15000);
        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(1200);
        await page.keyboard.up('ArrowRight');

        // colliding with door while holding a key opens it and consumes key
        await page.waitForFunction(() => (window as any).__game?.state?.doors?.main === 'open', { timeout: 10000 });

        const finalState = await page.evaluate(() => ({ ...(window as any).__game.state }));
        expect(finalState.doors.main).toBe('open');
        expect(finalState.inventory.keys ?? 0).toBe(0);
    });
});
