# Render Deployment - Quick Start

## One-Time Setup

1. **Create Render Account**
   - Go to https://render.com
   - Sign up and verify email

2. **Connect GitHub**
   - In Render dashboard → Settings → GitHub
   - Authorize Render to access your repo

## Create Services

### Web Service
1. Click "New +" → "Web Service"
2. Select your GitHub repo
3. Configure:
   - Name: `weatherops-api`
   - Build: `pip install -r requirements/base.txt`
   - Start: `sh -c 'alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT'`
4. Click "Create Web Service"

### PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. Name: `weatherops-postgres`
3. Plan: Starter
4. Click "Create Database"

### Redis Cache
1. Click "New +" → "Redis"
2. Name: `weatherops-redis`
3. Plan: Starter
4. Click "Create Redis"

## Link Services

### In Web Service Settings → Environment:

**Important:** Use the service linking feature (🔗 icon) to automatically use **Internal URLs** for secure, private communication between Render services.

1. **DATABASE_URL**
   - Click 🔗 icon
   - Select `weatherops-postgres` → `Internal Database URL`
   - ✅ Automatically uses: `postgresql://...@host...` (internal)
   - ❌ Don't use External URL

2. **REDIS_URL**
   - Click 🔗 icon
   - Select `weatherops-redis` → `Internal Redis URL`
   - ✅ Automatically uses: `redis://:password@host...` (internal)
   - ❌ Don't use External URL

## Set Environment Variables

In Web Service → Environment, add:

```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generated-key-below>
CELERY_BROKER_URL=  (empty, uses REDIS_URL)
CELERY_RESULT_BACKEND=  (empty, uses REDIS_URL)
WEATHERAI_API_KEY=<your-key>
SENDGRID_API_KEY=<your-key>
TWILIO_ACCOUNT_SID=<your-sid>
TWILIO_AUTH_TOKEN=<your-token>
TWILIO_PHONE_NUMBER=<your-number>
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deploy

1. Click "Deploy" button
2. Watch deploy logs
3. Once live, test: `curl https://your-service.onrender.com/api/v1/health`

## Monitor

- **Logs**: Service → "Logs" tab
- **Metrics**: Service → "Metrics" tab
- **Database**: PostgreSQL service → "Query" tab
- **Redis**: Redis service → "Status" tab

## Celery Workers (Optional)

For background jobs:

1. Click "New +" → "Background Worker"
2. Name: `weatherops-worker`
3. Build: `pip install -r requirements/base.txt`
4. Start: `celery -A app.workers.celery_app worker --loglevel=info`
5. Link same DATABASE_URL and REDIS_URL
6. Click "Create Background Worker"

## For Scheduled Jobs

1. Click "New +" → "Cron Job"
2. Name: `weatherops-beat`
3. Schedule: `0 */6 * * *` (every 6 hours)
4. Command: `celery -A app.workers.celery_app beat --loglevel=info`
5. Link same DATABASE_URL and REDIS_URL

## Troubleshooting

**Service won't deploy?**
- Check Logs tab for errors
- Verify all env variables are set
- Ensure requirements/base.txt exists

**Database connection fails?**
- Go to PostgreSQL service
- Verify connection in "Query" tab
- Check DATABASE_URL is linked

**Can't connect to Redis?**
- Go to Redis service
- Check status is "Available"
- Verify REDIS_URL is linked

## Production Tips

- ✅ Use Pro plan for production (includes auto-restarts)
- ✅ Enable backups on PostgreSQL
- ✅ Monitor logs regularly
- ✅ Set up error tracking (Sentry)
- ✅ Use strong SECRET_KEY
- ✅ Keep dependencies updated

## Useful Links

- Dashboard: https://dashboard.render.com
- Docs: https://render.com/docs
- Status: https://status.render.com
