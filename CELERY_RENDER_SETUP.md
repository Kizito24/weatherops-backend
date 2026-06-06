# Celery Setup for Render Deployment

This guide explains how Celery is configured for your WeatherOps backend on Render.

## Architecture Overview

Your Render deployment now has three worker services:

```
┌─────────────────────────────────────────────────────────┐
│ WeatherOps API Service                                  │
│ - Handles HTTP requests                                 │
│ - Submits tasks to Celery queue                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │  Redis Queue  │
         └───────────────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Worker  │ │ Worker  │ │  Beat   │
    │ Instance│ │ Instance│ │Scheduler│
    │ (2 CPU) │ │ (Future)│ │ (1 CPU) │
    └─────────┘ └─────────┘ └─────────┘
```

## Services Configuration

### 1. **API Service** (weatherops-api)
- Type: `web`
- Runs: FastAPI application
- Handles: HTTP requests, webhook endpoints
- Submits tasks to Redis queue

### 2. **Celery Worker** (weatherops-celery-worker)
- Type: `worker`
- Runs: `celery -A app.workers.celery_app worker --loglevel=info --concurrency=2`
- Processes: Async tasks from Redis queue
- Concurrency: 2 (suitable for Render starter plan)
- Executes: `tasks.weather_monitor` on schedule

### 3. **Celery Beat** (weatherops-celery-beat)
- Type: `worker`
- Runs: `celery -A app.workers.celery_app beat --loglevel=info`
- Schedules: Periodic tasks (weather monitoring every 5 minutes)
- Persists schedule to: File-based storage (celerybeat-schedule file)

## Environment Variables

Required environment variables (should already be in Render):

```bash
# Database - Auto-populated by Render
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis - Auto-populated by Render
REDIS_URL=redis://:password@host:6379/0

# Celery Configuration (empty values fall back to REDIS_URL)
CELERY_BROKER_URL=               # Falls back to REDIS_URL
CELERY_RESULT_BACKEND=           # Falls back to REDIS_URL
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC
CELERY_TASK_TRACK_STARTED=True
CELERY_TASK_TIME_LIMIT=3600      # 1 hour timeout per task

# Application
APP_NAME=WeatherOps
ENVIRONMENT=production
DEBUG=False

# External Services
WEATHERAI_API_KEY=<your-key>
SENDGRID_API_KEY=<your-key>
TWILIO_ACCOUNT_SID=<your-key>
```

## Deployment Steps

### Step 1: Set Environment Variables in Render

1. Go to your Render dashboard
2. For each service (API, Worker, Beat), set environment variables:
   - `DATABASE_URL` → Copy from PostgreSQL service → Info → Internal Database URL
   - `REDIS_URL` → Copy from Redis service → Info → Internal Redis URL
   - All other vars from `.env.render`

### Step 2: Ensure Services Have Database Access

The **Celery services need access to the database** for:
- Reading active rules
- Reading locations
- Creating and updating alerts
- Reading weather snapshots

In Render dashboard:
- Go to each worker service (Worker, Beat)
- Add `DATABASE_URL` environment variable
- Add `REDIS_URL` environment variable

### Step 3: Monitor Logs

In Render dashboard, view logs for each service:

**API Service Logs:**
```
[INFO] Starting Uvicorn server on port 8000
[INFO] Application startup complete
```

**Worker Logs:**
```
[INFO] celery worker started, version 5.x.x
[INFO] Connected to redis://...
[INFO] Ready to accept tasks
```

**Beat Logs:**
```
[INFO] celery beat started
[INFO] Scheduler: celery.beat.SchedulingError - weather-monitor [next: 2024-06-06 14:05:00]
```

## Testing the Setup

### Test 1: Health Check
```bash
curl https://your-api.onrender.com/health
# Should return: {"status": "ok"}
```

### Test 2: Check Active Alerts
```bash
curl https://your-api.onrender.com/alerts
# Should return list of alerts (auth required)
```

### Test 3: Verify Task Execution
Check Celery worker logs - you should see:
```
[INFO] Weather monitor task started
[INFO] Processing N locations
[INFO] Weather monitor task completed
```

This indicates the scheduled task ran successfully every 5 minutes.

## Common Issues & Troubleshooting

### Issue: Tasks not executing

**Symptoms:**
- Beat scheduler starts but shows no scheduled tasks
- Weather monitor task never runs

**Solutions:**
1. Check Beat logs for schedule loading
2. Verify `beat_schedule` is configured in `celery_app.py`
3. Ensure Worker service is running and connected to Redis
4. Check Redis connectivity: `REDIS_URL` must be accessible

### Issue: Worker crashes on startup

**Symptoms:**
- Worker service shows "Failed" or crashes immediately

**Solutions:**
1. Check worker logs for ImportError
2. Verify all packages in `requirements/base.txt` are installed
3. Check `CELERY_BROKER_URL` points to valid Redis instance
4. Ensure `DATABASE_URL` is reachable from worker environment

### Issue: Database connection errors

**Symptoms:**
- Worker logs show: `psycopg2.OperationalError: could not connect to server`

**Solutions:**
1. Verify `DATABASE_URL` is set in worker service environment
2. Check PostgreSQL service is running
3. Ensure Network allows connections between services

### Issue: Beat schedule not persisting

**Symptoms:**
- Beat service restarts lose scheduled tasks

**Solutions:**
1. Beat schedule is file-based, stored in `/tmp/celerybeat-schedule`
2. On Render, this is ephemeral (cleared on restart)
3. This is normal - schedule reloads from `beat_schedule.py` config

## Scaling Considerations

### Adding More Workers

To add more Celery worker instances:

1. In Render dashboard, go to weatherops-celery-worker service
2. Increase concurrency in `startCommand`:
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
   ```
3. Or deploy additional worker services with different names

### Monitoring Task Queue

Install Flower (Celery monitoring tool) for better visibility:

```bash
# Add to requirements
pip install flower

# Start Flower service in Render
celery -A app.workers.celery_app flower --port=5555
```

Then access at `https://your-flower.onrender.com`

## Key Files

- `render.yaml` - Service definitions
- `app/workers/celery_app.py` - Celery configuration
- `app/workers/beat_schedule.py` - Scheduled tasks definition
- `app/workers/tasks/weather_monitor.py` - Weather monitoring task
- `.env.render` - Environment variables template

## Next Steps

1. Push this code to trigger a new deployment
2. Monitor all three services in Render dashboard
3. Verify weather alerts are created every 5 minutes
4. Check notification channels (email, SMS) receive alerts

