.PHONY: help install dev start-api start-worker start-beat start-redis migrate test lint format clean db-reset db-create logs-api logs-worker logs-beat

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)WeatherOps Backend - Local Development$(NC)"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(NC)"
	@echo "  make install          Install dependencies"
	@echo "  make migrate          Run database migrations"
	@echo ""
	@echo "$(GREEN)Development Commands:$(NC)"
	@echo "  make dev              Start all services (API, Worker, Beat, Redis)"
	@echo "  make start-api        Start FastAPI server only"
	@echo "  make start-worker     Start Celery worker only"
	@echo "  make start-beat       Start Celery beat scheduler only"
	@echo "  make start-redis      Start Redis server only"
	@echo ""
	@echo "$(GREEN)Database Commands:$(NC)"
	@echo "  make db-create        Create local database and user"
	@echo "  make db-reset         Reset database (drop all tables and re-migrate)"
	@echo ""
	@echo "$(GREEN)Testing & Code Quality:$(NC)"
	@echo "  make test             Run all tests"
	@echo "  make test-verbose     Run tests with verbose output"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code (black, isort)"
	@echo "  make type-check       Run type checking with mypy"
	@echo ""
	@echo "$(GREEN)Utility Commands:$(NC)"
	@echo "  make clean            Remove virtual environment and cache files"
	@echo "  make shell            Open Python interactive shell with app context"
	@echo ""

install:
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements/base.txt
	pip install -r requirements/dev.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	python run_migrations.py
	@echo "$(GREEN)✓ Migrations completed$(NC)"

db-create:
	@echo "$(BLUE)Creating local database and user...$(NC)"
	@echo "$(YELLOW)Note: Ensure PostgreSQL is running$(NC)"
	createuser -P weatherops_dev 2>/dev/null || true
	createdb -U weatherops_dev weatherops_local 2>/dev/null || true
	@echo "$(GREEN)✓ Database created$(NC)"

db-reset:
	@echo "$(YELLOW)⚠ Resetting database (this will delete all data)...$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "$(GREEN)✓ Database reset completed$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

start-redis:
	@echo "$(BLUE)Starting Redis server...$(NC)"
	@echo "$(YELLOW)Make sure Redis is installed: brew install redis (macOS)$(NC)"
	redis-server

start-api:
	@echo "$(BLUE)Starting FastAPI server...$(NC)"
	@echo "$(YELLOW)API will be available at http://localhost:8000$(NC)"
	@echo "$(YELLOW)Docs at http://localhost:8000/docs$(NC)"
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start-worker:
	@echo "$(BLUE)Starting Celery worker...$(NC)"
	@echo "$(YELLOW)Worker will process tasks from Redis queue$(NC)"
	celery -A app.workers.celery_app worker --loglevel=info

start-beat:
	@echo "$(BLUE)Starting Celery beat scheduler...$(NC)"
	@echo "$(YELLOW)Beat will schedule weather monitoring every 5 minutes$(NC)"
	celery -A app.workers.celery_app beat --loglevel=info

dev:
	@echo "$(GREEN)WeatherOps Local Development Environment$(NC)"
	@echo ""
	@echo "$(YELLOW)Starting all services...$(NC)"
	@echo "$(BLUE)Open 4 terminal windows and run:$(NC)"
	@echo ""
	@echo "  $(YELLOW)Terminal 1:$(NC) make start-api"
	@echo "  $(YELLOW)Terminal 2:$(NC) make start-worker"
	@echo "  $(YELLOW)Terminal 3:$(NC) make start-beat"
	@echo "  $(YELLOW)Terminal 4:$(NC) make start-redis"
	@echo ""
	@echo "$(YELLOW)Then visit:$(NC)"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  ReDoc: http://localhost:8000/redoc"
	@echo ""

test:
	@echo "$(BLUE)Running tests...$(NC)"
	pytest

test-verbose:
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	pytest -v

test-coverage:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov=app --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

lint:
	@echo "$(BLUE)Running linting checks...$(NC)"
	flake8 app tests || true
	@echo "$(BLUE)Type checking...$(NC)"
	mypy app || true

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	black app tests
	isort app tests
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check:
	@echo "$(BLUE)Running type checking...$(NC)"
	mypy app

clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

shell:
	@echo "$(BLUE)Opening Python shell with app context...$(NC)"
	python

.DEFAULT_GOAL := help
