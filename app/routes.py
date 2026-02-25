"""
routes.py — All API routes for the SLA Monitor.

FIXES:
  - Immediate health check triggered on service creation via Celery task.
    No more waiting up to 2 minutes for first data after adding a service.
  - AnyHttpUrl validation on ServiceCreate.url
  - Normalize AnyHttpUrl to str before saving
"""

import logging

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, ConfigDict, AnyHttpUrl
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Service, CheckHistory
from app.health_checks import check_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["services"])


# -----------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------

class ServiceCreate(BaseModel):
    name: str
    url: AnyHttpUrl


class ServiceOut(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HistoryOut(BaseModel):
    id: int
    status: str
    status_code: int
    latency: float
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------
# Background task: run one immediate health check after service creation
# so the frontend shows real data instantly instead of waiting ~2 minutes.
# -----------------------------------------------------------------------

def _immediate_check(service_id: int):
    """Run a single health check for a newly created service right away."""
    db = SessionLocal()
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if service:
            check_service(db, service)
            logger.info("Immediate check complete for service_id=%s", service_id)
    except Exception as exc:
        logger.error("Immediate check failed for service_id=%s: %s", service_id, exc)
    finally:
        db.close()


# -----------------------------------------------------------------------
# Service CRUD Routes
# -----------------------------------------------------------------------

@router.post("/services", response_model=ServiceOut, status_code=201)
def create_service(
    payload: ServiceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Register a new service to monitor.
    Triggers an immediate health check in the background so the
    frontend shows real data within seconds instead of waiting for
    the next Celery Beat tick (~2 minutes).
    """
    service = Service(name=payload.name, url=str(payload.url))
    db.add(service)
    db.commit()
    db.refresh(service)
    logger.info("Created service id=%s name=%r url=%r", service.id, service.name, service.url)

    # Fire-and-forget: ping the URL immediately
    background_tasks.add_task(_immediate_check, service.id)

    return service


@router.get("/services", response_model=List[ServiceOut])
def list_services(db: Session = Depends(get_db)):
    """Return all registered services."""
    return db.query(Service).order_by(Service.id).all()


@router.get("/services/{service_id}", response_model=ServiceOut)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
):
    """Fetch a single service by ID."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.delete("/services/{service_id}", status_code=204)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
):
    """Delete a service and all its history. Returns 204 No Content on success."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    db.delete(service)
    db.commit()
    logger.info("Deleted service id=%s", service_id)
    return


# -----------------------------------------------------------------------
# Health Check History Route
# -----------------------------------------------------------------------

@router.get("/services/{service_id}/history", response_model=List[HistoryOut])
def get_history(
    service_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Return paginated health check history for a service.

    Query params:
      - limit: how many records to return (1-500, default 50)
      - offset: how many records to skip (for pagination)
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    history = (
        db.query(CheckHistory)
        .filter(CheckHistory.service_id == service_id)
        .order_by(CheckHistory.checked_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return history