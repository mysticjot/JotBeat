import { expect, test } from '@playwright/test';

//  AC-007: Game Over State
//  Given the player is in the Game scene,
//  when the oxygen timer reaches 0,
//  then the game transitions to the Game Over scene.

test.describe('AC-007 Game Over State', () => {

  test('AC-007: oxygen depletion triggers Game Over transition', async ({ page }) => {
    // Use fastOxygen=1 to drain 10 oxygen/sec instead of 1/sec
    // This takes 10 seconds to hit 0 oxygen
    await page.goto('/?seed=jotbeat-default-seed&fastOxygen=1');

    // Wait for Title scene, then enter the Game scene
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

    // Verify we start with 100 oxygen
    const initialOxygen = await page.evaluate(() => (window as any).__game.state.oxygen);
    expect(initialOxygen).toBe(100);

    // Wait for oxygen to reach 0 (10 seconds at 10/sec drain rate)
    // and the scene to transition to GameOver
    await page.waitForFunction(() => {
      const state = (window as any).__game?.state;
      return state && state.oxygen === 0 && state.scene === 'GameOver';
    }, null, { timeout: 15000 });

    // Assert final state: oxygen is 0, scene is GameOver
    const state = await page.evaluate(() => (window as any).__game.state);
    expect(state.oxygen).toBe(0);
    expect(state.scene).toBe('GameOver');
  });

});
