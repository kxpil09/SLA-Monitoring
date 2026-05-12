"""
alerts.py — Email alerting for service downtime.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from app.config import settings


logger = logging.getLogger(__name__)


def get_alert_recipients(db):
    """
    Get alert recipients from database if configured, otherwise use .env settings.
    """
    from app.models import AlertSettings
    
    # Try to get from database first
    setting = db.query(AlertSettings).filter(
        AlertSettings.key == "alert_recipients"
    ).first()
    
    if setting and setting.value:
        # Return database value (comma-separated emails)
        return [email.strip() for email in setting.value.split(",")]
    
    # Fallback to .env configuration
    if settings.ALERT_TO_EMAILS:
        return [email.strip() for email in settings.ALERT_TO_EMAILS.split(",")]
    
    return []


def send_alert_email(service_name: str, service_url: str, status: str, failure_count: int, db=None):
    """
    Send an email alert when a service goes down or recovers.
    
    Args:
        service_name: Name of the service
        service_url: URL being monitored
        status: Current status (UP/DOWN)
        failure_count: Number of consecutive failures
    """
    if not settings.ENABLE_EMAIL_ALERTS:
        logger.debug("Email alerts disabled, skipping")
        return
    
    if not settings.SMTP_HOST or not settings.ALERT_TO_EMAILS:
        logger.warning("Email alerts enabled but SMTP not configured")
        return
    
    # Get recipients (dynamic from DB or fallback to .env)
    if db:
        to_emails = get_alert_recipients(db)
    else:
        to_emails = [email.strip() for email in settings.ALERT_TO_EMAILS.split(",")]
    
    subject = f"🚨 ALERT: {service_name} is {status}"
    if status == "UP":
        subject = f"✅ RECOVERED: {service_name} is back online"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: {'#f43f5e' if status == 'DOWN' else '#10b981'};">
            {'⚠️ Service Down' if status == 'DOWN' else '✅ Service Recovered'}
        </h2>
        <p><strong>Service:</strong> {service_name}</p>
        <p><strong>URL:</strong> <a href="{service_url}">{service_url}</a></p>
        <p><strong>Status:</strong> {status}</p>
        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        {f'<p><strong>Consecutive Failures:</strong> {failure_count}</p>' if status == 'DOWN' else ''}
        <hr>
        <p style="font-size: 12px; color: #666;">
            This is an automated alert from SLA Monitor.
        </p>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.ALERT_FROM_EMAIL
        msg['To'] = ", ".join(to_emails)
        
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(
            "Alert email sent: service=%s status=%s recipients=%s",
            service_name, status, len(to_emails)
        )
    
    except Exception as exc:
        logger.error("Failed to send alert email: %s", exc, exc_info=True)


def check_and_send_alert(db, service, check_result):
    """
    Check if an alert should be sent based on service status changes.
    
    Args:
        db: Database session
        service: Service model instance
        check_result: CheckHistory result from health check
    """
    from app.models import AlertState
    
    # Get or create alert state
    alert_state = db.query(AlertState).filter(
        AlertState.service_id == service.id
    ).first()
    
    if not alert_state:
        alert_state = AlertState(
            service_id=service.id,
            last_status="UP",
            failure_count=0
        )
        db.add(alert_state)
    
    current_status = check_result.status
    previous_status = alert_state.last_status
    
    # Service went DOWN
    if current_status == "DOWN" and previous_status == "UP":
        alert_state.failure_count = 1
        alert_state.last_status = "DOWN"
        alert_state.last_alert_at = datetime.utcnow()
        db.commit()
        
        send_alert_email(
            service.name,
            service.url,
            "DOWN",
            alert_state.failure_count,
            db
        )
    
    # Service still DOWN (increment counter)
    elif current_status == "DOWN" and previous_status == "DOWN":
        alert_state.failure_count += 1
        db.commit()
        
        # Send reminder every 5 failures
        if alert_state.failure_count % 5 == 0:
            send_alert_email(
                service.name,
                service.url,
                "DOWN",
                alert_state.failure_count,
                db
            )
    
    # Service RECOVERED
    elif current_status == "UP" and previous_status == "DOWN":
        alert_state.last_status = "UP"
        alert_state.failure_count = 0
        alert_state.last_alert_at = datetime.utcnow()
        db.commit()
        
        send_alert_email(
            service.name,
            service.url,
            "UP",
            0,
            db
        )
    
    # Service still UP (no alert needed)
    else:
        alert_state.last_status = "UP"
        alert_state.failure_count = 0
        db.commit()
