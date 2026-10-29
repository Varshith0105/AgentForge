@echo off
title Check AgentForge Platform Health
echo ===================================================
echo   Checking AgentForge Status...
echo ===================================================

powershell -Command "try { $res = Invoke-RestMethod -Uri 'http://localhost:8000/health' -TimeoutSec 3; Write-Host '[HEALTH CHECK OK]' -ForegroundColor Green; Write-Host ($res | ConvertTo-Json) } catch { Write-Host '[HEALTH CHECK FAILED] Server not responding on http://localhost:8000' -ForegroundColor Red }"
echo ===================================================
pause
