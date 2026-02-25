"""
tasks.py — Celery tasks.

WHAT CHANGED:
  - Added logging so you can see task execution in Celery worker output
  - check_service now returns the record (health_checks.py was fixed to do this)
  - test_task kept for sanity-checking your Celery setup
"""

import logging

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Service
from app.health_checks import check_service


logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.run_all_health_checks")
def run_all_health_checks():
    """
    Scheduled task: ping every registered service and record results.
    Runs every 2 minutes via Celery Beat.
    """
    db = SessionLocal()
    try:
        services = db.query(Service).all()
        logger.info("Running health checks for %d services", len(services))

        for service in services:
            try:
                check_service(db, service)
            except Exception as exc:
                # Don't let one bad service kill checks for all others
                logger.error(
                    "Unexpected error checking service_id=%s: %s",
                    service.id,
                    exc,
                    exc_info=True,
                )

        logger.info("Health check run complete")

    finally:
        db.close()


@celery_app.task
def test_task():
    """Sanity check — run this to verify Celery worker is alive."""
    return "Celery is working!"