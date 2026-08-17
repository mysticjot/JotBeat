// artifacts/console-shots.cjs — console gate evidence: one screenshot per
// console tab into artifacts/screenshots/console/. Uses the Playwright
// install under game/ (no new dependency). Run: node artifacts/console-shots.cjs [baseURL]
const { createRequire } = require('module');
const path = require('path');
const req = createRequire(path.join(__dirname, '..', 'game', 'package.json'));
const { chromium } = req('playwright');

(async () => {
  const base = process.argv[2] || 'http://127.0.0.1:8790';
  const outDir = path.join(__dirname, 'screenshots', 'console');
  // The repo's Playwright browsers were installed by the game/ test harness;
  // if the default lookup misses (revision skew), fall back to the installed
  // headless shell via JOTBEAT_CHROMIUM_EXE or the standard cache location.
  const os = require('os');
  const fallbackExe = path.join(
    os.homedir(), 'AppData', 'Local', 'ms-playwright',
    'chromium_headless_shell-1228', 'chrome-headless-shell-win64',
    'chrome-headless-shell.exe');
  const exe = process.env.JOTBEAT_CHROMIUM_EXE ||
    (require('fs').existsSync(fallbackExe) ? fallbackExe : undefined);
  const browser = await chromium.launch(exe ? { executablePath: exe } : {});
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on('dialog', d => d.accept());
  await page.goto(base + '/', { waitUntil: 'networkidle' });
  for (const t of ['pipeline', 'gates', 'costs', 'artifacts', 'backlog', 'settings']) {
    await page.click(`nav.tabs button[data-tab="${t}"]`);
    if (t === 'settings') {
      await page.waitForSelector('iframe.settings');
      const frame = page.frame({ url: /\/settings/ });
      if (frame) {
        await frame.waitForSelector('#keys tbody tr', { timeout: 10000 }).catch(() => {});
      }
      await page.waitForTimeout(700);
      await page.screenshot({ path: path.join(outDir, `${t}.png`) });
    } else {
      await page.waitForSelector(`#tab-${t} .card`, { timeout: 10000 });
      // give inline images a beat to load
      await page.waitForTimeout(t === 'artifacts' || t === 'gates' ? 1800 : 800);
      await page.screenshot({ path: path.join(outDir, `${t}.png`), fullPage: true });
    }
    process.stdout.write('shot: ' + t + '\n');
  }
  await browser.close();
})().catch(e => { process.stderr.write(String(e && e.stack || e) + '\n'); process.exit(1); });
