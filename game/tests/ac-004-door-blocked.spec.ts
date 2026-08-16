import { expect, test } from '@playwright/test';

// AC-004: Locked door blocks the player when they have 0 keys.
// The locked door is at tile (15, 10) => pixel (496, 336)
// Player spawns at tile (5, 5), key at tile (9, 10)
// This test must NOT pick up the key, so we take a route that avoids passing through the key tile.

async function driveTo(page: any, tx: number, ty: number, budgetMs = 10000) {
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

test.describe('AC-004', () => {
  test('AC-004 locked door blocks player without key', async ({ page }) => {
    await page.goto('/?seed=jotbeat-default-seed');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

    // Wait for initial position to be set in Game scene
    await page.waitForFunction(() => {
      const s = (window as any).__game.state;
      return s && s.scene === 'Game' && s.position && s.position.x > 0;
    });

    // Verify player has 0 keys (no other test artifacts in this run)
    const inventory = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
    expect(inventory.keys || 0).toBe(0);

    // Verify door state is 'locked'
    const doors = await page.evaluate(() => ({ ...(window as any).__game.state.doors }));
    expect(doors.main).toBe('locked');

    // Navigate to just above the locked door at (15, 10) via the safe top corridor:
    // Route: up to row 2 (clear corridor), then right to column 15, then down to row 10.
    // This avoids both the key tile at (9,10) and the wall column at x=10 (rows 4–6).
    await driveTo(page, 5 * 32 + 16, 2 * 32 + 16);  // go straight up to the corridor
    await driveTo(page, 15 * 32 + 16, 2 * 32 + 16); // go right along the top
    await driveTo(page, 15 * 32 + 16, 9 * 32 + 16); // go down to row 9 (immediately above door)

    // Verify we are directly above the door
    const aboveDoor = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
    expect(Math.abs(aboveDoor.x - (15 * 32 + 16))).toBeLessThan(12);
    expect(Math.abs(aboveDoor.y - (9 * 32 + 16))).toBeLessThan(12);

    // Attempt to walk down INTO the locked door tile (15, 10)
    const before = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

    await page.keyboard.down('ArrowDown');
    await page.waitForTimeout(1200);
    await page.keyboard.up('ArrowDown');

    const after = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

    // Player should be blocked: y must not reach the door row (y < 10*32+16)
    // x stays centered on the column
    expect(after.x).toBeGreaterThanOrEqual(before.x - 5);
    expect(after.x).toBeLessThanOrEqual(before.x + 5);
    expect(after.y).toBeGreaterThanOrEqual(before.y - 5);
    expect(after.y).toBeLessThan(10 * 32 + 16 - 12);  // definitely NOT past the door center

    // Door must still report 'locked'
    const doorsAfter = await page.evaluate(() => ({ ...(window as any).__game.state.doors }));
    expect(doorsAfter.main).toBe('locked');

    // Verify no key was picked up along the route
    const inventoryAfter = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
    expect(inventoryAfter.keys || 0).toBe(0);
  });
});
