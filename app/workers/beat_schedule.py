"""Celery beat schedule configuration."""

from celery.schedules import crontab

beat_schedule = {
    "weather-monitor": {
        "task": "tasks.weather_monitor",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "default", "priority": 10},
    },
}
