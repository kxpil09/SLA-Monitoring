"""
Tests for API endpoints.
"""
import pytest
from app.models import Service, CheckHistory


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_service(client):
    """Test creating a new service."""
    payload = {
        "name": "Google",
        "url": "https://google.com"
    }
    response = client.post("/api/v1/services", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Google"
    assert data["url"].rstrip("/") == "https://google.com"
    assert "id" in data
    assert "created_at" in data


def test_create_service_invalid_url(client):
    """Test creating service with invalid URL."""
    payload = {
        "name": "Invalid",
        "url": "not-a-url"
    }
    response = client.post("/api/v1/services", json=payload)
    assert response.status_code == 422


def test_list_services(client, sample_service):
    """Test listing all services."""
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Service"


def test_get_service(client, sample_service):
    """Test getting a single service."""
    response = client.get(f"/api/v1/services/{sample_service.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_service.id
    assert data["name"] == "Test Service"


def test_get_service_not_found(client):
    """Test getting non-existent service."""
    response = client.get("/api/v1/services/999")
    assert response.status_code == 404


def test_delete_service(client, sample_service):
    """Test deleting a service."""
    response = client.delete(f"/api/v1/services/{sample_service.id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get(f"/api/v1/services/{sample_service.id}")
    assert response.status_code == 404


def test_delete_service_not_found(client):
    """Test deleting non-existent service."""
    response = client.delete("/api/v1/services/999")
    assert response.status_code == 404


def test_get_history(client, sample_service, db_session):
    """Test getting service history."""
    # Add some check history
    check = CheckHistory(
        service_id=sample_service.id,
        status="UP",
        status_code=200,
        latency=0.5
    )
    db_session.add(check)
    db_session.commit()
    
    response = client.get(f"/api/v1/services/{sample_service.id}/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "UP"
    assert data[0]["status_code"] == 200


def test_get_history_pagination(client, sample_service, db_session):
    """Test history pagination."""
    # Add multiple checks
    for i in range(10):
        check = CheckHistory(
            service_id=sample_service.id,
            status="UP",
            status_code=200,
            latency=0.1 * i
        )
        db_session.add(check)
    db_session.commit()
    
    response = client.get(f"/api/v1/services/{sample_service.id}/history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    response = client.get(f"/api/v1/services/{sample_service.id}/history?limit=5&offset=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_get_history_service_not_found(client):
    """Test getting history for non-existent service."""
    response = client.get("/api/v1/services/999/history")
    assert response.status_code == 404
