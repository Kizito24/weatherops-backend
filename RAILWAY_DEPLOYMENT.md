# WeatherOps Backend - Railway Deployment Guide

This guide walks through deploying the WeatherOps backend to Railway with PostgreSQL, Redis, and Celery.

## Prerequisites

- Railway account: https://railway.app
- Railway CLI installed: `npm i -g @railway/cli`
- Git repository initialized (already done)

## Deployment Steps

### 1. Create Railway Project

```bash
# Login to Railway
railway login

# Create new project
railway init
```

When prompted:
- Choose "Create a new project"
- Name it: `weatherops`

### 2. Add Services

Add PostgreSQL database:
```bash
railway add --name postgres
# Select "PostgreSQL"
```

Add Redis:
```bash
railway add --name redis
# Select "Redis"
```

### 3. Configure Environment Variables

Railway automatically provides:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

You need to set these in the Railway dashboard:

```bash
railway variables set SECRET_KEY="<generate-with-python-below>"
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="False"
railway variables set WEATHERAI_API_KEY="<your-key>"
railway variables set SENDGRID_API_KEY="<your-key>"
railway variables set TWILIO_ACCOUNT_SID="<your-sid>"
railway variables set TWILIO_AUTH_TOKEN="<your-token>"
railway variables set TWILIO_PHONE_NUMBER="<your-number>"
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Database Migrations

Railway provides a one-off deployment command:

```bash
railway run alembic upgrade head
```

This will run migrations against your production database.

### 5. Deploy Web Server

The web service is automatically configured in `railway.json` to use:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Deploy with:
```bash
railway up
```

### 6. Deploy Celery Worker (Optional - separate services)

If you want separate Celery worker and beat scheduler services, create them as additional services:

**Option A: Using Railway Deployments UI**
1. Go to Railway dashboard
2. Create new service with Dockerfile
3. Set start command: `celery -A app.workers.celery_app worker --loglevel=info`

**Option B: Using Railway CLI**
```bash
# Create worker service
railway service add celery-worker

# Create beat service
railway service add celery-beat
```

Then configure their start commands in the dashboard.

### 7. Verify Deployment

After deployment, verify your app is running:

```bash
# Check logs
railway logs

# Get your app URL
railway open
```

Test the health endpoint:
```bash
curl https://your-app.railway.app/api/v1/health
```

## Environment Variables Reference

| Variable | Source | Example |
|----------|--------|---------|
| `DATABASE_URL` | Auto (PostgreSQL) | `postgresql+asyncpg://user:pass@host:5432/railway` |
| `REDIS_URL` | Auto (Redis) | `redis://:password@host:6379/0` |
| `SECRET_KEY` | Manual | Generated using `secrets.token_urlsafe(32)` |
| `ENVIRONMENT` | Manual | `production` |
| `WEATHERAI_API_KEY` | Manual | Your WeatherAI API key |
| `SENDGRID_API_KEY` | Manual | Your SendGrid API key |
| `TWILIO_*` | Manual | Your Twilio credentials |

## Database Migrations

After deploying the web service, run migrations once:

```bash
railway run alembic upgrade head
```

For future migrations after code changes:
```bash
railway run alembic revision --autogenerate -m "description"
railway run alembic upgrade head
```

## Celery Tasks

With Redis configured, Celery tasks will work automatically:
- Tasks are stored in Redis (broker)
- Results are stored in Redis (backend)
- Worker processes execute tasks

To run the worker locally for testing:
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

To run beat scheduler locally:
```bash
celery -A app.workers.celery_app beat --loglevel=info
```

## Monitoring and Logs

View real-time logs:
```bash
railway logs -f
```

View specific service logs:
```bash
railway logs --service web -f
railway logs --service celery-worker -f
```

## Scaling

To scale your services in Railway:
1. Go to Railway dashboard
2. Select your service
3. Adjust CPU and memory allocations
4. Increase replica count for horizontal scaling

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running in Railway
- Run `railway run python -c "from app.database import engine; print('Connected!')"`

### Redis Connection Issues
- Verify `REDIS_URL` is set correctly
- Check Redis service is running in Railway
- Test with: `railway run redis-cli -u $REDIS_URL ping`

### Celery Not Processing Tasks
- Ensure Redis is running
- Check worker logs: `railway logs --service celery-worker -f`
- Verify `CELERY_BROKER_URL` is using Redis URL

### File Upload Issues
- Railway uses ephemeral storage
- Use external storage (S3, etc.) for persistent files

## Production Checklist

- [ ] Set `SECRET_KEY` to a secure random value
- [ ] Set `ENVIRONMENT` to `production`
- [ ] Set `DEBUG` to `False`
- [ ] Configure all required API keys (WeatherAI, SendGrid, Twilio)
- [ ] Run database migrations: `railway run alembic upgrade head`
- [ ] Test health endpoint
- [ ] Monitor logs for errors
- [ ] Set up error tracking (Sentry recommended)
- [ ] Configure backup strategy for PostgreSQL
