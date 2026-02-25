"""
health_checks.py — Core logic for pinging a service and recording the result.

WHAT CHANGED:
  - BUG FIX: Was importing `HealthCheck` which doesn't exist. Fixed to `CheckHistory`.
  - BUG FIX: Silent `except Exception: pass` replaced with structured logging.
    Before: you had no idea WHY a service was DOWN (timeout? DNS? refused?)
    Now: the exact exception is logged so you can diagnose real problems.
  - Added `failure_reason` local variable for log clarity.
"""

import logging
import requests

from datetime import datetime, timezone

from app.models import CheckHistory  # FIX: was wrongly imported as HealthCheck


logger = logging.getLogger(__name__)


def check_service(db, service) -> CheckHistory:
    """
    Ping `service.url`, record the result in check_history, and return the record.

    Args:
        db: SQLAlchemy session
        service: Service ORM instance (must have .id and .url)

    Returns:
        The CheckHistory record that was saved.
    """
    start = datetime.now(timezone.utc)
    failure_reason = None

    try:
        response = requests.get(service.url, timeout=5)
        status = "UP"
        status_code = response.status_code

        logger.info(
            "Health check OK | service_id=%s url=%s status_code=%s",
            service.id,
            service.url,
            status_code,
        )

    except requests.exceptions.Timeout:
        # Service took longer than 5 seconds to respond
        status = "DOWN"
        status_code = 0
        failure_reason = "Timeout after 5s"

    except requests.exceptions.ConnectionError as exc:
        # DNS failure, refused connection, etc.
        status = "DOWN"
        status_code = 0
        failure_reason = f"ConnectionError: {exc}"

    except Exception as exc:
        # Catch-all for anything unexpected — still logged with detail
        status = "DOWN"
        status_code = 0
        failure_reason = f"Unexpected error: {exc}"

    if failure_reason:
        logger.warning(
            "Health check FAILED | service_id=%s url=%s reason=%s",
            service.id,
            service.url,
            failure_reason,
        )

    end = datetime.now(timezone.utc)
    latency = (end - start).total_seconds()

    record = CheckHistory(
        service_id=service.id,
        status=status,
        status_code=status_code,
        latency=latency,
        checked_at=end,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record