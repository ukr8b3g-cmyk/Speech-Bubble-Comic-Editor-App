@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The Desktop environment is not installed.
  echo Run setup_and_start.cmd first.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean SpeechBubbleComicEditorApp.spec
if errorlevel 1 goto :failed

copy /y "README.md" "dist\SpeechBubbleComicEditorApp\README.md" >nul
copy /y "LICENSE" "dist\SpeechBubbleComicEditorApp\LICENSE" >nul
copy /y "PRIVACY.md" "dist\SpeechBubbleComicEditorApp\PRIVACY.md" >nul
copy /y "SECURITY.md" "dist\SpeechBubbleComicEditorApp\SECURITY.md" >nul
copy /y "THIRD-PARTY-NOTICES.md" "dist\SpeechBubbleComicEditorApp\THIRD-PARTY-NOTICES.md" >nul

echo.
echo Portable build:
echo %CD%\dist\SpeechBubbleComicEditorApp\SpeechBubbleComicEditorApp.exe
exit /b 0

:failed
echo.
echo Build failed. Check the message above.
pause
exit /b 1
