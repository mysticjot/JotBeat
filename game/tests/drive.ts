import type { Page } from '@playwright/test';

//  Shared QA bot movement (was copy-pasted between ac-006 and ac-008 —
//  extracted when baseline.spec.ts needed a third copy; fallow dupes gate).
//
//  Drive the player to (tx, ty); reads position each step and presses
//  toward the largest remaining axis. Corridor-safe: keeps the cross
//  axis within 4px of the target line BEFORE and DURING dominant-axis
//  travel, with press duration proportional to the remaining delta —
//  coarse fixed 150ms presses (24px at 160px/s) overshoot the ±8px
//  usable band of a one-tile corridor and wedge the body on corners.
//  Fails LOUDLY with the actual end position (that evidence is what a
//  retry fixes from).
export async function driveTo (page: Page, tx: number, ty: number, budgetMs: number)
{
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
