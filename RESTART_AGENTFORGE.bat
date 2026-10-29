@echo off
title Restart AgentForge Platform
echo ===================================================
echo   Restarting AgentForge Platform...
echo ===================================================

call "%~dp0STOP_AGENTFORGE.bat"
timeout /t 2 /nobreak >nul
call "%~dp0START_AGENTFORGE.bat"
