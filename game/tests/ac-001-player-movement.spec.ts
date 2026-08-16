import { expect, test } from '@playwright/test';

test.describe('AC-001: Player Movement', () => {

    test('player moves with arrow keys', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        const before = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(500);
        await page.keyboard.up('ArrowRight');

        const after = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
        expect(after.x).toBeGreaterThan(before.x);
    });
});
