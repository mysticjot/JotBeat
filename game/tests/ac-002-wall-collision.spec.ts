import { expect, test } from '@playwright/test';

test.describe('AC-002: Wall Collision', () => {

    test('player does not move when colliding with a wall', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');

        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');

        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        const before = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(3000);
        await page.keyboard.up('ArrowRight');

        const after = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
        expect(after.x).toBeLessThan(10 * 32);
    });
});
