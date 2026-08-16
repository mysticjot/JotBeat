"""tools/export.py — the export contract (docs/DECISIONS.md D-0001/D-0002).

Every JotBeat game is exportable to any platform from day one:

    dist/web/      Vite static build + itch.io-ready zip (index.html at ZIP ROOT)
    dist/desktop/  Electron thin shell around the web build
    dist/mobile/   Capacitor thin shell around the web build

The web build is the single artifact and must always work standalone;
wrappers are thin shells around it. Wrapper failures degrade to printed
FLAGs, never hard failures. Wrapper npm installs are skipped when
JOTBEAT_EXPORT_WRAPPERS=0 (CI keeps the shells scaffold-only).
$0, no model calls.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GAME_DIR = ROOT / "game"
DIST = ROOT / "dist"
WEB_DIR = DIST / "web"
ZIP_NAME = "jotbeat-web.zip"

WRAPPER_INSTALL_TIMEOUT = 300  # seconds; over this we scaffold + FLAG

DESKTOP_PACKAGE_JSON = """{
  "name": "jotbeat-desktop",
  "private": true,
  "version": "0.1.0",
  "description": "SALTBOUND desktop shell — Electron wrapper around dist/web (D-0002)",
  "main": "main.js",
  "scripts": {
    "start": "electron ."
  },
  "devDependencies": {
    "electron": "^33.0.0"
  }
}
"""

DESKTOP_MAIN_JS = """// SALTBOUND desktop shell (docs/DECISIONS.md D-0002).
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
"""

MOBILE_PACKAGE_JSON = """{
  "name": "jotbeat-mobile",
  "private": true,
  "version": "0.1.0",
  "description": "SALTBOUND mobile shell — Capacitor wrapper around dist/web (D-0002)",
  "scripts": {
    "sync": "cap sync"
  },
  "dependencies": {
    "@capacitor/core": "^6.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^6.0.0",
    "@capacitor/android": "^6.0.0"
  }
}
"""

MOBILE_CAPACITOR_CONFIG = """{
  "appId": "com.jotbeat.saltbound",
  "appName": "SALTBOUND",
  "webDir": "../dist/web",
  "backgroundColor": "#0d0d0d"
}
"""


def _run(cmd: str, cwd: Path, timeout: int) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        check=False,  # wrapper failures degrade to FLAGs, never raise (D-0001)
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _log_tail(text: str, lines: int = 20) -> str:
    """Log tails, not logs (docs/BUDGET.md rationing rule 3)."""
    return "\n".join(text.splitlines()[-lines:])


def _npm_step(cmd: str, cwd: Path) -> str | None:
    """Run an npm step in a wrapper dir. Returns None on success, else the
    FLAG reason — wrapper failures degrade, they never raise (D-0001)."""
    try:
        rc, out = _run(cmd, cwd, WRAPPER_INSTALL_TIMEOUT)
    except subprocess.TimeoutExpired as e:
        return f"`{cmd}` timed out after {WRAPPER_INSTALL_TIMEOUT}s ({e})"
    if rc != 0:
        return f"`{cmd}` failed (rc={rc})\n{_log_tail(out)}"
    return None


def _build_web() -> bool:
    """Production build via the shared BVT path, copied to dist/web/."""
    from tools.shell import run_bvt

    build = run_bvt()
    if not build["passed"]:
        print("web build FAILED")
        print(build["log_tail"])
        return False
    if WEB_DIR.exists():
        shutil.rmtree(WEB_DIR)
    shutil.copytree(GAME_DIR / "dist", WEB_DIR)
    print(f"web build -> {WEB_DIR.relative_to(ROOT)}")
    return True


def _zip_web() -> Path | None:
    """itch.io-ready zip: index.html at the ZIP ROOT, not nested."""
    zip_path = WEB_DIR / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(WEB_DIR.rglob("*")):
            if f.is_file() and f.name != ZIP_NAME:
                zf.write(f, f.relative_to(WEB_DIR))
    with zipfile.ZipFile(zip_path) as zf:
        if "index.html" not in zf.namelist():
            print("zip FAILED: index.html missing at zip root")
            return None
    size = zip_path.stat().st_size
    print(
        f"web zip -> {zip_path.relative_to(ROOT)}  ({size} bytes / {size / 1024:.1f} KB)"
    )
    return zip_path


def _scaffold_desktop() -> Path:
    desktop = ROOT / "desktop"
    desktop.mkdir(exist_ok=True)
    (desktop / "package.json").write_text(DESKTOP_PACKAGE_JSON, encoding="utf-8")
    (desktop / "main.js").write_text(DESKTOP_MAIN_JS, encoding="utf-8")
    return desktop


def _desktop(install: bool) -> None:
    """Electron shell (D-0002). Tauri needs a Rust toolchain; we only ever
    consider it when cargo is present, and D-0002 locks Electron regardless."""
    cargo = shutil.which("cargo")
    if cargo:
        print(
            f"desktop tool: Electron (locked by D-0002; cargo found at {cargo}, Tauri viable but not chosen)"
        )
    else:
        print("desktop tool: Electron (no Rust toolchain — Tauri not an option)")

    desktop = _scaffold_desktop()
    if not install:
        print(
            "FLAG: desktop packaging not built (JOTBEAT_EXPORT_WRAPPERS=0 — scaffold only)"
        )
    else:
        reason = _npm_step("npm install", desktop)
        if reason:
            print(f"FLAG: desktop packaging not built ({reason})")
        else:
            print("desktop: electron installed (run `npm start` in desktop/)")

    # The dist/ copy is the export artifact: shell + pointer to the web build.
    out = DIST / "desktop"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(desktop / "main.js", out / "main.js")
    shutil.copyfile(desktop / "package.json", out / "package.json")
    print("desktop shell -> dist/desktop")


def _mobile(install: bool) -> None:
    mobile = ROOT / "mobile"
    mobile.mkdir(exist_ok=True)
    (mobile / "package.json").write_text(MOBILE_PACKAGE_JSON, encoding="utf-8")
    (mobile / "capacitor.config.json").write_text(
        MOBILE_CAPACITOR_CONFIG, encoding="utf-8"
    )

    if not install:
        print(
            "FLAG: mobile packaging not built (JOTBEAT_EXPORT_WRAPPERS=0 — scaffold only)"
        )
    else:
        reason = _npm_step("npm install", mobile)
        if reason:
            print(f"FLAG: mobile packaging not built ({reason})")
        elif (mobile / "android").exists():
            print("mobile: android platform already present (mobile/android)")
        else:
            reason = _npm_step("npx cap add android", mobile)
            if reason:
                print(f"FLAG: mobile android platform not added ({reason})")
            else:
                print("mobile: android platform added (mobile/android)")

    out = DIST / "mobile"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(mobile / "capacitor.config.json", out / "capacitor.config.json")
    shutil.copyfile(mobile / "package.json", out / "package.json")
    print("mobile shell -> dist/mobile")


def run_export(install_wrappers: bool) -> int:
    """Exit 0 only if the web build + zip succeeded; wrappers only FLAG."""
    if not _build_web():
        return 1
    if _zip_web() is None:
        return 1
    _desktop(install_wrappers)
    _mobile(install_wrappers)
    print("export complete — web is standalone; wrappers are untested shells (D-0001)")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(run_export(os.environ.get("JOTBEAT_EXPORT_WRAPPERS", "1") != "0"))
