# WeatherOps Backend - Local Development Guide

Complete setup guide for running the WeatherOps event-driven weather intelligence platform locally.

## What is WeatherOps?

WeatherOps is a production-grade backend system for:
- **Monitoring weather** across multiple locations in real-time (via WeatherAI API)
- **Creating intelligent alert rules** based on weather conditions (temperature, rainfall, wind, humidity)
- **Managing locations and preferences** with user-specific settings
- **Processing async tasks** using Celery workers (weather checks every 5 minutes)
- **Sending notifications** via email (SendGrid), SMS (Twilio), and webhooks
- **Authenticating users** with JWT tokens and refresh token rotation
- **Caching data** in Redis for performance optimization

**Tech Stack**: FastAPI + PostgreSQL + Redis + Celery + SQLAlchemy ORM

---

## Prerequisites

Ensure you have these installed:

- **Python 3.12+** — [Download](https://www.python.org/downloads/)
- **PostgreSQL 14+** — [Download](https://www.postgresql.org/download/)
- **Redis 7+** — [Download](https://redis.io/download)
- **Git** — [Download](https://git-scm.com/downloads)
- **GNU Make** (optional, for Makefile commands)

### Quick Install by OS

**macOS (Homebrew):**
```bash
brew install python@3.12 postgresql redis make
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip postgresql postgresql-contrib redis-server build-essential
```

**Windows (WSL2):**
Use Ubuntu/Debian instructions above. Redis on Windows: [Windows builds](https://github.com/microsoftarchive/redis/releases)

---

## 5-Minute Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/Kizito24/weatherops-backend.git
cd weatherops-backend
python3.12 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install and configure
make install
cp .env.example .env
make db-create
make migrate

# 3. Start services (open 4 terminals)
# Terminal 1:
make start-api

# Terminal 2:
make start-worker

# Terminal 3:
make start-beat

# Terminal 4:
make start-redis

# 4. Visit http://localhost:8000/docs
```

---

## Detailed Setup Instructions

### Step 1: Clone Repository

```bash
git clone https://github.com/Kizito24/weatherops-backend.git
cd weatherops-backend
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3.12 -m venv venv

# Activate venv
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

Verify Python version:
```bash
python --version  # Should show 3.12.x
```

### Step 3: Install Dependencies

Using Makefile (easiest):
```bash
make install
```

Or manually:
```bash
pip install -r requirements/base.txt
pip install -r requirements/dev.txt
```

This installs:
- **FastAPI 0.115.0** - Web framework
- **SQLAlchemy 2.0.36** - ORM
- **Celery 5.4.0** - Task queue
- **Redis 5.2.0** - Cache and message broker
- **Pydantic 2.10.3** - Data validation
- **Alembic 1.14.0** - Database migrations
- **And more** - see requirements files

### Step 4: Setup PostgreSQL

Start PostgreSQL service:

```bash
# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# Windows (WSL2):
sudo service postgresql start

# Or verify it's running:
psql --version
```

Create database and user:

```bash
make db-create
```

Or manually:
```bash
# Create user (will prompt for password, use: weatherops_dev)
createuser -P weatherops_dev

# Create database
createdb -U weatherops_dev weatherops_local

# Verify connection
psql -U weatherops_dev -d weatherops_local -c "SELECT 1;"
```

### Step 5: Setup Redis

Start Redis:

```bash
# macOS:
brew services start redis

# Linux:
sudo systemctl start redis-server

# Or run in current terminal:
redis-server

# Verify connection:
redis-cli ping  # Should return: PONG
```

### Step 6: Create .env File

Copy example and customize:

```bash
cp .env.example .env
```

Key variables to set (most have defaults):

```bash
# DATABASE - Local PostgreSQL
DATABASE_URL=postgresql+asyncpg://weatherops_dev:weatherops_dev@localhost:5432/weatherops_local
DATABASE_ECHO=True          # Log SQL queries (development only)
DATABASE_POOL_SIZE=5        # Connection pool size

# REDIS - Local Redis
REDIS_URL=redis://localhost:6379/0

# CELERY (leave empty to use REDIS_URL)
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=

# APPLICATION
ENVIRONMENT=development
DEBUG=True
RELOAD=True                 # Auto-reload on code changes

# SECURITY - CHANGE THESE
SECRET_KEY=your-dev-secret-key-here
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# EXTERNAL SERVICES (optional for local testing)
WEATHERAI_API_KEY=your-key-here
SENDGRID_API_KEY=your-key-here     # Leave empty to skip email
TWILIO_ACCOUNT_SID=your-sid-here   # Leave empty to skip SMS
```

### Step 7: Run Database Migrations

Create all tables:

```bash
make migrate
```

Or manually:
```bash
python run_migrations.py
```

Expected output:
```
Running migrations...
Running migration base_tables
Running migration initial_alert_tables
Running migration add_user_preferences
Running migration add_refresh_tokens
Migrations completed successfully
```

Verify tables created:
```bash
psql -U weatherops_dev -d weatherops_local -c "\dt"
```

---

## Running the Application

### Using Makefile (Recommended)

View all available commands:
```bash
make
```

Start individual services:
```bash
# Terminal 1 - FastAPI API Server (port 8000)
make start-api

# Terminal 2 - Celery Worker (processes tasks)
make start-worker

# Terminal 3 - Celery Beat (schedules tasks every 5 min)
make start-beat

# Terminal 4 - Redis (if not running as service)
make start-redis
```

Or see instructions for starting all:
```bash
make dev
```

### Manual Commands

Terminal 1 - FastAPI (with auto-reload):
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Celery Worker:
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

Terminal 3 - Celery Beat Scheduler:
```bash
celery -A app.workers.celery_app beat --loglevel=info
```

Terminal 4 - Redis:
```bash
redis-server
```

### Verify Everything Works

1. **API Server** - Visit http://localhost:8000/docs
   - Should show Swagger UI with all endpoints
   - Try `GET /api/v1/health` → `{"status": "ok"}`

2. **Celery Worker** - Check terminal 2 output
   - Should show: `[INFO/MainProcess] celery@... ready.`

3. **Celery Beat** - Check terminal 3 output
   - Should show: `[INFO/MainProcess] celery beat v5.x.x is starting.`
   - Weather monitor scheduled: `[INFO] Scheduler: celery.beat.SchedulingError`

4. **Redis** - Test connection:
   ```bash
   redis-cli ping  # Returns: PONG
   ```

---

## API Endpoints Overview

### Authentication
```
POST   /api/v1/auth/register        Create new user account
POST   /api/v1/auth/login           Login and get tokens
POST   /api/v1/auth/refresh         Refresh access token
```

### Locations
```
GET    /api/v1/locations            List all user's locations
POST   /api/v1/locations            Create new location
GET    /api/v1/locations/{id}       Get location details
PUT    /api/v1/locations/{id}       Update location
DELETE /api/v1/locations/{id}       Delete location
```

### Weather
```
GET    /api/v1/weather              Get current weather
GET    /api/v1/weather/usage        Get API usage statistics
```

### Alerts
```
GET    /api/v1/alerts               List user's alerts
GET    /api/v1/alerts/{id}          Get alert details
PUT    /api/v1/alerts/{id}          Update alert status
GET    /api/v1/alerts/location/{id} Get location's alerts
```

### Rules
```
GET    /api/v1/rules                List all rules
POST   /api/v1/rules                Create new rule
GET    /api/v1/rules/{id}           Get rule details
PUT    /api/v1/rules/{id}           Update rule
DELETE /api/v1/rules/{id}           Delete rule
GET    /api/v1/rules/location/{id}  Get location's rules
```

### Health
```
GET    /api/v1/health               Health check status
```

Full API docs: http://localhost:8000/docs

---

## Common Development Tasks

### Run Tests

```bash
# All tests
make test

# Specific test file
make test-verbose

# With coverage report
make test-coverage
# View report: open htmlcov/index.html
```

### Format & Lint Code

```bash
# Format code (Black + isort)
make format

# Run linting checks
make lint

# Type checking
make type-check
```

### Database Operations

```bash
# Create fresh database and user
make db-create

# Reset database (drop all data and re-migrate)
make db-reset

# Run specific migration
alembic upgrade head
alembic downgrade base

# Check migration status
alembic current
```

### Celery Tasks

Monitor tasks with Flower:
```bash
pip install flower
celery -A app.workers.celery_app flower --port=5555
```

Then visit: http://localhost:5555

View pending tasks:
```bash
redis-cli
> keys celery*
> llen celery
```

### Database Inspection

```bash
# Connect to database
psql -U weatherops_dev -d weatherops_local

# List tables
\dt

# View users
SELECT * FROM users;

# View locations
SELECT id, name, latitude, longitude FROM locations;

# View alerts
SELECT id, metric, actual_value, threshold, severity, status FROM alerts;

# View rules
SELECT id, location_id, metric, operator, threshold FROM rules;

# View row count
SELECT count(*) FROM alerts;

# Exit
\q
```

---

## Project Structure

```
weatherops-backend/
├── app/
│   ├── main.py                 # FastAPI app factory
│   ├── api/v1/
│   │   ├── endpoints/          # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── locations.py
│   │   │   ├── weather.py
│   │   │   ├── alerts.py
│   │   │   ├── rules.py
│   │   │   └── health.py
│   │   └── router.py           # Router aggregator
│   ├── models/                 # Database models
│   │   ├── user.py
│   │   ├── location.py
│   │   ├── alert.py
│   │   ├── rule.py
│   │   └── ...
│   ├── schemas/                # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── alert.py
│   │   ├── rule.py
│   │   └── ...
│   ├── services/               # Business logic
│   │   ├── auth_service.py
│   │   ├── alert_service.py
│   │   ├── rule_engine.py      # Rule evaluation logic
│   │   ├── weather_service.py  # WeatherAI integration
│   │   └── ...
│   ├── repositories/           # Data access layer
│   │   ├── user_repository.py
│   │   ├── alert_repository.py
│   │   └── ...
│   ├── core/
│   │   ├── config.py           # Settings (from .env)
│   │   ├── security.py         # JWT, hashing
│   │   ├── channels/           # Notification channels
│   │   │   ├── email.py
│   │   │   ├── sms.py
│   │   │   └── webhook.py
│   │   └── ...
│   ├── workers/                # Celery tasks
│   │   ├── celery_app.py
│   │   ├── beat_schedule.py    # Scheduled tasks config
│   │   └── tasks/
│   │       └── weather_monitor.py
│   └── database/
│       ├── session.py          # Database session
│       └── base.py             # Base models
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── requirements/               # Dependency specifications
│   ├── base.txt
│   └── dev.txt
├── Makefile                    # Development commands
├── LOCAL_DEVELOPMENT.md        # This file
├── .env.example                # Example environment variables
└── render.yaml                 # Render deployment config
```

---

## Database Models

### User
- `id` (UUID, PK)
- `email` (String, unique)
- `hashed_password` (String)
- `is_active` (Boolean)
- `created_at`, `updated_at` (Timestamp)

### Location
- `id` (UUID, PK)
- `user_id` (UUID, FK → User)
- `name` (String)
- `latitude` (Float)
- `longitude` (Float)
- `created_at`, `updated_at` (Timestamp)

### Rule
- `id` (UUID, PK)
- `location_id` (UUID, FK → Location)
- `owner_id` (UUID, FK → User)
- `metric` (String: temperature, rainfall, wind_speed, humidity)
- `operator` (String: >, <, >=, <=, ==)
- `threshold` (Float)
- `is_active` (Boolean)
- `created_at`, `updated_at` (Timestamp)

### Alert
- `id` (UUID, PK)
- `location_id` (UUID, FK → Location)
- `rule_id` (UUID, FK → Rule)
- `user_id` (UUID, FK → User)
- `metric` (String)
- `actual_value` (Float)
- `threshold` (Float)
- `operator` (String)
- `severity` (String: LOW, MEDIUM, HIGH)
- `status` (String: active, resolved)
- `weather_snapshot` (JSON)
- `created_at`, `updated_at`, `resolved_at` (Timestamp)

---

## Alert Flow

```
1. Celery Beat (every 5 minutes)
   └─> Triggers: tasks.weather_monitor

2. Weather Monitor Task
   ├─> Fetch all locations from DB
   ├─> Get current weather from WeatherAI API
   ├─> For each location:
   │   ├─> Get all active rules
   │   ├─> Evaluate rules against weather data
   │   └─> For each triggered rule:
   │       ├─> Create alert (with deduplication)
   │       ├─> Send notifications (email, SMS, webhook)
   │       └─> Return stats

3. Alert Service (create_from_triggered_rule)
   ├─> Check for duplicates (5-min window)
   ├─> Calculate severity based on deviation
   ├─> Store weather snapshot
   └─> Persist to DB

4. Notification Service
   ├─> Format message
   └─> Send via channels in parallel:
       ├─> Email (SendGrid)
       ├─> SMS (Twilio)
       └─> Webhook (HTTP POST)
```

---

## Troubleshooting

### "psycopg2: connection failed"

```bash
# Check PostgreSQL running
psql --version

# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql # Linux

# Verify connection
psql -U weatherops_dev -d weatherops_local -c "SELECT 1;"
```

### "redis.exceptions.ConnectionError"

```bash
# Check Redis running
redis-cli ping

# Start Redis
brew services start redis       # macOS
sudo systemctl start redis-server # Linux
redis-server                    # Or run directly

# Verify
redis-cli PING  # Should return: PONG
```

### "ModuleNotFoundError: No module named 'app'"

```bash
# Ensure venv is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
make install
```

### "Celery worker not receiving tasks"

```bash
# 1. Kill all celery processes
pkill -f celery

# 2. Clear Redis queue
redis-cli FLUSHDB

# 3. Restart worker
make start-worker
```

### "Database does not exist"

```bash
# Recreate database
make db-create
make migrate
```

### "Stale database locks"

```bash
# Terminate all connections
psql -U weatherops_dev -d weatherops_local \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
      WHERE datname='weatherops_local';"

# Reset database
make db-reset
```

### Logs not showing?

```bash
# Set log level in .env
LOG_LEVEL=DEBUG

# Or directly in code:
# In worker terminal, use:
celery -A app.workers.celery_app worker --loglevel=debug -c 1
```

---

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENVIRONMENT` | `development` | App environment (dev/staging/prod) |
| `DEBUG` | `False` | Enable debug mode |
| `DATABASE_URL` | Local Postgres | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis cache/broker |
| `SECRET_KEY` | — | JWT signing key (generate new!) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT expiration |
| `CELERY_TIMEZONE` | `UTC` | Task scheduler timezone |
| `CELERY_TASK_TIME_LIMIT` | `1800` | Max task runtime (seconds) |
| `WEATHERAI_API_KEY` | — | WeatherAI API key |
| `SENDGRID_API_KEY` | — | SendGrid email API key |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG/INFO/WARNING) |

---

## Next Steps

1. ✅ Complete setup above
2. ✅ Start all services (API, Worker, Beat, Redis)
3. ✅ Visit http://localhost:8000/docs
4. ✅ Create test user via `/api/v1/auth/register`
5. ✅ Create location via `/api/v1/locations`
6. ✅ Create rule via `/api/v1/rules`
7. ✅ Monitor alerts being created in database
8. ✅ Check Celery logs for scheduled task execution
9. ✅ Test notifications (if keys configured)

---

## Useful Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Celery Docs](https://docs.celeryproject.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Redis Docs](https://redis.io/documentation)
- [Pydantic Docs](https://docs.pydantic.dev/)

---

## Quick Reference: Make Commands

```bash
make help              # Show all commands
make install           # Install dependencies
make dev               # Show instructions to start all services
make start-api         # Start FastAPI (port 8000)
make start-worker      # Start Celery worker
make start-beat        # Start Celery beat scheduler
make start-redis       # Start Redis server
make migrate           # Run database migrations
make db-create         # Create database and user
make db-reset          # Reset database (delete all data)
make test              # Run tests
make test-coverage     # Run tests with coverage
make lint              # Run linting checks
make format            # Format code (black + isort)
make type-check        # Run type checking
make clean             # Remove venv and cache
```

