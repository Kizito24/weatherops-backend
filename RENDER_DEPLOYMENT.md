# WeatherOps Backend - Render Deployment Guide

This guide walks through deploying the WeatherOps backend to Render with PostgreSQL, Redis, and Celery.

## Prerequisites

- Render account: https://render.com
- Git repository with all changes pushed to GitHub
- GitHub account connected to Render

## Deployment Steps

### 1. Create Render Account & Connect GitHub

1. Go to https://render.com and create an account
2. Connect your GitHub account in dashboard settings
3. Grant Render access to your repositories

### 2. Create New Web Service

1. Click "New +" → "Web Service"
2. Select your GitHub repository
3. Configure:
   - **Name**: `weatherops-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements/base.txt`
   - **Start Command**: `sh -c 'alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT'`
   - **Plan**: Starter (or higher as needed)

### 3. Add PostgreSQL Database

1. Click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `weatherops-postgres`
   - **Plan**: Starter (or higher)
3. Note the connection string provided

### 4. Add Redis

1. Click "New +" → "Redis"
2. Configure:
   - **Name**: `weatherops-redis`
   - **Plan**: Starter (or higher)
3. Note the connection URL provided

### 5. Configure Environment Variables

In your web service settings, go to "Environment" and add:

```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generate-new-secure-key>
DATABASE_URL=<from-PostgreSQL-service>
REDIS_URL=<from-Redis-service>
CELERY_BROKER_URL=<leave-empty-uses-REDIS_URL>
CELERY_RESULT_BACKEND=<leave-empty-uses-REDIS_URL>
WEATHERAI_API_KEY=<your-key>
SENDGRID_API_KEY=<your-key>
TWILIO_ACCOUNT_SID=<your-sid>
TWILIO_AUTH_TOKEN=<your-token>
TWILIO_PHONE_NUMBER=<your-number>
```

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Link Services Together

**Link PostgreSQL to Web Service:**
1. Go to web service settings → "Environment"
2. In "DATABASE_URL" field, click the database icon
3. Select `weatherops-postgres` → `Database URL`

**Link Redis to Web Service:**
1. In "REDIS_URL" field, click the database icon
2. Select `weatherops-redis` → `Redis URL`

The connection strings will auto-populate and update automatically.

### 7. Deploy

1. Click "Deploy"
2. Render will automatically build and deploy your app
3. Check the deploy logs in the dashboard

### 8. Verify Deployment

Once deployed, test your app:

```bash
# Get your service URL from Render dashboard
curl https://your-service.onrender.com/api/v1/health
```

## Celery Workers & Scheduler (Optional)

For async tasks, deploy Celery worker and beat scheduler as separate background services:

### Option A: Use Render Cron Jobs

For scheduled tasks, create cron jobs in Render:

1. Click "New +" → "Cron Job"
2. Configure:
   - **Name**: `weatherops-beat`
   - **Schedule**: `*/5 * * * *` (every 5 minutes for example)
   - **Command**: `celery -A app.workers.celery_app beat --loglevel=info`

### Option B: Deploy as Background Workers

For dedicated workers (if you have many async tasks):

1. Click "New +" → "Background Worker"
2. Configure:
   - **Name**: `weatherops-worker`
   - **Build Command**: `pip install -r requirements/base.txt`
   - **Start Command**: `celery -A app.workers.celery_app worker --loglevel=info`
   - **Plan**: Starter

3. Link the same DATABASE_URL and REDIS_URL as the web service

## Environment Variables Reference

| Variable | Source | Example |
|----------|--------|---------|
| `DATABASE_URL` | Auto (PostgreSQL) | `postgresql://user:pass@host:5432/weatherops` |
| `REDIS_URL` | Auto (Redis) | `redis://:password@host:6379` |
| `SECRET_KEY` | Manual | Generated using `secrets.token_urlsafe(32)` |
| `ENVIRONMENT` | Manual | `production` |
| `WEATHERAI_API_KEY` | Manual | Your WeatherAI API key |
| `SENDGRID_API_KEY` | Manual | Your SendGrid API key |
| `TWILIO_*` | Manual | Your Twilio credentials |

## Database Migrations

Migrations run automatically on each deploy via the start command:
```
alembic upgrade head && uvicorn app.main:app ...
```

For manual migrations:
1. Go to web service dashboard
2. Click "Shell" tab
3. Run: `alembic upgrade head`

## Monitoring and Logs

View logs in real-time:
1. Go to your service in Render dashboard
2. Click "Logs" tab
3. View real-time output

Search logs:
- Filter by date range
- Search for errors or specific messages
- Export logs if needed

## Troubleshooting

### Service Won't Start

1. Check logs for errors: "Logs" tab in dashboard
2. Verify all required environment variables are set
3. Check database connection: `Database` → test query
4. Check Redis connection: Create cron job to test

### Database Connection Issues

1. Verify `DATABASE_URL` is correctly linked from PostgreSQL service
2. Run manual migration: via Shell tab
3. Check connection string format: `postgresql://user:pass@host:port/db`

### Redis Connection Issues

1. Verify `REDIS_URL` is correctly linked from Redis service
2. Test connection via cron job: `redis-cli PING`
3. Check Celery logs for connection errors

### Migrations Failing

1. Check if database schema is valid
2. Review alembic version table: `SELECT * FROM alembic_version;`
3. Run specific migration: `alembic downgrade <revision>` then `alembic upgrade head`

## Scaling

To increase capacity:

1. Go to service settings
2. Change **Plan** from Starter to Pro or higher
3. Increase **Memory** allocation if needed

## Production Checklist

- [ ] All environment variables configured
- [ ] SECRET_KEY set to secure random value
- [ ] ENVIRONMENT=production, DEBUG=False
- [ ] Database URL linked and verified
- [ ] Redis URL linked and verified
- [ ] All API keys (WeatherAI, SendGrid, Twilio) set
- [ ] Migrations run successfully
- [ ] Health endpoint responds
- [ ] Logs checked for errors
- [ ] Celery workers/beat configured (if using async tasks)
- [ ] Database backups configured (in PostgreSQL service)

## Cost Optimization

- **Starter Plan**: $7/month per service, good for development/small projects
- **Pro Plan**: $12/month, recommended for production
- **Databases**: $7/month per database
- Consider consolidating services to reduce costs

## Support & Documentation

- Render Docs: https://render.com/docs
- PostgreSQL Service: https://render.com/docs/databases
- Redis Service: https://render.com/docs/redis
- Environment Variables: https://render.com/docs/environment-variables
