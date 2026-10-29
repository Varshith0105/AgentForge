@echo off
echo ==========================================
echo Starting AgentForge Frontend Server
echo ==========================================
echo.
echo Frontend Platform: http://localhost:3000/frontend/app.html
echo Landing Page: http://localhost:3000/index.html
echo Login Page: http://localhost:3000/frontend/pages/login.html
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0.."
python -m http.server 3000

pause
