# WeatherOps Backend - Local Development Setup

Complete guide for setting up and running WeatherOps locally for development.

## Prerequisites

Before you start, ensure you have installed:

- **Python 3.12+** — [Download](https://www.python.org/downloads/)
- **PostgreSQL 14+** — [Download](https://www.postgresql.org/download/)
- **Redis 7+** — [Download](https://redis.io/download)
- **Git** — [Download](https://git-scm.com/downloads)

### macOS Installation (Homebrew)

```bash
brew install python@3.12 postgresql redis
```

### Ubuntu/Debian Installation

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip postgresql postgresql-contrib redis-server
```

### Windows Installation

Use Homebrew (via WSL2) or download installers from official sites. Redis: [Windows version](https://github.com/microsoftarchive/redis/releases)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Kizito24/weatherops-backend.git
cd weatherops-backend
```

### 2. Create Virtual Environment

```bash
python3.12 -m venv venv

# Activate venv
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements/base.txt
pip install -r requirements/dev.txt  # For development tools
```

### 4. Setup Local Database

#### Start PostgreSQL

**macOS:**
```bash
brew services start postgresql
```

**Linux:**
```bash
sudo systemctl start postgresql
```

**Windows (WSL2):**
```bash
sudo service postgresql start
```

#### Create Database & User

```bash
createuser -P weatherops_dev
# Enter password: weatherops_dev (or your preference)

createdb -U weatherops_dev weatherops_local
```

Verify connection:
```bash
psql -U weatherops_dev -d weatherops_local -c "SELECT 1;"
```

### 5. Setup Local Redis

#### Start Redis

**macOS:**
```bash
brew services start redis
```

**Linux:**
```bash
sudo systemctl start redis-server
```

**Windows (WSL2):**
```bash
sudo service redis-server start
```

**Or run in a separate terminal:**
```bash
redis-server
```

Verify connection:
```bash
redis-cli ping
# Should return: PONG
```

### 6. Create .env File

Copy `.env.render` and customize for local development:

```bash
cp .env.render .env
```

Edit `.env` with local values:

```bash
# APPLICATION
APP_NAME=WeatherOps
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000
RELOAD=True

# DATABASE - Local PostgreSQL
DATABASE_URL=postgresql://weatherops_dev:weatherops_dev@localhost:5432/weatherops_local
DATABASE_ECHO=True
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=0
DATABASE_POOL_PRE_PING=True

# REDIS - Local Redis
REDIS_URL=redis://localhost:6379/0
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_SOCKET_KEEPALIVE=True

# CELERY
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
CELERY_ACCEPT_CONTENT=json
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC
CELERY_TASK_TRACK_STARTED=True
CELERY_TASK_TIME_LIMIT=3600

# SECURITY - Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-local-dev-key-here
JWT_SECRET_KEY=your-local-jwt-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# EXTERNAL APIS
WEATHERAI_API_KEY=your-key-here
SENDGRID_API_KEY=your-key-here
TWILIO_ACCOUNT_SID=your-key-here
TWILIO_AUTH_TOKEN=your-key-here
TWILIO_PHONE_NUMBER=+1234567890

# LOGGING
LOG_LEVEL=DEBUG
LOG_FORMAT=json
```

### 7. Run Migrations

```bash
python run_migrations.py
```

You should see output like:
```
Running migrations...
Migrations completed successfully
```

### 8. Start Development Services

Open 4 terminal windows:

#### Terminal 1: FastAPI Server
```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Terminal 2: Celery Worker
```bash
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

Expected output:
```
[INFO/MainProcess] celery@hostname ready.
[INFO/MainProcess] mingle: searching for neighbors
```

#### Terminal 3: Celery Beat (Scheduler)
```bash
source venv/bin/activate
celery -A app.workers.celery_app beat --loglevel=info
```

Expected output:
```
[INFO/MainProcess] celery beat v5.x.x is starting.
[INFO/MainProcess] LocalTime -> 2024-06-06 14:30:00
```

#### Terminal 4: Redis (if not running as service)
```bash
redis-server
```

## Development Workflow

### Access the Application

- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Common Development Tasks

#### Create a Database Migration

```bash
# 1. Modify models in app/models/
# 2. Generate migration
alembic revision --autogenerate -m "Add new column"

# 3. Review migration in alembic/versions/
# 4. Apply migration
alembic upgrade head
```

#### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_services.py

# With coverage report
pytest --cov=app

# Verbose output
pytest -v
```

#### Run Linting & Formatting

```bash
# Type checking
mypy app

# Linting
flake8 app

# Format code
black app
isort app
```

#### Create a User (for testing)

```bash
# Via Python shell
python

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
import uuid
import asyncio

async def create_user():
    async with AsyncSessionLocal() as db:
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        await db.commit()
        print(f"Created user: {user.email}")

asyncio.run(create_user())
```

#### View Celery Tasks in Real-time

Use Flower (web UI for Celery):

```bash
celery -A app.workers.celery_app flower --port=5555
```

Then visit: http://localhost:5555

### Database Management

#### Reset Database (Dev Only)

```bash
# Drop all tables
alembic downgrade base

# Re-run migrations
alembic upgrade head
```

#### View Database Contents

```bash
psql -U weatherops_dev -d weatherops_local

# List tables
\dt

# View alerts table
SELECT * FROM alerts LIMIT 10;

# Exit
\q
```

#### Check Database Connection

```bash
psql -U weatherops_dev -d weatherops_local -c "SELECT version();"
```

### Debugging Tips

#### Enable Detailed Logging

In `.env`:
```bash
LOG_LEVEL=DEBUG
SQLALCHEMY_ECHO=True
```

#### Debug Celery Tasks

```bash
# Terminal 2, run worker with debug logs
celery -A app.workers.celery_app worker --loglevel=debug -c 1
```

The `-c 1` flag runs with 1 worker process (easier to debug).

#### Check Redis Queue

```bash
redis-cli

# List all keys
keys *

# Check task queue
llen celery

# View task details
get <key>

# Exit
exit
```

#### Test External APIs Locally

```bash
# Test WeatherAI API
curl -X GET "http://localhost:8000/health"

# Create test location (requires auth)
curl -X POST "http://localhost:8000/locations" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Location", "latitude": 40.7128, "longitude": -74.0060}'
```

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENVIRONMENT` | `development` | App environment |
| `DEBUG` | `True` | Enable debug mode |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |
| `DATABASE_URL` | Local Postgres | Database connection |
| `REDIS_URL` | `redis://localhost` | Redis broker |
| `CELERY_TIMEZONE` | `UTC` | Celery timezone |
| `WEATHERAI_API_KEY` | — | Weather API key |
| `SENDGRID_API_KEY` | — | Email service key |

## Troubleshooting

### Issue: "psycopg2: connection failed"

**Solution:**
```bash
# Check PostgreSQL is running
psql -U weatherops_dev -d weatherops_local -c "SELECT 1;"

# If not running, start it
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
```

### Issue: "redis.exceptions.ConnectionError"

**Solution:**
```bash
# Check Redis is running
redis-cli ping

# If not running, start it
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux
redis-server  # Or run directly
```

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements/base.txt
```

### Issue: "Database 'weatherops_local' does not exist"

**Solution:**
```bash
createdb -U weatherops_dev weatherops_local
python run_migrations.py
```

### Issue: Celery worker not picking up tasks

**Solution:**
```bash
# 1. Kill all celery processes
pkill -f celery

# 2. Restart worker
celery -A app.workers.celery_app worker --loglevel=info

# 3. Check Redis connection
redis-cli ping
```

### Issue: Stale database locks

**Solution:**
```bash
# Cancel active connections
psql -U weatherops_dev -d weatherops_local -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='weatherops_local';"

# Then reset
alembic downgrade base
alembic upgrade head
```

## Project Structure

```
weatherops-backend/
├── app/
│   ├── api/                 # API endpoints
│   ├── core/               # Configuration, security, logging
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── repositories/       # Data access
│   ├── workers/            # Celery tasks
│   ├── database/           # Database setup
│   └── main.py             # FastAPI app factory
├── tests/                  # Test suite
├── alembic/                # Database migrations
├── requirements/           # Dependency files
├── .env                    # Local environment (create from .env.render)
├── render.yaml             # Render deployment config
└── LOCAL_DEVELOPMENT.md    # This file
```

## Next Steps

1. ✅ Complete setup above
2. ✅ Start all 4 services (API, Worker, Beat, Redis)
3. ✅ Visit http://localhost:8000/docs
4. ✅ Create a test account and location
5. ✅ Create a weather rule
6. ✅ Monitor Celery Beat scheduler and Worker
7. ✅ Watch alerts get created every 5 minutes
8. ✅ Test notification channels (email, SMS, webhook)

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

## Getting Help

If you encounter issues:

1. Check logs in each terminal window
2. Review troubleshooting section above
3. Check environment variables match `.env`
4. Verify all services are running (Redis, PostgreSQL, API, Worker, Beat)
5. Open an issue with detailed error logs

