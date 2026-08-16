import { expect, test } from '@playwright/test';

//  AC-008: Pause Screen
//  When the player presses the Spacebar, the game pauses and the oxygen
//  timer stops.
//  Verification: window.__game.state.paused is true; oxygen does not
//  decrease while paused.

const SEED = 'jotbeat-default-seed';

// Drive the player to (tx, ty); reads position each step and presses
// toward the largest remaining axis. Corridor-safe: keeps the cross
// axis within 4px of the target line BEFORE and DURING dominant-axis
// travel, with press duration proportional to the remaining delta —
// coarse fixed 150ms presses (24px at 160px/s) overshoot the ±8px
// usable band of a one-tile corridor and wedge the body on corners.
// Fails LOUDLY with the actual end position (that evidence is what a
// retry fixes from).
async function driveTo(page: import('@playwright/test').Page, tx: number, ty: number, budgetMs = 15000) {
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

async function startGame(page: import('@playwright/test').Page) {
  await page.goto(`/?seed=${SEED}&fastOxygen=1`);
  await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');
  // Reset any paused state from prior runs
  await page.evaluate(() => {
    if ((window as any).__game.state.paused) {
      (window as any).__game.state.paused = false;
    }
  });
}

test.describe('AC-008 Pause Screen', () => {

  test('AC-008: Spacebar pauses the game and stops oxygen drain', async ({ page }) => {
    await startGame(page);

    // Move to a safe open area (tile 3,7) so we're away from walls and the key
    await driveTo(page, 3 * 32 + 16, 7 * 32 + 16);

    // Wait for at least one oxygen tick with fastOxygen=1
    await page.waitForTimeout(1200);

    // Record oxygen before pausing
    const oxygenBeforePause = await page.evaluate(() => (window as any).__game.state.oxygen);
    expect(oxygenBeforePause).toBeLessThan(100);

    // Press Spacebar to pause
    await page.keyboard.press('Space');
    await page.waitForTimeout(100); // allow the event to propagate

    // Verify the game is paused
    const pausedState = await page.evaluate(() => ({
      paused: (window as any).__game.state.paused
    }));
    expect(pausedState.paused).toBe(true);

    // Record oxygen at the moment of pause
    const oxygenAtPause = await page.evaluate(() => (window as any).__game.state.oxygen);

    // Wait through several fast oxygen ticks (3.5s would normally drain 35)
    await page.waitForTimeout(3500);

    // Assert oxygen did NOT decrease while paused
    const oxygenAfterPauseWait = await page.evaluate(() => (window as any).__game.state.oxygen);
    expect(oxygenAfterPauseWait).toBe(oxygenAtPause);

    // Verify still paused
    const stillPaused = await page.evaluate(() => (window as any).__game.state.paused);
    expect(stillPaused).toBe(true);

    // Press Spacebar again to resume
    await page.keyboard.press('Space');
    await page.waitForTimeout(100);

    // Verify resumed
    const resumedState = await page.evaluate(() => ({
      paused: (window as any).__game.state.paused
    }));
    expect(resumedState.paused).toBe(false);

    // Wait through another fast oxygen tick and verify drain resumes
    await page.waitForTimeout(1500);
    const oxygenAfterResume = await page.evaluate(() => (window as any).__game.state.oxygen);
    expect(oxygenAfterResume).toBeLessThan(oxygenAtPause);
  });

  test('AC-008: player cannot move while paused', async ({ page }) => {
    // No fastOxygen here — we just want to test movement freeze
    await page.goto(`/?seed=${SEED}`);
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

    // Move to a safe open area (tile 3,7)
    await driveTo(page, 3 * 32 + 16, 7 * 32 + 16);

    // Let residual velocity flush before sampling: state.position is only
    // refreshed on unpaused update() frames, so one post-keyup physics step
    // can still move the player after driveTo returns (TRIAGE-0001 — the
    // drift happens BEFORE pause, not during it; the world is genuinely
    // frozen while paused). Sample until two reads 200ms apart match, then
    // startPos is a stable reference and exact equality below is meaningful.
    let startPos = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
    for (let i = 0; i < 10; i++) {
      await page.waitForTimeout(200);
      const cur = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
      if (cur.x === startPos.x && cur.y === startPos.y) break;
      startPos = cur;
    }

    // Press Spacebar to pause
    await page.keyboard.press('Space');
    await page.waitForTimeout(100);
    const paused = await page.evaluate(() => (window as any).__game.state.paused);
    expect(paused).toBe(true);

    // Try to move right for 1 second
    await page.keyboard.down('ArrowRight');
    await page.waitForTimeout(1000);
    await page.keyboard.up('ArrowRight');

    // Position should be unchanged while paused
    const pausedPos = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
    expect(pausedPos.x).toBe(startPos.x);
    expect(pausedPos.y).toBe(startPos.y);

    // Resume
    await page.keyboard.press('Space');
    await page.waitForTimeout(100);
    const resumed = await page.evaluate(() => (window as any).__game.state.paused);
    expect(resumed).toBe(false);

    // Now movement should work
    await page.keyboard.down('ArrowRight');
    await page.waitForTimeout(300);
    await page.keyboard.up('ArrowRight');

    const movedPos = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
    expect(movedPos.x).toBeGreaterThan(pausedPos.x);
  });

});
