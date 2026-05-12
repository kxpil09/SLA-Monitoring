"""
Tests for alerting functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.alerts import send_alert_email, check_and_send_alert
from app.models import Service, CheckHistory, AlertState


def test_send_alert_email_disabled(db_session):
    """Test that alerts are skipped when disabled."""
    with patch('app.alerts.settings.ENABLE_EMAIL_ALERTS', False):
        with patch('app.alerts.smtplib.SMTP') as mock_smtp:
            send_alert_email("Test", "https://test.com", "DOWN", 1)
            mock_smtp.assert_not_called()


def test_send_alert_email_success(db_session):
    """Test successful email sending."""
    with patch('app.alerts.settings.ENABLE_EMAIL_ALERTS', True):
        with patch('app.alerts.settings.SMTP_HOST', 'smtp.test.com'):
            with patch('app.alerts.settings.ALERT_TO_EMAILS', 'test@example.com'):
                with patch('app.alerts.settings.ALERT_FROM_EMAIL', 'alerts@test.com'):
                    with patch('app.alerts.smtplib.SMTP') as mock_smtp:
                        mock_server = MagicMock()
                        mock_smtp.return_value.__enter__.return_value = mock_server
                        
                        send_alert_email("Test Service", "https://test.com", "DOWN", 1)
                        
                        mock_server.starttls.assert_called_once()
                        mock_server.send_message.assert_called_once()


def test_check_and_send_alert_new_service_down(db_session):
    """Test alert when new service goes down."""
    service = Service(name="Test", url="https://test.com")
    db_session.add(service)
    db_session.commit()
    
    check = CheckHistory(
        service_id=service.id,
        status="DOWN",
        status_code=0,
        latency=5.0
    )
    db_session.add(check)
    db_session.commit()
    
    with patch('app.alerts.send_alert_email') as mock_send:
        check_and_send_alert(db_session, service, check)
        mock_send.assert_called_once()
        assert mock_send.call_args[0][2] == "DOWN"


def test_check_and_send_alert_recovery(db_session):
    """Test alert when service recovers."""
    service = Service(name="Test", url="https://test.com")
    db_session.add(service)
    db_session.commit()
    
    # Create existing DOWN state
    alert_state = AlertState(
        service_id=service.id,
        last_status="DOWN",
        failure_count=3
    )
    db_session.add(alert_state)
    db_session.commit()
    
    # Service recovers
    check = CheckHistory(
        service_id=service.id,
        status="UP",
        status_code=200,
        latency=0.5
    )
    db_session.add(check)
    db_session.commit()
    
    with patch('app.alerts.send_alert_email') as mock_send:
        check_and_send_alert(db_session, service, check)
        mock_send.assert_called_once()
        assert mock_send.call_args[0][2] == "UP"


def test_check_and_send_alert_consecutive_failures(db_session):
    """Test reminder alerts every 5 failures."""
    service = Service(name="Test", url="https://test.com")
    db_session.add(service)
    db_session.commit()
    
    alert_state = AlertState(
        service_id=service.id,
        last_status="DOWN",
        failure_count=4
    )
    db_session.add(alert_state)
    db_session.commit()
    
    check = CheckHistory(
        service_id=service.id,
        status="DOWN",
        status_code=0,
        latency=5.0
    )
    db_session.add(check)
    db_session.commit()
    
    with patch('app.alerts.send_alert_email') as mock_send:
        check_and_send_alert(db_session, service, check)
        # Should send alert on 5th failure
        mock_send.assert_called_once()
        
        # Check failure count incremented
        updated_state = db_session.query(AlertState).filter(
            AlertState.service_id == service.id
        ).first()
        assert updated_state.failure_count == 5
