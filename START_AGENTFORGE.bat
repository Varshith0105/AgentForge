@echo off
title AgentForge Production Platform
echo ===================================================
echo   Starting AgentForge AI Engineering Platform
echo ===================================================

cd /d "%~dp0"

:: 1. Verify Docker (optional)
docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker Desktop is running.
) else (
    echo [INFO] Docker Desktop not detected (optional services run locally).
)

:: 2. Activate Python Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] Activated .venv
)

:: 3. Start AgentForge Backend & Frontend (Uvicorn)
echo [OK] Launching AgentForge Platform Server on http://localhost:8000 ...
start /b python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend

:: 4. Wait for Backend Health
echo [WAIT] Waiting for AgentForge server readiness...
powershell -Command "for ($i=0; $i -lt 30; $i++) { try { $r = Invoke-RestMethod -Uri 'http://localhost:8000/health' -TimeoutSec 2; if ($r.status -eq 'healthy') { break } } catch { Start-Sleep -Seconds 1 } }"

echo ===================================================
echo [SUCCESS] AgentForge is running!
echo   • Frontend App:  http://localhost:8000/app
echo   • Landing Page:  http://localhost:8000/
echo   • API Docs:      http://localhost:8000/docs
echo ===================================================

:: 5. Open Browser Automatically
start http://localhost:8000/app
