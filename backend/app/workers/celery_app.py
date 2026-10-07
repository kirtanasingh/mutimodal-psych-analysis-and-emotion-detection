from celery import Celery

from app.config import settings


celery_app = Celery(
    "psych_session",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.update(task_track_started=True)
celery_app.autodiscover_tasks(["app.workers"])
