import { expect, test } from '@playwright/test';

// AC-004: Locked door blocks the player when they have 0 keys.
// Map: game/maps/build_map.py — the locked vault door is at tile (34, 31)
// => pixel (1104, 1008); key at tile (31, 8); player spawns at tile (7, 19).
// This test must NOT pick up the key, so the route stays west of it:
// corridor 1 -> connector -> Room B southwest -> corridor 2 -> vault west.

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

    // Route to the vault door's west side without crossing the key tile:
    // east along corridor 1, north up the connector, across Room B's south
    // edge to corridor 2, south to the vault, then east to the door.
    await driveTo(page, 27 * 32 + 16, 19 * 32 + 16);  // east end of corridor 1
    await driveTo(page, 25 * 32 + 16, 12 * 32 + 16);  // Room B south-west (corridor 2 mouth)
    await driveTo(page, 25 * 32 + 16, 27 * 32 + 16);  // south down corridor 2
    await driveTo(page, 28 * 32 + 16, 27 * 32 + 16);  // into the vault west half
    await driveTo(page, 32 * 32 + 16, 31 * 32 + 16);  // squarely west of the door

    // Verify we are directly west of the door, aligned with its row
    const besideDoor = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
    expect(Math.abs(besideDoor.x - (32 * 32 + 16))).toBeLessThan(12);
    expect(Math.abs(besideDoor.y - (31 * 32 + 16))).toBeLessThan(12);

    // Attempt to walk right INTO the locked door tile (34, 31)
    const before = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

    await page.keyboard.down('ArrowRight');
    await page.waitForTimeout(1200);
    await page.keyboard.up('ArrowRight');

    const after = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

    // Player should be blocked: x must not reach the door column center
    // (34*32+16 = 1104); contact happens ~26px west of it.
    expect(after.y).toBeGreaterThanOrEqual(before.y - 5);
    expect(after.y).toBeLessThanOrEqual(before.y + 5);
    expect(after.x).toBeLessThan(34 * 32 + 16 - 12);  // definitely NOT past the door center

    // Door must still report 'locked'
    const doorsAfter = await page.evaluate(() => ({ ...(window as any).__game.state.doors }));
    expect(doorsAfter.main).toBe('locked');

    // Verify no key was picked up along the route
    const inventoryAfter = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
    expect(inventoryAfter.keys || 0).toBe(0);
  });
});
