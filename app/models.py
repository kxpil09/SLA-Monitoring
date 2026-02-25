"""
models.py — SQLAlchemy ORM models.

WHAT CHANGED:
  - Added __repr__ to each model (makes debugging print statements readable)
  - No structural changes; models were already well designed
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    checks = relationship(
        "CheckHistory",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    alert_state = relationship(
        "AlertState",
        back_populates="service",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Service id={self.id} name={self.name!r} url={self.url!r}>"


class CheckHistory(Base):
    __tablename__ = "check_history"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String, nullable=False)       # "UP" or "DOWN"
    status_code = Column(Integer, nullable=False)  # HTTP code, or 0 on timeout
    latency = Column(Float, nullable=False)        # seconds
    checked_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    service = relationship("Service", back_populates="checks")

    def __repr__(self):
        return (
            f"<CheckHistory service_id={self.service_id} "
            f"status={self.status!r} latency={self.latency:.3f}s>"
        )


class AlertState(Base):
    """
    Tracks the ongoing alert state per service.
    Used to avoid sending duplicate alerts and to count consecutive failures.
    Will be wired into alert logic in Step 3.
    """
    __tablename__ = "alert_states"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    last_status = Column(String, nullable=False, default="UP")
    failure_count = Column(Integer, default=0, nullable=False)
    last_alert_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    service = relationship("Service", back_populates="alert_state")

    def __repr__(self):
        return (
            f"<AlertState service_id={self.service_id} "
            f"last_status={self.last_status!r} failures={self.failure_count}>"
        )