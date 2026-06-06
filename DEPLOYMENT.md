# WeatherOps Deployment Guide

## Production Deployment on Render

This guide covers deploying WeatherOps Backend to Render with PostgreSQL, Redis, and Celery workers.

## Architecture Overview

```
┌─────────────────┐
│  Web Clients    │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────────────────────┐
│              RENDER PLATFORM                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌────────────────────┐                       │
│  │  Web Service       │                       │
│  │  (FastAPI/Uvicorn)│                       │
│  │  Port: 8000        │                       │
│  └────┬───────────────┘                       │
│       │                                        │
│  ┌────┴────┬────────────────────────┐         │
│  │          │                        │         │
│  ▼          ▼                        ▼         │
│ PostgreSQL Redis            Celery Worker     │
│ (Database) (Cache/Queue)    & Beat Scheduler │
│  Port:      Port:                             │
│  5432       6379                              │
│                                              │
└─────────────────────────────────────────────────┘
         │              │
         ▼              ▼
    External APIs   Notification Services
    (WeatherAI,    (SendGrid, Twilio)
     etc)
```

## Prerequisites

- Render account with credit card
- GitHub/GitLab account with repository
- Environment variables configured
- Docker knowledge (optional, but recommended)

## Step 1: Prepare Repository

### 1.1 Create/Update render.yaml

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: weatherops-backend
    runtime: python
    pythonVersion: 3.12
    buildCommand: bash build.sh
    startCommand: bash start.sh
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: weatherops_postgres
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: weatherops_redis
          type: redis
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          name: weatherops_redis
          type: redis
          property: connectionString
      - key: CELERY_RESULT_BACKEND
        fromService:
          name: weatherops_redis
          type: redis
          property: connectionString
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: JWT_ALGORITHM
        value: HS256
      - key: JWT_EXPIRATION_HOURS
        value: '24'
      - key: WEATHER_API_KEY
        sync: false
      - key: SENDGRID_API_KEY
        sync: false
      - key: TWILIO_ACCOUNT_SID
        sync: false
      - key: TWILIO_AUTH_TOKEN
        sync: false

  - type: pserv
    name: weatherops_postgres
    ipAllowList: []
    postgresVersion: 15

  - type: redis
    name: weatherops_redis
    ipAllowList: []
```

### 1.2 Create build.sh

```bash
#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements/base.txt

echo "Build completed successfully!"
```

### 1.3 Create start.sh

```bash
#!/bin/bash
set -e

echo "Starting WeatherOps backend..."

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head || {
    echo "Warning: Migration failed, attempting fallback..."
    python run_migrations.py || true
}

# Start Uvicorn
echo "Starting API server on port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 1.4 Create run_migrations.py

```python
#!/usr/bin/env python
import subprocess
import sys

def run_migrations():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("[Alembic] ✓ Migrations completed successfully")
            return True
        else:
            print(f"[Alembic] Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("[Alembic] Timeout: Migration took too long")
        return False
    except Exception as e:
        print(f"[Alembic] Exception: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
```

### 1.5 Verify Dockerfile

Dockerfile should include:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Copy application
COPY . .

