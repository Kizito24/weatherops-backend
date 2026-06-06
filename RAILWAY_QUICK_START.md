# Railway Deployment - Quick Start

## One-Time Setup

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize Railway project
railway init
# Follow prompts, select "Create a new project" → "weatherops"
```

## Add Services

```bash
# Add PostgreSQL
railway add --name postgres
# Select "PostgreSQL"

# Add Redis
railway add --name redis
# Select "Redis"
```

## Set Environment Variables

```bash
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set variables
railway variables set SECRET_KEY="<generated-key>"
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="False"
railway variables set WEATHERAI_API_KEY="<your-key>"
railway variables set SENDGRID_API_KEY="<your-key>"
railway variables set TWILIO_ACCOUNT_SID="<your-sid>"
railway variables set TWILIO_AUTH_TOKEN="<your-token>"
railway variables set TWILIO_PHONE_NUMBER="<your-number>"
```

## Deploy

```bash
# Run migrations once
railway run alembic upgrade head

# Deploy web service
railway up
```

## View Logs

```bash
# Real-time logs
railway logs -f

# Specific service logs
railway logs --service web -f
```

## Local Testing (Railway-like setup)

```bash
# Start all services locally (PostgreSQL, Redis, web, workers)
docker-compose -f docker-compose.railway.yml up -d

# Stop services
docker-compose -f docker-compose.railway.yml down

# View logs
docker-compose -f docker-compose.railway.yml logs -f web
docker-compose -f docker-compose.railway.yml logs -f celery-worker
```

## Celery Workers & Beat Scheduler

For async tasks and scheduled jobs, deploy as separate services:

1. **Web Service** (automatic) - Runs the FastAPI app
2. **Worker Service** - Runs: `celery -A app.workers.celery_app worker --loglevel=info`
3. **Beat Service** - Runs: `celery -A app.workers.celery_app beat --loglevel=info`

To add these in Railway:
1. Go to Railway dashboard
2. For each service: Create new → Dockerfile
3. Set the appropriate start command above
4. Connect to same PostgreSQL and Redis services

## Monitoring

- **Logs**: `railway logs -f`
- **Health**: Visit `/api/v1/health` endpoint
- **Database**: `railway run psql -U weatherops -d weatherops`
- **Redis**: `railway run redis-cli -u $REDIS_URL`

## Scaling

In Railway dashboard:
1. Select service
2. Adjust CPU/Memory
3. Increase replicas for horizontal scaling

## Production Checklist

- [ ] SECRET_KEY set to secure value
- [ ] ENVIRONMENT=production
- [ ] DEBUG=False
- [ ] All API keys configured
- [ ] Database migrations run
- [ ] Health endpoint working
- [ ] Logs monitored for errors
