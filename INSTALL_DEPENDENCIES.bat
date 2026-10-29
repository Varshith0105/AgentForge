@echo off
title Install AgentForge Dependencies
echo ===================================================
echo   Installing AgentForge Dependencies...
echo ===================================================

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

echo ===================================================
echo [OK] Dependencies installed successfully.
echo ===================================================
pause
