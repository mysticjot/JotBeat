import { defineConfig, devices } from '@playwright/test';

//  Phase 1 gate harness. Serves the production build (npm run build)
//  via vite preview and asserts against window.__game.state (ADR-0001).
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
    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
    webServer: {
        command: 'npm run build-nolog && npx vite preview --config vite/config.prod.mjs --port 4173',
        url: 'http://localhost:4173',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
    },
});
