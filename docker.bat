@echo off
REM Lifeforge Docker Management Script for Windows Command Prompt
REM Usage: docker.bat <command>

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="build" goto build
if "%1"=="up" goto up
if "%1"=="dev" goto dev
if "%1"=="down" goto down
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="logs-be" goto logs-be
if "%1"=="logs-fe" goto logs-fe
if "%1"=="clean" goto clean
if "%1"=="shell-be" goto shell-be
if "%1"=="shell-fe" goto shell-fe
if "%1"=="health" goto health
if "%1"=="prune" goto prune
goto unknown

:help
echo Lifeforge Docker Commands:
echo   docker.bat build       - Build all Docker images
echo   docker.bat up          - Start all services (production)
echo   docker.bat dev         - Start all services (development)
echo   docker.bat down        - Stop all services
echo   docker.bat restart     - Restart all services
echo   docker.bat logs        - View logs from all services
echo   docker.bat logs-be     - View backend logs only
echo   docker.bat logs-fe     - View frontend logs only
echo   docker.bat clean       - Remove all containers, images, and volumes
echo   docker.bat shell-be    - Open shell in backend container
echo   docker.bat shell-fe    - Open shell in frontend container
echo   docker.bat health      - Check service health
echo   docker.bat prune       - Clean up Docker system
goto end

:build
echo Building Docker images...
docker-compose build
goto end

:up
echo Starting services in production mode...
docker-compose up -d
goto end

:dev
echo Starting services in development mode...
docker-compose -f docker-compose.dev.yml up
goto end

:down
echo Stopping services...
docker-compose down
docker-compose -f docker-compose.dev.yml down 2>nul
goto end

:restart
echo Restarting services...
docker-compose restart
goto end

:logs
docker-compose logs -f
goto end

:logs-be
docker-compose logs -f backend
goto end

:logs-fe
docker-compose logs -f frontend
goto end

:clean
echo Removing all containers and images...
docker-compose down -v --rmi all
docker-compose -f docker-compose.dev.yml down -v --rmi all 2>nul
goto end

:shell-be
echo Opening shell in backend container...
docker-compose exec backend /bin/bash
goto end

:shell-fe
echo Opening shell in frontend container...
docker-compose exec frontend /bin/sh
goto end

:health
echo Checking service health...
curl -f http://localhost:8000/ping && echo Backend is healthy || echo Backend is unhealthy
curl -f http://localhost:3000 && echo Frontend is healthy || echo Frontend is unhealthy
goto end

:prune
echo Cleaning up Docker system...
docker system prune -af
docker volume prune -f
goto end

:unknown
echo Unknown command: %1
echo.
goto help

:end
