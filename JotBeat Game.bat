@echo off
rem JotBeat Game — one-click launcher.
rem Double-click: starts the game dev server on http://localhost:8080 and
rem opens the browser. The server runs in this window — close it to stop.
cd /d "%~dp0game"
start "" http://localhost:8080
npm run dev-nolog
