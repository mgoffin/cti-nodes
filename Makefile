.PHONY: install install-backend install-frontend run run-backend run-frontend dev build clean test docker-build docker-up docker-down docker-logs help

# Default target
all: install build

# =============================================================================
# Installation
# =============================================================================

# Install all dependencies (Linux/macOS)
install: install-backend install-frontend

install-backend:
	cd backend && python3 -m venv venv && \
	. venv/bin/activate && pip install -r requirements.txt

install-backend-win:
	cd backend && python -m venv venv && \
	venv\Scripts\pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

# =============================================================================
# Build
# =============================================================================

build:
	cd frontend && npm run build

# =============================================================================
# Run (Production)
# =============================================================================

run: build run-backend

run-backend:
	cd backend && . venv/bin/activate && python -m app.main

run-backend-win:
	cd backend && venv\Scripts\python -m app.main

run-frontend:
	cd frontend && npm run preview

# =============================================================================
# Development Mode (Hot Reload)
# =============================================================================

dev:
	@echo "=========================================="
	@echo "Starting development mode"
	@echo "=========================================="
	@echo ""
	@echo "Run these commands in separate terminals:"
	@echo ""
	@echo "  Terminal 1 (Backend):"
	@echo "    make dev-backend"
	@echo ""
	@echo "  Terminal 2 (Frontend):"
	@echo "    make dev-frontend"
	@echo ""
	@echo "Frontend: http://localhost:5173"
	@echo "Backend:  http://localhost:8000"
	@echo "=========================================="

dev-backend:
	cd backend && . venv/bin/activate && NODES_DEBUG=true python -m app.main

dev-backend-win:
	cd backend && set NODES_DEBUG=true && venv\Scripts\python -m app.main

dev-frontend:
	cd frontend && npm run dev

# =============================================================================
# Testing
# =============================================================================

test:
	cd backend && . venv/bin/activate && pytest

test-win:
	cd backend && venv\Scripts\pytest

lint:
	cd frontend && npm run lint

# =============================================================================
# Docker
# =============================================================================

docker-build:
	docker-compose -f docker/docker-compose.yml build

docker-up:
	docker-compose -f docker/docker-compose.yml up -d --build
	@echo ""
	@echo "=========================================="
	@echo "Nodes is starting..."
	@echo "Open http://localhost:8000 in your browser"
	@echo "=========================================="

docker-down:
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	docker-compose -f docker/docker-compose.yml logs -f

docker-restart:
	docker-compose -f docker/docker-compose.yml restart

docker-clean:
	docker-compose -f docker/docker-compose.yml down -v --rmi local

# =============================================================================
# Database
# =============================================================================

init-db:
	cd backend && . venv/bin/activate && python -c "from app.core.database import init_database; import asyncio; asyncio.run(init_database())"

init-db-win:
	cd backend && venv\Scripts\python -c "from app.core.database import init_database; import asyncio; asyncio.run(init_database())"

# =============================================================================
# Cleanup
# =============================================================================

clean:
	rm -rf backend/venv
	rm -rf backend/data
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf backend/app/**/__pycache__
	rm -rf frontend/node_modules
	rm -rf frontend/dist
	rm -rf .pytest_cache

clean-win:
	if exist backend\venv rmdir /s /q backend\venv
	if exist backend\data rmdir /s /q backend\data
	if exist frontend\node_modules rmdir /s /q frontend\node_modules
	if exist frontend\dist rmdir /s /q frontend\dist

# =============================================================================
# Help
# =============================================================================

help:
	@echo "=========================================="
	@echo "Nodes - Threat Intel Notebook"
	@echo "=========================================="
	@echo ""
	@echo "Quick Start (Docker):"
	@echo "  make docker-up        Build and start with Docker"
	@echo "  make docker-down      Stop containers"
	@echo "  make docker-logs      View logs"
	@echo ""
	@echo "Quick Start (Manual):"
	@echo "  make install          Install dependencies"
	@echo "  make build            Build frontend"
	@echo "  make run              Run application"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Show dev mode instructions"
	@echo "  make dev-backend      Run backend with hot reload"
	@echo "  make dev-frontend     Run frontend with hot reload"
	@echo "  make test             Run tests"
	@echo "  make lint             Lint frontend code"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Remove all build artifacts"
	@echo "  make docker-clean     Remove Docker containers and images"
	@echo ""
	@echo "Windows: Use *-win variants (e.g., make run-backend-win)"
	@echo ""
