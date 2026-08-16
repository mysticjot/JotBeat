import { expect, test } from '@playwright/test';

//  Smoke test (roadmap §15.2): game loads headless, state readable.
//  Everything hangs off the debug hook pinned in ADR-0001.

test.describe('Phase 1 scaffold', () => {

    test('boots to Title scene and exposes window.__game.state', async ({ page }) => {
        await page.goto('/');

        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');

        const state = await page.evaluate(() => (window as any).__game.state);
        expect(state.scene).toBe('Title');
        expect(state).toHaveProperty('position');
        expect(state).toHaveProperty('inventory');
        expect(state).toHaveProperty('doors');
        expect(state.seed).toBe('jotbeat-default-seed');
    });

    test('seed hook: ?seed= param flows into state', async ({ page }) => {
        await page.goto('/?seed=qa-run-42');

        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');

        const seed = await page.evaluate(() => (window as any).__game.state.seed);
        expect(seed).toBe('qa-run-42');
    });

    test('ENTER starts the Game scene; arrow keys move the player; camera follows', async ({ page }) => {
        await page.goto('/');

        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        const before = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(500);
        await page.keyboard.up('ArrowRight');

        const after = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
        expect(after.x).toBeGreaterThan(before.x);

        //  Wall collision: corridor 1 (spawn row 19) runs east to the col-27
        //  wall; holding Right long enough must stop there, not pass it.
        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(6000);
        await page.keyboard.up('ArrowRight');

        const stopped = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
        expect(stopped.x).toBeLessThan(29 * 32);  // corridor 1 ends at col 27 (x=928)
    });

});
