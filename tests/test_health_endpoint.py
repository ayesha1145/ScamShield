"""
test_health_endpoint.py — Smoke test for the ScamShield /health API.
Ensures the backend server responds correctly.
"""

from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)

def test_health_endpoint_returns_ok():
    """Verify that /health returns a 200 OK and valid JSON body."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"].lower() in ["ok", "healthy"]
