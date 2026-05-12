"""
Tests for health check functionality.
"""
import pytest
from unittest.mock import Mock, patch
from app.health_checks import check_service
from app.models import Service, CheckHistory


def test_check_service_success(db_session):
    """Test successful health check."""
    service = Service(name="Test", url="https://example.com")
    db_session.add(service)
    db_session.commit()
    
    mock_response = Mock()
    mock_response.status_code = 200
    
    with patch('app.health_checks.requests.get', return_value=mock_response):
        result = check_service(db_session, service)
    
    assert result.status == "UP"
    assert result.status_code == 200
    assert result.latency > 0
    assert result.service_id == service.id


def test_check_service_timeout(db_session):
    """Test health check timeout."""
    service = Service(name="Test", url="https://slow-site.com")
    db_session.add(service)
    db_session.commit()
    
    with patch('app.health_checks.requests.get', side_effect=Exception("Timeout")):
        result = check_service(db_session, service)
    
    assert result.status == "DOWN"
    assert result.status_code == 0
    assert result.latency > 0


def test_check_service_connection_error(db_session):
    """Test health check connection error."""
    service = Service(name="Test", url="https://nonexistent.com")
    db_session.add(service)
    db_session.commit()
    
    from requests.exceptions import ConnectionError
    with patch('app.health_checks.requests.get', side_effect=ConnectionError("Failed")):
        result = check_service(db_session, service)
    
    assert result.status == "DOWN"
    assert result.status_code == 0
