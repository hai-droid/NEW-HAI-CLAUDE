@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo.
echo === Campaign Machine - Windows setup ===
echo.

where winget >nul 2>nul
if errorlevel 1 (
  echo winget not found. Install "App Installer" from the Microsoft Store, then run this again.
  pause & exit /b 1
)

where git >nul 2>nul || (echo Installing Git... & winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements)
where node >nul 2>nul || (echo Installing Node.js LTS... & winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements)
where python >nul 2>nul || (echo Installing Python... & winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements)

where claude >nul 2>nul || (
  echo Installing Claude Code...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
)

echo.
echo Installing Python packages...
python -m pip install --user -r requirements.txt
if errorlevel 1 (
  echo.
  echo If "python" was just installed, close this window, open a new one and run install-windows.bat again.
  pause & exit /b 1
)

if not exist .env copy .env.example .env >nul

echo.
echo === Done ===
echo 1. Open .env in Notepad and fill in the keys (see README).
echo 2. Open a terminal in this folder and type: claude
echo 3. In Claude Code type: /campaign demo-studio
echo.
pause
