# Lifeforge Docker Management Script for Windows PowerShell
# Usage: .\docker.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Lifeforge Docker Commands:" -ForegroundColor Cyan
    Write-Host "  .\docker.ps1 build       - Build all Docker images" -ForegroundColor Green
    Write-Host "  .\docker.ps1 up          - Start all services (production)" -ForegroundColor Green
    Write-Host "  .\docker.ps1 dev         - Start all services (development)" -ForegroundColor Green
    Write-Host "  .\docker.ps1 down        - Stop all services" -ForegroundColor Green
    Write-Host "  .\docker.ps1 restart     - Restart all services" -ForegroundColor Green
    Write-Host "  .\docker.ps1 logs        - View logs from all services" -ForegroundColor Green
    Write-Host "  .\docker.ps1 logs-be     - View backend logs only" -ForegroundColor Green
    Write-Host "  .\docker.ps1 logs-fe     - View frontend logs only" -ForegroundColor Green
    Write-Host "  .\docker.ps1 clean       - Remove all containers, images, and volumes" -ForegroundColor Green
    Write-Host "  .\docker.ps1 shell-be    - Open shell in backend container" -ForegroundColor Green
    Write-Host "  .\docker.ps1 shell-fe    - Open shell in frontend container" -ForegroundColor Green
    Write-Host "  .\docker.ps1 health      - Check service health" -ForegroundColor Green
    Write-Host "  .\docker.ps1 prune       - Clean up Docker system" -ForegroundColor Green
}

function Build {
    Write-Host "Building Docker images..." -ForegroundColor Yellow
    docker-compose build
}

function Start-Production {
    Write-Host "Starting services in production mode..." -ForegroundColor Yellow
    docker-compose up -d
}

function Start-Development {
    Write-Host "Starting services in development mode..." -ForegroundColor Yellow
    docker-compose -f docker-compose.dev.yml up
}

function Stop-Services {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    docker-compose down
    docker-compose -f docker-compose.dev.yml down 2>$null
}

function Restart-Services {
    Write-Host "Restarting services..." -ForegroundColor Yellow
    docker-compose restart
}

function Show-Logs {
    docker-compose logs -f
}

function Show-BackendLogs {
    docker-compose logs -f backend
}

function Show-FrontendLogs {
    docker-compose logs -f frontend
}

function Clean-All {
    Write-Host "Removing all containers and images..." -ForegroundColor Yellow
    docker-compose down -v --rmi all
    docker-compose -f docker-compose.dev.yml down -v --rmi all 2>$null
}

function Open-BackendShell {
    Write-Host "Opening shell in backend container..." -ForegroundColor Yellow
    docker-compose exec backend /bin/bash
}

function Open-FrontendShell {
    Write-Host "Opening shell in frontend container..." -ForegroundColor Yellow
    docker-compose exec frontend /bin/sh
}

function Check-Health {
    Write-Host "Checking service health..." -ForegroundColor Yellow

    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/ping" -UseBasicParsing -ErrorAction Stop
        Write-Host "✓ Backend is healthy" -ForegroundColor Green
    } catch {
        Write-Host "✗ Backend is unhealthy" -ForegroundColor Red
    }

    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -ErrorAction Stop
        Write-Host "✓ Frontend is healthy" -ForegroundColor Green
    } catch {
        Write-Host "✗ Frontend is unhealthy" -ForegroundColor Red
    }
}

function Prune-System {
    Write-Host "Cleaning up Docker system..." -ForegroundColor Yellow
    docker system prune -af
    docker volume prune -f
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "build" { Build }
    "up" { Start-Production }
    "dev" { Start-Development }
    "down" { Stop-Services }
    "restart" { Restart-Services }
    "logs" { Show-Logs }
    "logs-be" { Show-BackendLogs }
    "logs-fe" { Show-FrontendLogs }
    "clean" { Clean-All }
    "shell-be" { Open-BackendShell }
    "shell-fe" { Open-FrontendShell }
    "health" { Check-Health }
    "prune" { Prune-System }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