# Run migrations and start app
CMD ["bash", "start.sh"]
```

## Step 2: Create Services on Render

### 2.1 Create PostgreSQL Service

1. Go to Render Dashboard: https://dashboard.render.com
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: weatherops_postgres
   - **Database**: weatherops_postgres
   - **User**: (auto-generated)
   - **Region**: Choose closest to you
   - **Instance Type**: Standard (Starter for testing)
4. Create Database
5. Note the **Internal Database URL** and **External Database URL**

### 2.2 Create Redis Service

1. Click "New +" → "Redis"
2. Configure:
   - **Name**: weatherops_redis
   - **Region**: Same as PostgreSQL
   - **Instance Type**: Standard (Starter for testing)
3. Create Redis
4. Note the **Redis URL**

### 2.3 Create Web Service

1. Click "New +" → "Web Service"
2. Connect GitHub/GitLab repository
3. Configure:
   - **Name**: weatherops-backend
   - **Runtime**: Python
   - **Build Command**: `bash build.sh`
   - **Start Command**: `bash start.sh`
   - **Instance Type**: Standard (Starter)
   - **Auto-deploy**: Yes
   - **Region**: Same as other services
4. Add environment variables (see below)
5. Create Web Service

### 2.4 Add Environment Variables

In Web Service settings, add:

| Key | Value | Source |
|-----|-------|--------|
| ENVIRONMENT | production | Text |
| DATABASE_URL | (from PostgreSQL) | Paste internal URL |
| REDIS_URL | (from Redis) | Paste Redis URL |
| CELERY_BROKER_URL | (same as REDIS_URL) | Text |
| CELERY_RESULT_BACKEND | (same as REDIS_URL) | Text |
| JWT_SECRET_KEY | (generate random) | Text |
| JWT_ALGORITHM | HS256 | Text |
| JWT_EXPIRATION_HOURS | 24 | Text |
| WEATHER_API_KEY | (your API key) | Text |
| SENDGRID_API_KEY | (your API key) | Text |
| TWILIO_ACCOUNT_SID | (your SID) | Text |
| TWILIO_AUTH_TOKEN | (your token) | Text |

## Step 3: Configure Background Workers

### 3.1 Create Celery Worker Service

1. Click "New +" → "Background Worker"
2. Configure:
   - **Name**: weatherops-celery-worker
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements/base.txt`
   - **Start Command**: `celery -A app.workers.celery_app worker --loglevel=info`
   - **Instance Type**: Standard
   - **Region**: Same as others
3. Add same environment variables as Web Service
4. Create Background Worker

### 3.2 Create Celery Beat Service

1. Click "New +" → "Background Worker"
2. Configure:
   - **Name**: weatherops-celery-beat
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements/base.txt`
   - **Start Command**: `celery -A app.workers.celery_app beat --loglevel=info`
   - **Instance Type**: Standard
   - **Region**: Same as others
3. Add same environment variables as Web Service
4. Create Background Worker

## Step 4: Verify Database Configuration

### 4.1 Database URL Format

Render provides two URLs:
- **Internal URL**: For services within Render (use in most cases)
- **External URL**: For external connections (use for local testing)

The app should use the **Internal URL** for better performance and security.

Format:
```
postgresql+asyncpg://user:password@host:5432/database
```

The app automatically converts `postgresql://` to `postgresql+asyncpg://` for async operations.

### 4.2 Test Database Connection

After deployment:

```bash
# SSH into web service
render ssh -s weatherops-backend

# Test database connection
python -c "
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

async def test():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('✓ Database connected')
    await engine.dispose()

asyncio.run(test())
"
```

## Step 5: Initial Deployment

### 5.1 Deploy

Push to repository:
```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

Render automatically deploys when changes are pushed to main.

### 5.2 Monitor Deployment

1. Go to Web Service → Deployments
2. Watch build/deploy logs
3. Service goes live when status is "Live"

### 5.3 Verify Health

```bash
# Check API health
curl https://<your-app>.onrender.com/api/v1/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok"
  }
}
```

## Step 6: Test API Endpoints

### 6.1 Register User

```bash
curl -X POST https://<your-app>.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

### 6.2 Login

```bash
curl -X POST https://<your-app>.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

### 6.3 Create Location

```bash
curl -X POST https://<your-app>.onrender.com/api/v1/locations \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "San Francisco",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "description": "Office location"
  }'
```

## Step 7: Database Migrations

### 7.1 Automatic Migrations

Migrations run automatically via `start.sh` before the app starts.

### 7.2 Manual Migrations

If automatic migration fails:

```bash
# SSH into web service
render ssh -s weatherops-backend

# Run migrations manually
python -m alembic upgrade head

# Or with fallback
python run_migrations.py
```

### 7.3 Create New Migration

For development, create migrations locally:

```bash
# In local development
alembic revision --autogenerate -m "Add new table"
alembic upgrade head

