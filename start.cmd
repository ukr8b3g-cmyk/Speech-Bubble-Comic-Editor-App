@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
  echo The Desktop environment is not installed.
  echo Run setup_and_start.cmd first.
  pause
  exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" -m desktop_app.main
exit /b 0
