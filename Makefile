# Lifeforge Docker Management Makefile
# Use this file for easy Docker operations

.PHONY: help build up down restart logs clean test dev prod

# Default target
help:
	@echo "Lifeforge Docker Commands:"
	@echo "  make build       - Build all Docker images"
	@echo "  make up          - Start all services (production)"
	@echo "  make dev         - Start all services (development with hot-reload)"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make logs-be     - View backend logs only"
	@echo "  make logs-fe     - View frontend logs only"
	@echo "  make clean       - Remove all containers, images, and volumes"
	@echo "  make test        - Run tests"
	@echo "  make shell-be    - Open shell in backend container"
	@echo "  make shell-fe    - Open shell in frontend container"
	@echo "  make prune       - Clean up Docker system"

# Build images
build:
	@echo "Building Docker images..."
	docker-compose build

build-dev:
	@echo "Building Docker images for development..."
	docker-compose -f docker-compose.dev.yml build

# Start services (production)
up:
	@echo "Starting services in production mode..."
	docker-compose up -d

# Start services (development)
dev:
	@echo "Starting services in development mode..."
	docker-compose -f docker-compose.dev.yml up

# Stop services
down:
	@echo "Stopping services..."
	docker-compose down
	docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart

restart-be:
	@echo "Restarting backend..."
	docker-compose restart backend

restart-fe:
	@echo "Restarting frontend..."
	docker-compose restart frontend

# View logs
logs:
	docker-compose logs -f

logs-be:
	docker-compose logs -f backend

logs-fe:
	docker-compose logs -f frontend

# Clean up
clean:
	@echo "Removing all containers and images..."
	docker-compose down -v --rmi all
	docker-compose -f docker-compose.dev.yml down -v --rmi all 2>/dev/null || true

# Run tests
test:
	@echo "Running tests..."
	docker-compose run --rm backend pytest tests/ -v
	docker-compose run --rm frontend npm test

# Shell access
shell-be:
	@echo "Opening shell in backend container..."
	docker-compose exec backend /bin/bash

shell-fe:
	@echo "Opening shell in frontend container..."
	docker-compose exec frontend /bin/sh

# System cleanup
prune:
	@echo "Cleaning up Docker system..."
	docker system prune -af
	docker volume prune -f

# Check service health
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/ping && echo "✓ Backend is healthy" || echo "✗ Backend is unhealthy"
	@curl -f http://localhost:3000 && echo "✓ Frontend is healthy" || echo "✗ Frontend is unhealthy"

# Production deployment
prod:
	@echo "Deploying to production..."
	docker-compose pull
	docker-compose up -d
	docker system prune -af
