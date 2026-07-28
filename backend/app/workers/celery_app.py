"""
Curato AI — Celery Application Configuration

Configures the Celery instance for background task execution.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "curato_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Retry
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Task execution limits
    task_soft_time_limit=600,   # 10 minutes soft limit
    task_time_limit=900,        # 15 minutes hard limit

    # Result expiration
    result_expires=86400,       # Results expire after 24 hours

    # Task discovery
    task_routes={
        "app.workers.tasks.*": {"queue": "curato_workflows"},
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers"])
