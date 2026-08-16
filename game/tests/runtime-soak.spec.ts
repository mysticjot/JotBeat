import { expect, test } from '@playwright/test';

//  RUNTIME SOAK — phase-gate runtime check (user directive 2026-08-16):
//  every phase gate proves the BUILT game boots and runs smoothly, not just
//  that its assertions pass. Doubles as the export contract's "web artifact
//  boots headless for 60s" bot check (docs/DECISIONS.md).
//  Desktop project only — a boot/health signal, not a viewport matrix test.

test('runtime: built game boots and runs cleanly for 60s', async ({ page }) => {
  test.skip(test.info().project.name !== 'chromium', 'desktop-only runtime check');
  test.setTimeout(90000);

  const pageErrors: string[] = [];
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  page.on('console', (m) => {
    if (m.type() === 'error') pageErrors.push(m.text());
  });

  await page.goto('/?seed=jotbeat-default-seed');
  await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

  const t0 = await page.evaluate(() => ({ ...(window as any).__game.state }));
  expect(t0.oxygen).toBe(100);

  // Soak: the game just runs. No input — a smooth idle is the signal.
  await page.waitForTimeout(60000);

  const t1 = await page.evaluate(() => ({ ...(window as any).__game.state }));
  expect(t1.scene).toBe('Game');           // still alive, not GameOver/crash
  expect(t1.oxygen).toBeLessThan(100);     // timer ticking = main loop live
  expect(t1.oxygen).toBeGreaterThan(30);   // drain rate sane (~1/s, no runaway)
  expect(pageErrors).toEqual([]);          // zero page/console errors in 60s
});
