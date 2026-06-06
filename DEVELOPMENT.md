# WeatherOps Development Guide

This guide covers local development setup, contributing to the project, and best practices.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Code Style & Quality](#code-style--quality)
4. [Testing](#testing)
5. [Database Development](#database-development)
6. [Working with Celery](#working-with-celery)
7. [Common Development Tasks](#common-development-tasks)
8. [Debugging](#debugging)
9. [Contributing](#contributing)

## Development Environment Setup

### 1.1 Prerequisites

- Python 3.12+
- PostgreSQL 13+
- Redis 6+
- Git
- Virtual Environment tool (venv or conda)

### 1.2 Clone Repository

```bash
git clone https://github.com/your-org/weatherops-backend.git
cd weatherops-backend
```

### 1.3 Create Virtual Environment

```bash
# Using venv
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n weatherops python=3.12
conda activate weatherops
```

### 1.4 Install Dependencies

```bash
# Install base dependencies
pip install -r requirements/base.txt

# Install development dependencies
pip install -r requirements/dev.txt  # If exists
# Or manually:
pip install black ruff mypy pytest pytest-asyncio pytest-cov
```

### 1.5 Setup Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit with your values
nano .env
```

Example `.env`:
```
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/weatherops_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_ACCEPT_CONTENT=json

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External APIs
WEATHER_API_KEY=your_weatherai_api_key
SENDGRID_API_KEY=your_sendgrid_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token

# Development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 1.6 Start Services

#### Option A: Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Verify services
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option B: Manual Services

```bash
# Terminal 1: PostgreSQL
pg_ctl -D /usr/local/var/postgres start
# Or: brew services start postgresql

# Terminal 2: Redis
redis-server

# Terminal 3: Continue with setup
```

### 1.7 Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify schema created
psql weatherops_dev -c "\dt"
```

### 1.8 Start Development Server

```bash
# Terminal 1: FastAPI server (auto-reload)
uvicorn app.main:app --reload --port 8000

# Terminal 2: Celery worker
celery -A app.workers.celery_app worker --loglevel=debug

# Terminal 3: Celery Beat scheduler
celery -A app.workers.celery_app beat --loglevel=debug
```

### 1.9 Verify Installation

```bash
# Check API
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok"
  }
}

# Access API docs
open http://localhost:8000/docs
```

## Project Structure

```
weatherops-backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py          # Configuration & settings
│   │   ├── constants.py        # Constants
│   │   ├── security.py         # JWT & auth utilities
│   │   └── exceptions.py       # Custom exceptions
│   ├── database/
│   │   ├── session.py          # SQLAlchemy setup
│   │   ├── models.py           # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py         # Auth endpoints
│   │   │   ├── locations.py    # Location endpoints
│   │   │   ├── weather.py      # Weather endpoints
│   │   │   ├── alerts.py       # Alert endpoints
│   │   │   ├── rules.py        # Rule endpoints
│   │   │   └── health.py       # Health endpoint
│   │   └── dependencies.py     # Dependency injection
│   ├── services/
│   │   ├── auth.py             # Authentication logic
│   │   ├── weather.py          # Weather service
│   │   ├── rule_engine.py      # Rule evaluation
│   │   ├── notification.py     # Notifications
│   │   └── user.py             # User operations
│   ├── workers/
│   │   ├── celery_app.py       # Celery setup
│   │   ├── tasks.py            # Task definitions
│   │   └── beat_schedule.py    # Beat scheduler
│   └── middleware/
│       ├── error_handler.py    # Error handling
│       ├── logging.py          # Logging
│       └── cors.py             # CORS setup
├── alembic/
│   ├── versions/               # Migration files
│   ├── env.py                  # Migration config
│   └── script.py.mako          # Migration template
├── tests/
│   ├── conftest.py             # Pytest configuration
│   ├── test_auth.py            # Auth tests
│   ├── test_locations.py       # Location tests
│   ├── test_weather.py         # Weather tests
│   ├── test_alerts.py          # Alert tests
│   ├── test_rules.py           # Rule tests
│   └── test_integration.py     # Integration tests
├── requirements/
│   ├── base.txt                # Base dependencies
│   ├── dev.txt                 # Development dependencies
│   └── prod.txt                # Production dependencies
├── docker/
│   ├── Dockerfile              # Production image
│   ├── Dockerfile.dev          # Development image
│   └── docker-compose.yml      # Compose config
├── .env.example                # Example env file
├── .gitignore                  # Git ignore rules
├── render.yaml                 # Render deployment config
├── start.sh                    # Production start script
├── build.sh                    # Production build script
├── run_migrations.py           # Migration runner
└── README.md                   # Project README
```

## Code Style & Quality

### 1. Formatting with Black

```bash
# Format all code
black app/ tests/

# Format specific file
black app/main.py

# Check without modifying
black --check app/
```

### 2. Linting with Ruff

```bash
# Check for issues
ruff check app/ tests/

# Fix auto-fixable issues
ruff check --fix app/

# Specific rule check
ruff check --select=E501 app/  # Line too long
```

### 3. Type Checking with MyPy

```bash
# Full type check
mypy app/

# Specific file
mypy app/services/weather.py

# Ignore missing imports
mypy app/ --ignore-missing-imports
```

### 4. Pre-commit Hooks

Setup automatic checks before commit:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.12
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.1
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### 5. Code Quality Checklist

Before committing:
- [ ] Code formatted with Black
- [ ] No linting errors (Ruff)
- [ ] Type hints added
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No hardcoded secrets

## Testing

### 1. Project Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_auth.py             # Auth endpoint tests
├── test_locations.py        # Location tests
├── test_weather.py          # Weather service tests
├── test_rules.py            # Rule engine tests
├── test_alerts.py           # Alert tests
└── test_integration.py      # End-to-end tests
```

### 2. Writing Tests

Example test:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_register_user

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto
```

### 4. Test Configuration (conftest.py)

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_user(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    return response.json()
```

### 5. Coverage Report

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

## Database Development

### 1. Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user_preferences table"

# Manual migration
alembic revision -m "Custom migration"
```

### 2. Migration File

```python
# alembic/versions/001_create_users.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
```

### 3. Run Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade +1

# Downgrade one step
alembic downgrade -1

# Check current version
alembic current

# Check history
alembic history
```

### 4. Database Inspection

```bash
# Connect to dev database
psql weatherops_dev

# List tables
\dt

# Describe table
\d users

# List indexes
\di

# Run query
SELECT * FROM users LIMIT 10;
```

### 5. Database Seeding

```bash
# Create seed script
cat > scripts/seed_dev_data.py << 'EOF'
import asyncio
from app.database.session import AsyncSessionLocal
from app.models import User
from app.core.security import get_password_hash

async def seed():
    async with AsyncSessionLocal() as session:
        # Create test user
        user = User(
            email="dev@example.com",
            hashed_password=get_password_hash("devpass123"),
            is_active=True
        )
        session.add(user)
        await session.commit()
        print("✓ Seeded development data")

if __name__ == "__main__":
    asyncio.run(seed())
EOF

# Run seed
python scripts/seed_dev_data.py
```

## Working with Celery

### 1. Define Tasks

```python
# app/workers/tasks.py
from celery import shared_task
from app.services.weather import WeatherService

@shared_task
def check_weather_for_location(location_id: str):
    """Check weather and trigger alerts"""
    service = WeatherService()
    return service.check_and_alert(location_id)

@shared_task
def send_email_notification(user_id: str, subject: str, body: str):
    """Send email to user"""
    from app.services.notification import NotificationService
    service = NotificationService()
    return service.send_email(user_id, subject, body)
```

### 2. Schedule Tasks

```python
# app/workers/beat_schedule.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-weather-every-5-minutes': {
        'task': 'app.workers.tasks.check_weather_for_location',
        'schedule': 300.0,  # 5 minutes
        'args': ('location-id',)
    },
    'cleanup-old-alerts-daily': {
        'task': 'app.workers.tasks.cleanup_old_alerts',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    }
}
```

### 3. Monitor Tasks

```bash
# Use Flower for monitoring
pip install flower
celery -A app.workers.celery_app flower

# Access at http://localhost:5555
```

### 4. Debug Tasks

```bash
# Enable debug logging
celery -A app.workers.celery_app worker --loglevel=debug

# Test task execution
python -c "
from app.workers.tasks import check_weather_for_location
result = check_weather_for_location.apply_async(
    args=['location-id'],
    countdown=5  # Run after 5 seconds
)
print(f'Task ID: {result.id}')
"
```

## Common Development Tasks

### 1. Add New API Endpoint

```python
# app/api/v1/example.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/examples", tags=["examples"])

@router.get("/")
async def list_examples(
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    # Implementation
    return []

@router.post("/")
async def create_example(
    data: ExampleSchema,
    current_user = Depends(get_current_user)
):
    # Implementation
    return {"id": "...", **data.dict()}

# Add to app/main.py
from app.api.v1 import example
app.include_router(example.router)
```

### 2. Add New Database Model

```python
# app/database/models.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.database.base import Base

class Example(Base):
    __tablename__ = "examples"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create migration
alembic revision --autogenerate -m "Add example table"
alembic upgrade head
```

### 3. Add New Service

```python
# app/services/example.py
class ExampleService:
    async def get_example(self, example_id: str):
        # Implementation
        pass
    
    async def create_example(self, data: dict):
        # Implementation
        pass

# Use in endpoint
from app.services.example import ExampleService

service = ExampleService()
result = await service.get_example("id")
```

### 4. Update Dependencies

```bash
# Add new package
pip install new-package
pip freeze > requirements/base.txt

# Or use pip-tools
pip install pip-tools
echo "fastapi==0.115.0" > requirements/base.in
pip-compile requirements/base.in
```

## Debugging

### 1. Using Print Statements

```python
# Add debug prints
print(f"DEBUG: user_id={user_id}, location_id={location_id}")

# Run with logs
uvicorn app.main:app --reload --log-level debug
```

### 2. Using Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use breakpoint() (Python 3.7+)
breakpoint()

# In debugger:
# l (list)
# n (next)
# s (step)
# c (continue)
# p variable_name (print)
```

### 3. Using VS Code Debugger

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.main:app", "--reload", "--port", "8000"],
            "jinja": true,
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

### 4. Database Query Logging

Enable SQLAlchemy logging:

```python
# app/core/config.py
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 5. Request/Response Logging

```python
# app/middleware/logging.py
import logging
import time
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    process_time = time.time() - start
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s"
    )
    return response
```

## Contributing

### 1. Workflow

1. Create feature branch: `git checkout -b feature/feature-name`
2. Make changes and test locally
3. Format code: `black app/ tests/`
4. Run linter: `ruff check app/`
5. Run tests: `pytest`
6. Commit: `git commit -m "feat: add feature"`
7. Push: `git push origin feature/feature-name`
8. Create Pull Request

### 2. Commit Messages

Follow conventional commits:
```
feat: add weather monitoring
fix: resolve token refresh issue
docs: update API documentation
test: add user registration tests
style: format code with black
refactor: simplify rule evaluation
chore: update dependencies
```

### 3. Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Manual testing performed

## Checklist
- [ ] Code formatted with Black
- [ ] No linting errors
- [ ] Type hints added
- [ ] Documentation updated
- [ ] No hardcoded secrets
```

### 4. Code Review Checklist

Before submitting PR:
- [ ] Code follows project style
- [ ] All tests pass
- [ ] No console warnings
- [ ] Comments added for complex logic
- [ ] Commit messages are clear
- [ ] No unrelated changes

### 5. Documentation Updates

Update relevant docs:
- `README.md` - Overview changes
- `API.md` - New endpoints
- `ARCHITECTURE.md` - Design changes
- `DEVELOPMENT.md` - Dev process changes

## IDE Setup

### VS Code Extensions

```
ms-python.python
ms-python.vscode-pylance
charliermarsh.ruff
ms-python.debugpy
httpyac.httpyac
```

### PyCharm Configuration

1. Settings → Python → Project → Python Interpreter
2. Add local venv
3. Settings → Tools → Python Integrated Tools
4. Set Default test runner to pytest
5. Configure code formatter to Black

## Performance Profiling

### Profile FastAPI Endpoints

```bash
pip install pyinstrument

# Add profiler middleware
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

# ... run code ...

profiler.stop()
print(profiler.output_text(unicode=True, color=True))
```

### Memory Profiling

```bash
pip install memory-profiler

# Profile function
from memory_profiler import profile

@profile
async def my_function():
    pass

# Run: python -m memory_profiler script.py
```

## Useful Commands

```bash
# Check Python version
python --version

# Show venv location
which python

# List installed packages
pip list

# Check for outdated packages
pip list --outdated

# Generate requirements
pip freeze > requirements/base.txt

# Install from requirements
pip install -r requirements/base.txt

# Clear cache
pip cache purge
```

## Additional Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python 3.12 Release](https://www.python.org/downloads/release/python-3120/)

---

Happy coding! 🚀
