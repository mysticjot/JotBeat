import { expect, test } from '@playwright/test';

//  AC-009: HUD Key Count
//  The HUD key counter must match window.__game.state.inventory.keys live.

test.describe('AC-009 HUD Key Count', () => {
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

    test('AC-009 HUD shows 0 keys initially', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        // Give one frame for HUD to render
        await page.waitForTimeout(100);

        const hudTextValue = await page.evaluate(() => {
            const game: any = (window as any).__game?.game ?? (window as any).game;
            const scene = game?.scene?.getScene('Game');
            return scene?.hudText?.text;
        });
        const stateKeys = await page.evaluate(() => (window as any).__game.state.inventory.keys ?? 0);
        expect(hudTextValue).toContain('Keys: 0');
        expect(stateKeys).toBe(0);
    });

    test('AC-009 HUD key count updates after key pickup', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        // Player spawns at tile (7,19); key at tile (31,8) center (1008, 272)
        // (map: game/maps/build_map.py). Route: east along corridor 1,
        // north up the connector into Room B, then to the key.
        await driveTo(page, 27 * 32 + 16, 19 * 32 + 16);  // corridor 1 east end
        await driveTo(page, 27 * 32 + 16, 9 * 32 + 16);   // up the connector
        await driveTo(page, 1008, 272);                   // the key tile

        // Wait for key pickup (overlap triggers on contact)
        await page.waitForFunction(() => (window as any).__game.state.inventory.keys === 1, null, { timeout: 5000 });

        // Give a frame for HUD update
        await page.waitForTimeout(100);

        const hudTextValue = await page.evaluate(() => {
            const game: any = (window as any).__game?.game ?? (window as any).game;
            const scene = game?.scene?.getScene('Game');
            return scene?.hudText?.text;
        });
        const stateKeys = await page.evaluate(() => (window as any).__game.state.inventory.keys);
        expect(hudTextValue).toContain('Keys: 1');
        expect(stateKeys).toBe(1);
    });

    test('AC-009 HUD key count matches state after door opens (key consumed)', async ({ page }) => {
        await page.goto('/?seed=jotbeat-default-seed');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Title');
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => (window as any).__game?.state?.scene === 'Game');

        // Pick up the key NATURALLY — injecting state.inventory.keys and then
        // driving over the real key tile (31,8) double-counts and the
        // assertion never lands. Route: corridor 1, connector, Room B.
        await driveTo(page, 27 * 32 + 16, 19 * 32 + 16);
        await driveTo(page, 27 * 32 + 16, 9 * 32 + 16);
        await driveTo(page, 1008, 272);
        await page.waitForFunction(() => (window as any).__game.state.inventory.keys === 1, null, { timeout: 5000 });
        const hudWithKey = await page.evaluate(() => {
            const game: any = (window as any).__game?.game;
            return game?.scene?.getScene('Game')?.hudText?.text;
        });
        expect(hudWithKey).toContain('Keys: 1');

        // Vault door at tile (34,31); drive corridor 2 to the approach tile
        // (32,31) and bump right into the door.
        await driveTo(page, 25 * 32 + 16, 12 * 32 + 16);
        await driveTo(page, 25 * 32 + 16, 27 * 32 + 16);
        await driveTo(page, 28 * 32 + 16, 27 * 32 + 16);
        await driveTo(page, 32 * 32 + 16, 31 * 32 + 16);
        await page.keyboard.down('ArrowRight');
        // removeFromInventory DELETES the property — wait for undefined, not 0.
        await page.waitForFunction(() => (window as any).__game.state.inventory.keys === undefined, null, { timeout: 5000 });
        await page.keyboard.up('ArrowRight');

        // Give a moment for HUD to update
        await page.waitForTimeout(100);

        // Verify HUD shows 0 keys now
        const hudAfterDoor = await page.evaluate(() => {
            const game: any = (window as any).__game?.game;
            return game?.scene?.getScene('Game')?.hudText?.text;
        });
        const stateKeysAfter = await page.evaluate(() => (window as any).__game.state.inventory.keys ?? 0);
        expect(hudAfterDoor).toContain('Keys: 0');
        expect(stateKeysAfter).toBe(0);
    });
});
