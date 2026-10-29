# app/core/celery_app.py
# Optional: Celery integration for background tasks
try:
    from celery import Celery
    from app.core.config import settings

    celery_app = Celery(
        "agentforge",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks.analysis_tasks", "app.tasks.streaming_tasks"],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
except ImportError:
    celery_app = None
