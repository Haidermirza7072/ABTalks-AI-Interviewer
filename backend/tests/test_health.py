def test_health_endpoint(client):
    """Test GET /health returns 200 and expected schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "llm_ready" in data
    assert isinstance(data["llm_ready"], bool)

def test_admin_stats(client):
    """Test GET /admin/stats returns memory and session stats."""
    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "active_sessions" in data
    assert "rss_memory_mb" in data

def test_admin_reload_data(client):
    """Test POST /admin/reload-data reloads static JSON files."""
    response = client.post("/admin/reload-data")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reloaded"
    assert data["days"] > 0
    assert data["candidates"] > 0
