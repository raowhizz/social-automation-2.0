"""
Celery application configuration.
"""

import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery app
celery_app = Celery(
    "social_automation",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["app.tasks.token_tasks", "app.tasks.calendar_tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Celery Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # Refresh tokens expiring within threshold
    "refresh-expiring-tokens": {
        "task": "app.tasks.token_tasks.refresh_expiring_tokens",
        "schedule": crontab(
            hour=f"*/{os.getenv('TOKEN_REFRESH_INTERVAL', '24')}",  # Every N hours
            minute=0,
        ),
    },
    # Cleanup expired OAuth states
    "cleanup-expired-states": {
        "task": "app.tasks.token_tasks.cleanup_expired_states",
        "schedule": crontab(
            hour=f"*/{os.getenv('STATE_CLEANUP_INTERVAL', '1')}",  # Every N hours
            minute=0,
        ),
    },
    # Publish due calendar posts
    "publish-due-calendar-posts": {
        "task": "publish_due_calendar_posts",
        "schedule": crontab(minute="*/1"),  # Every 1 minute
    },
}

if __name__ == "__main__":
    celery_app.start()
