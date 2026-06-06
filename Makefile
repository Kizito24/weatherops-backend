.PHONY: help start stop logs build migrate reset-db status clean install

help:
	@echo "WeatherOps Backend - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Service Management:"
	@echo "  make start              Start all services (PostgreSQL, Redis, FastAPI, Celery)"
	@echo "  make stop               Stop all services"
	@echo "  make logs               View container logs (streaming)"
	@echo "  make status             Show status of all containers"
	@echo ""
	@echo "Build & Setup:"
	@echo "  make build              Build Docker images"
	@echo "  make install            Install Python dependencies"
	@echo ""
	@echo "Database:"
	@echo "  make migrate            Run database migrations (upgrade head)"
	@echo "  make reset-db           Reset database (drop all data and recreate)"
	@echo "  make downgrade-db       Downgrade database by one migration"
	@echo "  make history-db         Show migration history"
	@echo ""
	@echo "Development:"
	@echo "  make clean              Stop services and clean volumes"
	@echo "  make help               Show this help message"
	@echo ""

# Service Management
start:
	@echo "Starting WeatherOps services..."
	@echo "  - PostgreSQL (port 5433)"
	@echo "  - Redis (port 6379)"
	@echo "  - FastAPI Backend (port 8001)"
	@echo "  - Celery Worker"
	docker compose up -d
	@echo "[OK] All services started!"
	@echo ""
	@echo "Service URLs:"
	@echo "  FastAPI API: http://localhost:8001"
	@echo "  API Docs: http://localhost:8001/docs"
	@echo "  ReDoc: http://localhost:8001/redoc"
	@echo ""
	@echo "Waiting for services to be healthy..."
	@sleep 3
	@docker compose ps

stop:
	@echo "Stopping all services..."
	docker compose down
	@echo "[OK] All services stopped!"

logs:
	@echo "Showing container logs (Ctrl+C to exit)..."
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-celery:
	docker compose logs -f celery_worker

logs-postgres:
	docker compose logs -f postgres

logs-redis:
	docker compose logs -f redis

status:
	@echo "Container Status:"
	@echo "================="
	docker compose ps
	@echo ""
	@echo "Service Health:"
	@docker compose ps --format "table {{.Service}}\t{{.Status}}"

# Build & Setup
build:
	@echo "Building Docker images..."
	docker compose build
	@echo "[OK] Build completed!"

install:
	@echo "Installing Python dependencies..."
	pip install -e .
	@echo "[OK] Dependencies installed!"

# Database Management
migrate:
	@echo "Running database migrations..."
	docker compose exec -T backend alembic upgrade head
	@echo "[OK] Migrations completed!"

downgrade-db:
	@echo "Downgrading database by one migration..."
	docker compose exec -T backend alembic downgrade -1
	@echo "[OK] Downgrade completed!"

history-db:
	@echo "Migration history:"
	docker compose exec -T backend alembic history

reset-db:
	@echo "⚠️  WARNING: This will DELETE ALL database data!"
	@printf "Are you sure? Type 'yes' to confirm: "; \
	read response; \
	if [ "$$response" = "yes" ]; then \
		echo "Resetting database..."; \
		docker compose down -v; \
		docker volume rm weatherops-postgres_data 2>/dev/null || true; \
		docker volume rm weatherops-redis_data 2>/dev/null || true; \
		echo "Starting fresh services..."; \
		docker compose up -d; \
		echo "Waiting for services to be ready..."; \
		sleep 5; \
		echo "Running migrations..."; \
		docker compose exec -T backend alembic upgrade head; \
		echo "[OK] Database reset completed!"; \
	else \
		echo "Database reset cancelled"; \
	fi

# Development
clean:
	@echo "Cleaning up..."
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "[OK] Cleanup completed!"

shell-backend:
	@echo "Opening shell in backend container..."
	docker compose exec backend /bin/bash

shell-db:
	@echo "Opening PostgreSQL shell..."
	docker compose exec postgres psql -U weatherops -d weatherops
