# Docker & Deployment Guide

This guide explains how to use Docker and the CI/CD pipeline for the Lifeforge project.

> **🪟 Windows Users**: This guide now includes Windows-specific commands using PowerShell! Jump to the [Windows Quick Reference](#-windows-quick-reference) for a TL;DR.

## Table of Contents

- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Choose Your Command Style](#️-choose-your-command-style)
- [Docker Setup](#docker-setup)
  - [File Structure](#file-structure)
  - [Available Commands](#-available-commands)
- [Development vs Production](#development-vs-production)
- [Configuration](#configuration)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Windows-Specific Issues](#windows-specific-issues)
- [Common Workflows](#-common-workflows)
- [Windows Quick Reference](#-windows-quick-reference)

---

## Quick Start

### Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)

### 🖥️ Choose Your Command Style

This project provides multiple ways to run Docker commands depending on your operating system:

| OS | Recommended | Command Example |
|---|---|---|
| **Windows (PowerShell)** | `docker.ps1` | `.\docker.ps1 dev` |
| **Windows (CMD)** | `docker.bat` | `docker.bat dev` |
| **Linux / Mac** | `Makefile` | `make dev` |
| **Any OS** | Docker Compose | `docker-compose -f docker-compose.dev.yml up` |

**For Windows Users**: The `docker.ps1` (PowerShell) and `docker.bat` (Command Prompt) scripts provide the same convenience as Make but work natively on Windows.

**First time PowerShell users**: Enable script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Start the Application (Production Mode)

**Windows (PowerShell)**:
```powershell
.\docker.ps1 build
.\docker.ps1 up
```

**Windows (Command Prompt)**:
```cmd
docker.bat build
docker.bat up
```

**Linux / Mac**:
```bash
make build
make up
```

**Any OS (Docker Compose)**:
```bash
docker-compose build
docker-compose up -d
```

The services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Start the Application (Development Mode)

**Windows (PowerShell)**:
```powershell
.\docker.ps1 dev
```

**Windows (Command Prompt)**:
```cmd
docker.bat dev
```

**Linux / Mac**:
```bash
make dev
```

**Any OS (Docker Compose)**:
```bash
docker-compose -f docker-compose.dev.yml up
```

This starts services with:
- Hot-reload enabled
- Source code mounted as volumes
- Development environment variables

---

## Docker Setup

### File Structure

```
Lifeforge/
├── docker-compose.yml          # Production configuration
├── docker-compose.dev.yml      # Development configuration
├── Makefile                    # Docker commands (Linux/Mac)
├── docker.ps1                  # Docker commands (Windows PowerShell)
├── docker.bat                  # Docker commands (Windows CMD)
├── .env                        # Environment variables
├── .env.example                # Environment template
├── services/
│   ├── backend/
│   │   ├── Dockerfile          # Backend production image
│   │   └── .dockerignore       # Files to exclude
│   └── frontend/
│       └── multirag/
│           ├── Dockerfile      # Frontend production image
│           ├── Dockerfile.dev  # Frontend development image
│           └── .dockerignore   # Files to exclude
└── .github/
    └── workflows/
        └── ci-cd.yml           # GitHub Actions pipeline
```

### 📋 Available Commands

All command scripts (`docker.ps1`, `docker.bat`, `Makefile`) support the same operations:

| Command | Description |
|---------|-------------|
| `help` | Show all available commands |
| `build` | Build all Docker images |
| `up` | Start services in production mode |
| `dev` | Start services in development mode (hot-reload) |
| `down` | Stop all services |
| `restart` | Restart all services |
| `logs` | View logs from all services |
| `logs-be` | View backend logs only |
| `logs-fe` | View frontend logs only |
| `clean` | Remove all containers, images, and volumes |
| `shell-be` | Open shell in backend container |
| `shell-fe` | Open shell in frontend container |
| `health` | Check service health status |
| `prune` | Clean up Docker system |

**Examples**:
```powershell
# Windows PowerShell
.\docker.ps1 help
.\docker.ps1 logs-be

# Windows CMD
docker.bat help
docker.bat logs-be

# Linux/Mac
make help
make logs-be
```

### Backend Dockerfile

The backend uses a **multi-stage build** for optimization:

1. **Builder Stage**: Installs dependencies and downloads NLTK data
2. **Runtime Stage**: Minimal image with only runtime dependencies

**Key Features**:
- Python 3.11 slim base image
- Virtual environment isolation
- NLTK data pre-downloaded
- Health checks configured
- Non-root user for security

### Frontend Dockerfile

The frontend also uses **multi-stage build**:

1. **Dependencies Stage**: Installs node_modules
2. **Builder Stage**: Builds Next.js app
3. **Runner Stage**: Minimal production image

**Key Features**:
- Node 20 Alpine base image
- Standalone output mode enabled
- Non-root user (nextjs)
- Health checks configured
- Optimized for production

---

## Development vs Production

### Production Mode (`docker-compose.yml`)

**Windows (PowerShell)**:
```powershell
.\docker.ps1 up
```

**Linux/Mac**:
```bash
make up
```

**Any OS**:
```bash
docker-compose up -d
```

**Characteristics**:
- Optimized production images
- No source code mounting
- Environment: `NODE_ENV=production`
- Standalone builds
- Minimal image size
- Health checks enabled

**Use When**:
- Deploying to staging/production
- Testing production builds locally
- Performance testing

### Development Mode (`docker-compose.dev.yml`)

**Windows (PowerShell)**:
```powershell
.\docker.ps1 dev
```

**Linux/Mac**:
```bash
make dev
```

**Any OS**:
```bash
docker-compose -f docker-compose.dev.yml up
```

**Characteristics**:
- Source code mounted as volumes
- Hot-reload enabled (both backend and frontend)
- Development environment variables
- Full debug logging
- LangSmith tracing enabled

**Use When**:
- Active development
- Testing changes quickly
- Debugging issues

---

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

**Windows (PowerShell)**:
```powershell
Copy-Item .env.example .env
```

**Windows (CMD)**:
```cmd
copy .env.example .env
```

**Linux/Mac**:
```bash
cp .env.example .env
```

Then edit `.env` with your API keys and configuration.

**Required Variables**:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key

# LLM Configuration
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.2
QUERY_ENHANCER_MODEL=gpt-4o-mini
QUERY_ENHANCER_TEMPERATURE=0.7

# Optional: LangSmith (for monitoring)
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=lifeforge
```

### Modifying Docker Configuration

#### Change Ports

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Change from 8000 to 8080

  frontend:
    ports:
      - "3001:3000"  # Change from 3000 to 3001
```

#### Add Environment Variables

```yaml
services:
  backend:
    environment:
      - NEW_ENV_VAR=value
      - ANOTHER_VAR=${FROM_ENV_FILE}
```

#### Mount Additional Volumes

```yaml
services:
  backend:
    volumes:
      - ./data:/app/data
      - ./models:/app/models
```

#### Change Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

The pipeline (`.github/workflows/ci-cd.yml`) runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual trigger via GitHub UI

### Pipeline Stages

#### 1. Test Backend

```yaml
- Python 3.11 setup
- Install dependencies
- Run flake8 linting
- Run pytest (when tests exist)
```

#### 2. Test Frontend

```yaml
- Node.js 20 setup
- Install dependencies
- Run ESLint
- Build Next.js app
- Run tests (when tests exist)
```

#### 3. Build & Push Images

**Only on push to main/develop**:

```yaml
- Build Docker images
- Tag with branch name and SHA
- Push to GitHub Container Registry (ghcr.io)
- Cache layers for faster builds
```

#### 4. Deploy (Optional)

Uncomment the deploy job to enable automatic deployment.

### Setting Up CI/CD

#### 1. Enable GitHub Container Registry

No setup needed - uses `GITHUB_TOKEN` automatically.

#### 2. Alternative: Use Docker Hub

Uncomment the Docker Hub login step and add secrets:

```yaml
# In GitHub Settings > Secrets and variables > Actions
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_token
```

#### 3. Enable Deployment

Add deployment secrets:

```yaml
DEPLOY_HOST=your_server_ip
DEPLOY_USER=deploy_user
DEPLOY_SSH_KEY=your_ssh_private_key
```

Then uncomment the `deploy` job in `ci-cd.yml`.

### Modifying the Pipeline

#### Add Tests

Uncomment test steps in `ci-cd.yml`:

```yaml
- name: Run tests
  working-directory: ./services/backend
  run: |
    pytest tests/ -v --cov=app --cov-report=xml
```

#### Change Python/Node Version

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # Change version

- uses: actions/setup-node@v4
  with:
    node-version: '22'  # Change version
```

#### Add Code Coverage

```yaml
- name: Upload coverage reports
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    token: ${{ secrets.CODECOV_TOKEN }}
```

#### Add Slack Notifications

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Build failed: ${{ github.repository }}"
      }
```

---

## Deployment

### Deploy to Production Server

#### Option 1: Using Docker Compose (Simple)

On your server:

```bash
# 1. Clone repository
git clone https://github.com/yourusername/lifeforge.git
cd lifeforge

# 2. Create .env file
cp .env.example .env
# Edit .env with production values

# 3. Start services
docker-compose up -d

# 4. Check logs
docker-compose logs -f
```

#### Option 2: Using Pre-built Images

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: ghcr.io/yourusername/lifeforge/backend:latest
    # ... rest of config

  frontend:
    image: ghcr.io/yourusername/lifeforge/frontend:latest
    # ... rest of config
```

```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

#### Option 3: Using CI/CD Auto-Deploy

1. Set up deployment secrets in GitHub
2. Uncomment deploy job in `ci-cd.yml`
3. Push to `main` branch
4. Pipeline automatically deploys

### Deploy to Cloud Platforms

#### AWS ECS

```bash
# Install ECS CLI
ecs-cli configure --cluster lifeforge --region us-east-1

# Deploy
ecs-cli compose -f docker-compose.yml up
```

#### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/backend
gcloud builds submit --tag gcr.io/PROJECT_ID/frontend

# Deploy
gcloud run deploy backend --image gcr.io/PROJECT_ID/backend
gcloud run deploy frontend --image gcr.io/PROJECT_ID/frontend
```

#### DigitalOcean App Platform

```bash
# Use doctl or web UI
doctl apps create --spec .do/app.yaml
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution 1 (Windows)**: Find and kill the process
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with the actual number)
taskkill /PID <PID> /F
```

**Solution 1 (Linux/Mac)**: Find and kill the process
```bash
# Find process
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

**Solution 2 (Any OS)**: Change port in docker-compose.yml
```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Use different external port
```

#### Container Keeps Restarting

**Check logs**:
```powershell
# Windows
.\docker.ps1 logs-be

# Any OS
docker-compose logs backend
```

**Common causes**:
1. Missing environment variables in `.env` file
2. Database connection issues
3. Import errors or missing dependencies
4. Port conflicts

**Debug with shell**:
```powershell
# Windows
.\docker.ps1 shell-be

# Linux/Mac
make shell-be

# Any OS
docker-compose exec backend /bin/bash
```

Then inside the container, try running the application manually:
```bash
cd /app
python -m uvicorn app.api.app:app --host 0.0.0.0 --port 8000
```

#### Hot-Reload Not Working

```bash
# For Windows/Mac, add polling
environment:
  - WATCHPACK_POLLING=true
```

#### Build Fails

```bash
# Clear cache and rebuild
docker-compose build --no-cache

# Check disk space
docker system df
docker system prune -a
```

#### Permission Issues

```bash
# On Linux, fix file ownership
sudo chown -R $USER:$USER .

# Or run with sudo
sudo docker-compose up
```

### Windows-Specific Issues

#### "Cannot be loaded because running scripts is disabled"

**Error in PowerShell**:
```
.\docker.ps1 : File cannot be loaded because running scripts is disabled on this system.
```

**Solution**:
```powershell
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Line Endings (CRLF vs LF)

**Error**: Scripts fail with `\r` errors in containers

**Solution**: Configure Git to use LF line endings:
```bash
git config --global core.autocrlf false
git rm --cached -r .
git reset --hard
```

#### Path Issues

**Windows paths** in volumes may need forward slashes:
```yaml
volumes:
  - ./data:/app/data  # Good
  - .\data:/app/data  # May cause issues
```

### Useful Commands

**View container status**:
```powershell
# Windows
.\docker.ps1 health

# Any OS
docker-compose ps
```

**View resource usage**:
```bash
docker stats
```

**Execute command in container**:
```powershell
# Windows - Open shell first
.\docker.ps1 shell-be

# Then inside container:
python -c "print('Hello')"
cd app/
ls -la
```

**Copy files from container**:
```bash
docker cp lifeforge-backend:/app/logs ./local-logs
```

**View container details**:
```bash
docker inspect lifeforge-backend
```

**Rebuild single service**:
```bash
docker-compose build backend
docker-compose up -d backend
```

**Check Docker version**:
```bash
docker --version
docker-compose --version
```

---

## 📚 Common Workflows

### Daily Development (Windows)

```powershell
# Morning - Start fresh
.\docker.ps1 build
.\docker.ps1 dev

# Check if backend is working
.\docker.ps1 logs-be

# Make code changes... hot-reload handles it automatically!

# Debug an issue
.\docker.ps1 shell-be
# Inside container: python app/api/app.py

# End of day - stop everything
.\docker.ps1 down
```

### Daily Development (Linux/Mac)

```bash
# Morning - Start fresh
make build
make dev

# Check if backend is working
make logs-be

# Debug an issue
make shell-be

# End of day
make down
```

### Testing Before Deployment

```powershell
# Windows
.\docker.ps1 build
.\docker.ps1 up
.\docker.ps1 health

# Linux/Mac
make build
make up
make health
```

### Clean Restart (Something's Wrong)

```powershell
# Windows
.\docker.ps1 down
.\docker.ps1 clean
.\docker.ps1 prune
.\docker.ps1 build
.\docker.ps1 dev

# Linux/Mac
make down
make clean
make prune
make build
make dev
```

---

## Best Practices

1. **Always use .env files** - Never commit secrets to git
2. **Use health checks** - Ensure services are actually ready
3. **Multi-stage builds** - Keep images small
4. **Cache layers** - Order Dockerfile commands properly
5. **Use .dockerignore** - Exclude unnecessary files
6. **Version tags** - Don't rely on `latest` in production
7. **Monitor logs** - Set up logging aggregation
8. **Regular updates** - Keep base images updated

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Next.js Docker Documentation](https://nextjs.org/docs/deployment#docker-image)

---

## 🪟 Windows Quick Reference

### First Time Setup

```powershell
# 1. Enable PowerShell scripts (one-time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. Copy environment file
Copy-Item .env.example .env

# 3. Edit .env with your API keys
notepad .env

# 4. Build and start
.\docker.ps1 build
.\docker.ps1 dev
```

### Most Used Commands

```powershell
.\docker.ps1 help      # Show all commands
.\docker.ps1 dev       # Start development
.\docker.ps1 logs      # View logs
.\docker.ps1 logs-be   # Backend logs only
.\docker.ps1 down      # Stop services
.\docker.ps1 restart   # Restart services
.\docker.ps1 shell-be  # Debug backend
.\docker.ps1 clean     # Full cleanup
```

### Troubleshooting

```powershell
# Can't run scripts?
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Port in use?
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Something broken?
.\docker.ps1 down
.\docker.ps1 clean
.\docker.ps1 prune
.\docker.ps1 build
.\docker.ps1 dev
```

---

**Need Help?**

If you encounter issues not covered here, please:
1. **Check the logs**: `.\docker.ps1 logs` (Windows) or `docker-compose logs -f` (Any OS)
2. **Verify environment**: `docker-compose config`
3. **Check service health**: `.\docker.ps1 health` (Windows) or `make health` (Linux/Mac)
4. **Open an issue on GitHub** with your logs and error messages
