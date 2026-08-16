import { expect, test } from '@playwright/test';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import * as fs from 'fs';
import * as path from 'path';
import { visualGate } from './visual.config';

//  Visual regression (HANDOFF-PHASE4 §2.2): pixelmatch against stored
//  baselines in tests/baseline/ (git-LFS). Deterministic seed + fixed
//  desktop viewport. Baselines regenerate with UPDATE_BASELINE=1.
//  Failures archive actual + diff to artifacts/visual-diffs/.

const BASELINE_DIR = path.join(__dirname, 'baseline');
const DIFF_DIR = path.join(__dirname, '..', '..', 'artifacts', 'visual-diffs');

async function driveTo(page: any, tx: number, ty: number, budgetMs = 15000) {
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
        ? (dy >= 0 ? 'ArrowDown' : 'ArrowUp')
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

function compareAgainstBaseline(name: string, actualBuf: Buffer): void {
  const baselinePath = path.join(BASELINE_DIR, `${name}.png`);
  if (process.env.UPDATE_BASELINE === '1' || !fs.existsSync(baselinePath)) {
    fs.mkdirSync(BASELINE_DIR, { recursive: true });
    fs.writeFileSync(baselinePath, actualBuf);
    console.log(`baseline written: ${name}.png`);
    return;
  }
  const baseline = PNG.sync.read(fs.readFileSync(baselinePath));
  const actual = PNG.sync.read(actualBuf);
  expect(
    actual.width === baseline.width && actual.height === baseline.height,
    `${name}: viewport size changed (${baseline.width}x${baseline.height} -> ${actual.width}x${actual.height}) — regenerate baselines deliberately`,
  ).toBe(true);
  const diff = new PNG({ width: actual.width, height: actual.height });
  const diffPixels = pixelmatch(baseline.data, actual.data, diff.data, actual.width, actual.height, {
    threshold: visualGate.pixelThreshold,
    includeAA: false,
  });
  const ratio = diffPixels / (actual.width * actual.height);
  if (ratio > visualGate.maxDiffPixelRatio) {
    fs.mkdirSync(DIFF_DIR, { recursive: true });
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    fs.writeFileSync(path.join(DIFF_DIR, `${name}-actual-${stamp}.png`), actualBuf);
    fs.writeFileSync(path.join(DIFF_DIR, `${name}-diff-${stamp}.png`), PNG.sync.write(diff));
  }
  expect(
    ratio,
    `${name}: ${(ratio * 100).toFixed(2)}% pixels differ from baseline (max ${visualGate.maxDiffPixelRatio * 100}%) — diff archived to artifacts/visual-diffs/`,
  ).toBeLessThanOrEqual(visualGate.maxDiffPixelRatio);
}

async function shot(page: any, name: string): Promise<void> {
  const buf = await page.screenshot();
  compareAgainstBaseline(name, buf);
}

test.describe('visual regression baseline', () => {
  test('title / gameplay / victory match baselines', async ({ page }) => {
    //  Skip on non-desktop projects: baselines are captured at the desktop
    //  viewport; tablet/mobile coverage is the viewport matrix's job (§2.1).
    test.skip(test.info().project.name !== 'chromium', 'desktop-viewport baselines only');

    await page.goto('/?seed=jotbeat-default-seed');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
    await page.waitForTimeout(300);  // fonts + first-frame settle
    await shot(page, 'title');

    await page.keyboard.press('Enter');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');
    await page.waitForTimeout(600);  // camera follow lerp settles on spawn
    await shot(page, 'gameplay');

    //  Full start-to-victory run for the victory baseline.
    await driveTo(page, 240, 272);   // key
    await page.waitForFunction(() => (window as any).__game?.state?.inventory?.keys === 1);
    await driveTo(page, 368, 272);   // door-adjacent
    await page.keyboard.down('ArrowRight');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Victory', undefined, { timeout: 10000 });
    await page.keyboard.up('ArrowRight');
    await page.waitForTimeout(300);
    await shot(page, 'victory');
  });
});
