"""
Integration tests for /health endpoint and correlation headers.
"""
def test_health_check_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "object_storage" in data
    assert "worker_heartbeat" in data
    assert data["database"] in ["ok", "degraded", "down"]
    assert "X-Request-ID" in response.headers


def test_custom_request_id_propagation(client):
    custom_id = "11111111-2222-3333-4444-555555555555"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id
