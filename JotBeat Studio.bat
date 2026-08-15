@echo off
rem JotBeat Studio — one-click launcher.
rem Double-click: starts the settings UI on 127.0.0.1 and opens the browser.
rem pythonw = no console window. Close the app: Task Manager -> pythonw.exe,
rem or run `jotbeat ui` from a terminal instead if you want Ctrl+C.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo venv not found — run: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "studio\cli.py" ui
