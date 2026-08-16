import { expect, test } from '@playwright/test';

//  AC-010: Title Screen With Start Flow
//  Verifies the game boots to Title, pressing Enter transitions to Game,
//  and all game state resets (position/inventory).

test.describe('AC-010 Title Screen With Start Flow', () => {

    test('AC-010 game boots to Title scene', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');

        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');

        const state = await page.evaluate(() => (window as any).__game.state);
        expect(state.scene).toBe('Title');
        expect(state.seed).toBe('jotbeat-default-seed');
    });

    test('AC-010 pressing Enter starts Game scene with reset state', async ({ page }) => {
        // Boot to Title
        await page.goto('/?seed=jotbeat-default-seed');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');

        // Pre-start state check
        const preState = await page.evaluate(() => (window as any).__game.state);
        expect(preState.scene).toBe('Title');

        // Press Enter to start the game
        await page.keyboard.press('Enter');

        // Wait for transition to Game scene
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        // Post-transition state assertion
        const postState = await page.evaluate(() => (window as any).__game.state);
        expect(postState.scene).toBe('Game');
        
        // Verify reset state: player at start position (5,5) tile center
        expect(postState.position.x).toBeCloseTo(5 * 32 + 16, 1);
        expect(postState.position.y).toBeCloseTo(5 * 32 + 16, 1);

        // Inventory should be empty/reset
        expect(postState.inventory).toEqual({});

        // Oxygen should be reset to 100
        expect(postState.oxygen).toBe(100);

        // Should not be paused
        expect(postState.paused).toBe(false);
    });

    test('AC-010 Game scene is playable after Enter', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');

        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        // Verify player can move after starting
        const before = await page.evaluate(() => ({ ...(window as any).__game.state.position }));

        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(200);
        await page.keyboard.up('ArrowRight');

        const after = await page.evaluate(() => ({ ...(window as any).__game.state.position }));
        expect(after.x).toBeGreaterThan(before.x);
        expect(after.y).toBeCloseTo(before.y, 1);  // moving right should not change Y
    });

});
