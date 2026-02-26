# start-dev.ps1 — start backend and frontend in separate PowerShell windows

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$BackendDir  = Join-Path $RepoRoot "services\backend"
$FrontendDir = Join-Path $RepoRoot "services\frontend\multirag"

# Backend window
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "& { `$host.UI.RawUI.WindowTitle = 'Lifeforge Backend'; Set-Location '$BackendDir'; uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload }"

# Wait for backend to be ready
Write-Host "Waiting for backend" -NoNewline -ForegroundColor Blue
$ready = $false
while (-not $ready) {
    Start-Sleep -Seconds 1
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/ping" -UseBasicParsing -ErrorAction Stop | Out-Null
        $ready = $true
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Blue
    }
}
Write-Host " ready!" -ForegroundColor Blue

# Frontend window
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "& { `$host.UI.RawUI.WindowTitle = 'Lifeforge Frontend'; Set-Location '$FrontendDir'; npm run dev }"

Write-Host ""
Write-Host "Two windows have been opened:" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Blue
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Close each window (or press Ctrl+C inside it) to stop that service." -ForegroundColor Yellow
