// SALTBOUND desktop shell (docs/DECISIONS.md D-0002).
// Thin wrapper: loads the web build, nothing else. Game code never imports
// Electron APIs — platform features go through game/src/platform/ only.
const { app, BrowserWindow } = require('electron');
const fs = require('fs');
const path = require('path');

// Resolve the web build for the three layouts this shell can sit in:
// packaged (web/ next to main.js), dist/desktop/ (sibling dist/web/),
// and the repo-root desktop/ working folder (sibling dist/web/).
const CANDIDATES = [
  path.join(__dirname, 'web', 'index.html'),
  path.join(__dirname, '..', 'web', 'index.html'),
  path.join(__dirname, '..', 'dist', 'web', 'index.html'),
];

function webEntry () {
  const found = CANDIDATES.find((p) => fs.existsSync(p));
  if (!found) {
    throw new Error('web build not found — run `python studio/cli.py export` first');
  }
  return found;
}

function createWindow () {
  const win = new BrowserWindow({
    width: 1280,
    height: 720,
    autoHideMenuBar: true,
    backgroundColor: '#0d0d0d',
  });
  win.loadFile(webEntry());
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
