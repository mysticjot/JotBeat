import { defineConfig, devices } from '@playwright/test';

//  Phase 1 gate harness. Serves the production build (npm run build)
//  via vite preview and asserts against window.__game.state (ADR-0001).
//  Phase 4 (HANDOFF §2.1): viewport matrix. The game canvas is a fixed
//  640x480 flex-centered in #app — the matrix checks the SUITE stays green
//  at tablet/mobile sizes; visual deltas are the visual-regression gate's
//  job (tests/baseline/), not these specs'. The orchestrator's in-loop QA
//  pins --project=chromium (desktop) for speed; `jotbeat verify` runs all.
const matrix = {
    chromium: { width: 1280, height: 720 },          // desktop
    'chromium-tablet': { width: 768, height: 1024 },
    'chromium-mobile': { width: 375, height: 667 },
};

export default defineConfig({
    testDir: './tests',
    timeout: 30_000,
    retries: 0,
    workers: 1,
    reporter: 'list',
    use: {
        baseURL: 'http://localhost:4173',
        headless: true,
        screenshot: 'only-on-failure',
    },
    projects: Object.entries(matrix).map(([name, viewport]) => ({
        name,
        use: { ...devices['Desktop Chrome'], viewport },
    })),
    webServer: {
        command: 'npm run build-nolog && npx vite preview --config vite/config.prod.mjs --port 4173',
        url: 'http://localhost:4173',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
    },
});