# Commit and push
git add alembic/versions/
git commit -m "Add migration for new table"
git push origin main
```

## Step 8: Monitoring & Logging

### 8.1 View Logs

1. Web Service → Logs tab
2. Real-time log streaming
3. Filter by service, date range

### 8.2 Error Monitoring

Check logs for errors:
```
filter: level >= ERROR
```

### 8.3 Performance Metrics

Render provides:
- CPU usage
- Memory usage
- Disk I/O
- Network I/O

## Step 9: Scaling

### 9.1 Scale Web Service

1. Web Service settings → Instance Type
2. Choose larger instance (Standard → Plus)
3. Renders automatically scales

### 9.2 Scale Database

1. PostgreSQL settings → Instance Type
2. Choose larger instance
3. Handles scaling with minimal downtime

### 9.3 Multiple Celery Workers

Create additional worker services:
1. New +" → "Background Worker"
2. Configure with same settings
3. Celery automatically distributes tasks

## Step 10: Custom Domain

### 10.1 Add Custom Domain

1. Web Service settings → Custom Domain
2. Add your domain
3. Add CNAME record to DNS:
   ```
   CNAME: <service>.onrender.com
   ```

### 10.2 SSL Certificate

Render automatically provisions free SSL certificate.

## Troubleshooting

### Issue: Database Migration Fails

```
Error: relation "users" does not exist
```

**Solution:**
1. Check DATABASE_URL is correct
2. Check PostgreSQL service is running
3. Manually run migrations:
   ```bash
   render ssh -s weatherops-backend
   python run_migrations.py
   ```

### Issue: Redis Connection Error

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solution:**
1. Verify REDIS_URL is correct (use internal URL)
2. Check Redis service is running
3. Verify environment variable is set
4. Restart services

### Issue: Celery Tasks Not Running

**Solution:**
1. Check Celery worker is deployed
2. Verify CELERY_BROKER_URL and CELERY_RESULT_BACKEND
3. Check worker logs for errors
4. Verify Redis is running

### Issue: API Returns 502 Bad Gateway

**Solution:**
1. Check app logs for errors
2. Verify environment variables
3. Ensure database migration completed
4. Restart web service

### Issue: High Memory Usage

**Solution:**
1. Check for memory leaks in application
2. Reduce Celery worker concurrency
3. Increase instance type
4. Enable Redis memory optimization

## Performance Optimization

### 1. Caching

Configure Redis caching:
```python
# app/core/config.py
REDIS_CACHE_TTL = 3600  # 1 hour
CACHE_ENABLED = True
```

### 2. Database Indexing

Ensure indexes are created:
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_rules_location_id ON rules(location_id);
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
```

### 3. Connection Pooling

SQLAlchemy automatically manages connection pool.

### 4. Pagination

Always paginate list endpoints:
```bash
GET /api/v1/locations?skip=0&limit=50
```

## Security Checklist

- [ ] Environment variables configured (no secrets in code)
- [ ] HTTPS/SSL enabled
- [ ] JWT secret key generated
- [ ] Database backups enabled
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Input validation enabled
- [ ] SQL injection prevention (SQLAlchemy ORM)
- [ ] XSS prevention (JSON responses)
- [ ] CSRF protection (if applicable)

## Backup & Recovery

### 1. Database Backups

Render PostgreSQL automatically backs up:
- Daily automated backups
- 7-day retention
- Point-in-time recovery available

### 2. Manual Backup

```bash
# SSH into web service
render ssh -s weatherops-backend

# Backup database
pg_dump $DATABASE_URL > backup.sql
```

### 3. Restore from Backup

Contact Render support or use point-in-time recovery.

## Cost Estimation

| Service | Tier | Cost/Month |
|---------|------|-----------|
| Web Service | Standard | $7 |
| PostgreSQL | Standard | $15 |
| Redis | Standard | $6 |
| Celery Worker | Standard | $7 |
| Celery Beat | Standard | $7 |
| **Total** | | **$42+** |

*(Starter tier is free for testing)*

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Celery Best Practices](https://docs.celeryproject.io/en/stable/userguide/tasks.html)
- [Redis Best Practices](https://redis.io/docs/latest/develop/use/patterns/)

## Support

For deployment issues:
1. Check Render Dashboard logs
2. Review application error logs
3. Verify environment configuration
4. Contact Render support
5. Open GitHub issue with logs
