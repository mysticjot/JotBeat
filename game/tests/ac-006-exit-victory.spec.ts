import { expect, test } from '@playwright/test';
import { driveTo } from './drive';

test.describe('BL-006: Exit Triggers Victory Scene', () => {

    test('AC-006: crossing the exit tile after unlocking the door transitions to Victory', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');

        //  Boot → Title
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');

        //  Title → Game
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        //  Collect the key at tile (31, 8) — center (1008, 272). Route:
        //  east along corridor 1, north up the connector into Room B
        //  (map: game/maps/build_map.py). Player spawns at tile (7, 19).
        await driveTo(page, 27 * 32 + 16, 19 * 32 + 16, 20000);
        await driveTo(page, 27 * 32 + 16, 9 * 32 + 16, 20000);
        await driveTo(page, 31 * 32 + 16, 8 * 32 + 16, 20000);
        let inventory = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
        expect(inventory.keys).toBe(1);

        //  Move to the tile squarely west of the vault door: door is at
        //  (34, 31) and blocks that tile; drive to (32, 31) via corridor 2
        //  and the vault west half — center (1040, 1008).
        await driveTo(page, 25 * 32 + 16, 12 * 32 + 16, 20000);
        await driveTo(page, 25 * 32 + 16, 27 * 32 + 16, 20000);
        await driveTo(page, 28 * 32 + 16, 27 * 32 + 16, 20000);
        await driveTo(page, 32 * 32 + 16, 31 * 32 + 16, 20000);
        //  The player is at (1040±, 1008±). Hold Right through the door tile to trigger the open.
        await page.keyboard.down('ArrowRight');
        await page.waitForTimeout(600);
        await page.keyboard.up('ArrowRight');

        //  Door should now be open and key consumed.
        inventory = await page.evaluate(() => ({ ...(window as any).__game.state.inventory }));
        expect(inventory.keys).toBeUndefined();
        const doors = await page.evaluate(() => ({ ...(window as any).__game.state.doors }));
        expect(doors['main']).toBe('open');

        //  The exit zone at tile (37, 31) fires its overlap on EDGE contact
        //  and the scene transition freezes the player mid-stride — so NEVER
        //  driveTo a point past the zone: hold Right and wait for the scene
        //  flip instead.
        await page.keyboard.down('ArrowRight');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Victory', undefined, { timeout: 10000 });
        await page.keyboard.up('ArrowRight');

        const state = await page.evaluate(() => ({ ...(window as any).__game.state }));
        expect(state.scene).toBe('Victory');
    });

});
