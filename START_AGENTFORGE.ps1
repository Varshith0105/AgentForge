# AgentForge Launch Script for PowerShell
Set-Location -Path $PSScriptRoot

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting AgentForge AI Engineering Platform" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# 1. Activate Virtual Environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
    Write-Host "[OK] Activated .venv" -ForegroundColor Green
}

# 2. Start Uvicorn Background Process
Write-Host "[OK] Launching AgentForge Server on http://localhost:8000 ..." -ForegroundColor Green
$proc = Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory "$PSScriptRoot\backend" -PassThru -NoNewWindow

# 3. Wait for Health
Write-Host "[WAIT] Waiting for AgentForge server readiness..." -ForegroundColor Yellow
for ($i=0; $i -lt 15; $i++) {
    try {
        $res = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2
        if ($res.status -eq "healthy") {
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] AgentForge is running!" -ForegroundColor Green
Write-Host "  • Frontend Workspace: http://localhost:8000/app" -ForegroundColor Yellow
Write-Host "  • Landing Page:       http://localhost:8000/" -ForegroundColor Yellow
Write-Host "  • Swagger API Docs:   http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  • Health Check:       http://localhost:8000/health" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

# 4. Open Browser
Start-Process "http://localhost:8000/app"
