"""
celery_app.py — Celery application and Beat schedule configuration.

WHAT CHANGED:
  - broker/backend URLs now come from config.settings
"""

from celery import Celery

from app.config import settings


celery_app = Celery(
    "sla_monitor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.beat_schedule = {
    "run-health-checks-every-2-minutes": {
        "task": "app.tasks.run_all_health_checks",
        "schedule": 120.0,
    }
}

celery_app.conf.timezone = "UTC"