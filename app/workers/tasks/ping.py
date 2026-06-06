"""
Example Celery task.
Demonstrates task structure and execution.
"""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.ping")
def ping_task(self) -> str:
    """
    Example ping task.

    Returns:
        "pong"
    """
    logger.info(f"Ping task executing. Task ID: {self.request.id}")
    return "pong"
