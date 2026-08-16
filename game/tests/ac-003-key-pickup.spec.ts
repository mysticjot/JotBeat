import { expect, test } from '@playwright/test';

// AC-003: Player picks up a key on the ground and inventory updates
// The key is at tile (9, 10) => pixel (304, 336)
// Player spawns at tile (5, 5)

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

test.describe('AC-003', () => {
  test('AC-003 player picks up key and inventory updates', async ({ page }) => {
    await page.goto('/?seed=jotbeat-default-seed');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

    // Verify player starts with 0 keys
    const inventoryBefore = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
    expect(inventoryBefore.keys || 0).toBe(0);

    // Navigate to key at tile (9, 10) => pixel (304, 336)
    await driveTo(page, 9 * 32 + 16, 10 * 32 + 16);

    // Press space (or any action) to pick up? The implementation uses overlap detection; we just need to be on the tile and the key disappears.
    // The test does not specify key press; just drive and then check inventory.
    const afterPickup = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
    expect(afterPickup.keys).toBe(1);
  });
});
