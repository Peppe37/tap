"""Celery application instance shared by the API (for enqueuing) and the worker/beat processes.

A single "default" queue is used for every task: per-provider request-rate limiting is enforced
inside app.workers.tasks itself (a Redis counter keyed by provider code), not via dedicated
Celery queues, so one worker process consuming the default queue is enough regardless of how
many provider plugins are installed."""

from celery import Celery

from app.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "tap",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
    beat_schedule={
        "enqueue-due-packages": {
            "task": "app.workers.tasks.enqueue_due_packages",
            "schedule": 300.0,
        },
    },
)
