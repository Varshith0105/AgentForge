@echo off
echo ==========================================
echo Starting AgentForge Backend Server
echo ==========================================
echo.

cd /d "%~dp0..\backend"

echo Starting Uvicorn server...
echo Backend URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
