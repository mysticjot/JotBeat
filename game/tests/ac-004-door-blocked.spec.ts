import { expect, test } from '@playwright/test';

// AC-004: Locked door blocks the player when they have 0 keys.
// The locked door is at tile (12, 8) => pixel (400, 272); key at (7, 8).
// Player spawns at tile (5, 5).
// This test must NOT pick up the key, so we route around the key tile.

async function driveTo(page: any, tx: number, ty: number, budgetMs = 15000) {
  // tx/ty in PIXELS. Corridor-safe: keeps the cross axis within 4px of the
  // target line BEFORE and DURING dominant-axis travel, with press duration
  // proportional to the remaining delta — coarse 150ms presses overshoot the
  // ±8px usable band of a one-tile corridor and wedge the body on corners.
  const start = Date.now();
  let last = { x: NaN, y: NaN };
  let stuckStreak = 0;
  const pressMs = (delta: number) => Math.min(200, Math.max(30, Math.abs(delta) / 160 * 900));
  while (Date.now() - start < budgetMs) {
    const pos = await page.evaluate(() => (window as any).__game.state.position);
    const dx = tx - pos.x, dy = ty - pos.y;
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

    // Navigate to just above the locked door at (12, 8) via the top corridor:
    // up col 5 to row 2, right to col 12, down to row 7 — avoids the key at (7, 8).
    await driveTo(page, 5 * 32 + 16, 2 * 32 + 16);  // up to the corridor
    await driveTo(page, 12 * 32 + 16, 2 * 32 + 16); // right along the top
    await driveTo(page, 12 * 32 + 16, 7 * 32 + 16); // down to row 7 (above door)

    // Verify we are directly above the door
    const aboveDoor = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
    expect(Math.abs(aboveDoor.x - (12 * 32 + 16))).toBeLessThan(12);
    expect(Math.abs(aboveDoor.y - (7 * 32 + 16))).toBeLessThan(12);

    // Attempt to walk down INTO the locked door tile (12, 8)
    const before = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

    await page.keyboard.down('ArrowDown');
    await page.waitForTimeout(1200);
    await page.keyboard.up('ArrowDown');

    const after = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

    // Player should be blocked: y must not reach the door row (y < 8*32+16)
    // x stays centered on the column
    expect(after.x).toBeGreaterThanOrEqual(before.x - 5);
    expect(after.x).toBeLessThanOrEqual(before.x + 5);
    expect(after.y).toBeGreaterThanOrEqual(before.y - 5);
    expect(after.y).toBeLessThan(8 * 32 + 16 - 12);  // definitely NOT past the door center

    // Door must still report 'locked'
    const doorsAfter = await page.evaluate(() => ({ ...(window as any).__game.state.doors }));
    expect(doorsAfter.main).toBe('locked');

    // Verify no key was picked up along the route
    const inventoryAfter = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
    expect(inventoryAfter.keys || 0).toBe(0);
  });
});
