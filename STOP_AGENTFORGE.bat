@echo off
title Stop AgentForge Platform
echo ===================================================
echo   Stopping AgentForge Platform...
echo ===================================================

powershell -Command "Get-Process -Name 'python' -ErrorAction SilentlyContinue | ForEach-Object { $cmd = (Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine; if ($cmd -like '*uvicorn*app.main:app*') { Stop-Process -Id $_.Id -Force; Write-Host \"Stopped AgentForge PID: $($_.Id)\" } }"

echo [OK] AgentForge platform stopped.
