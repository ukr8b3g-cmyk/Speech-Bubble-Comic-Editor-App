@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto :failed
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-desktop.txt
if errorlevel 1 goto :failed

start "" ".venv\Scripts\pythonw.exe" -m desktop_app.main
exit /b 0

:failed
echo.
echo Setup failed. Check the message above.
pause
exit /b 1
