"""Celery application configuration for background task processing."""

from celery import Celery
from loguru import logger

from config.settings import settings

# Create Celery app
celery_app = Celery(
    "sales_call_analysis",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.tasks.transcription_tasks",
        "workers.tasks.analysis_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # 1 hour
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_compression="gzip",
    result_compression="gzip"
)

# Task routing
celery_app.conf.task_routes = {
    "workers.tasks.transcription_tasks.*": {"queue": "transcription"},
    "workers.tasks.analysis_tasks.*": {"queue": "analysis"},
}

# Error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Request: {self.request!r}")


# Health check task
@celery_app.task(bind=True)
def health_check(self):
    """Health check task for monitoring."""
    return {
        "status": "healthy",
        "worker_id": self.request.id,
        "timestamp": self.request.timestamp
    }


if __name__ == "__main__":
    celery_app.start()
