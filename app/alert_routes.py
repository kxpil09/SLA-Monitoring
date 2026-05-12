"""
alert_routes.py — API routes for alert configuration and management.
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Service, AlertState
from app.config import settings
from app.alerts import send_alert_email


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


# -----------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------

class AlertSettingsOut(BaseModel):
    enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    alert_from: str
    alert_to: List[str]
    
    model_config = ConfigDict(from_attributes=True)


class AlertHistoryOut(BaseModel):
    service_id: int
    service_name: str
    last_status: str
    failure_count: int
    last_alert_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class TestAlertRequest(BaseModel):
    email: EmailStr


class UpdateAlertRecipientsRequest(BaseModel):
    emails: List[EmailStr]


# -----------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------

@router.get("/settings", response_model=AlertSettingsOut)
def get_alert_settings():
    """Get current alert configuration."""
    return {
        "enabled": settings.ENABLE_EMAIL_ALERTS,
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER,
        "alert_from": settings.ALERT_FROM_EMAIL,
        "alert_to": settings.ALERT_TO_EMAILS.split(",") if settings.ALERT_TO_EMAILS else [],
    }


@router.get("/history", response_model=List[AlertHistoryOut])
def get_alert_history(db: Session = Depends(get_db)):
    """Get alert history for all services."""
    alert_states = (
        db.query(AlertState, Service.name)
        .join(Service, AlertState.service_id == Service.id)
        .all()
    )
    
    return [
        {
            "service_id": state.service_id,
            "service_name": name,
            "last_status": state.last_status,
            "failure_count": state.failure_count,
            "last_alert_at": state.last_alert_at,
        }
        for state, name in alert_states
    ]


@router.post("/test")
def send_test_alert(payload: TestAlertRequest):
    """Send a test alert email."""
    if not settings.ENABLE_EMAIL_ALERTS:
        raise HTTPException(
            status_code=400,
            detail="Email alerts are disabled. Enable them in settings."
        )
    
    try:
        # Temporarily override alert recipients for test
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        subject = "✅ Test Alert from SLA Monitor"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #10b981;">✅ Test Alert</h2>
            <p>This is a test email from your SLA Monitor.</p>
            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            <p><strong>Sent to:</strong> {payload.email}</p>
            <hr>
            <p style="font-size: 12px; color: #666;">
                If you received this email, your alert system is working correctly!
            </p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.ALERT_FROM_EMAIL
        msg['To'] = payload.email
        
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info("Test alert sent to %s", payload.email)
        return {"message": f"Test alert sent to {payload.email}"}
    
    except Exception as exc:
        logger.error("Failed to send test alert: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test alert: {str(exc)}"
        )


@router.get("/status")
def get_alert_status(db: Session = Depends(get_db)):
    """Get overall alert system status."""
    total_services = db.query(Service).count()
    alert_states = db.query(AlertState).all()
    
    down_services = sum(1 for state in alert_states if state.last_status == "DOWN")
    services_with_failures = sum(1 for state in alert_states if state.failure_count > 0)
    
    return {
        "enabled": settings.ENABLE_EMAIL_ALERTS,
        "total_services": total_services,
        "down_services": down_services,
        "services_with_failures": services_with_failures,
        "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_USER),
    }


@router.post("/recipients")
def update_alert_recipients(payload: UpdateAlertRecipientsRequest, db: Session = Depends(get_db)):
    """Update alert recipients dynamically."""
    from app.models import AlertSettings
    
    # Convert list to comma-separated string
    emails_str = ",".join(payload.emails)
    
    # Get or create setting
    setting = db.query(AlertSettings).filter(
        AlertSettings.key == "alert_recipients"
    ).first()
    
    if setting:
        setting.value = emails_str
        setting.updated_at = datetime.utcnow()
    else:
        setting = AlertSettings(
            key="alert_recipients",
            value=emails_str
        )
        db.add(setting)
    
    db.commit()
    db.refresh(setting)
    
    logger.info("Alert recipients updated: %s", emails_str)
    
    return {
        "message": "Alert recipients updated successfully",
        "recipients": payload.emails
    }


@router.get("/recipients")
def get_alert_recipients_api(db: Session = Depends(get_db)):
    """Get current alert recipients."""
    from app.alerts import get_alert_recipients
    
    recipients = get_alert_recipients(db)
    
    return {
        "recipients": recipients,
        "source": "database" if recipients else "env"
    }
