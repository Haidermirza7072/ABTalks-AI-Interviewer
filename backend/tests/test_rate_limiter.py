from app.config import settings

def test_rate_limiter_exceeded(client):
    """Test that exceeding the rate limit per IP returns 429 Retry-After."""
    # Set small limit for testing or execute requests
    limit = settings.RATE_LIMIT_PER_MINUTE
    responses = []
    
    # Make limit + 1 requests
    for _ in range(limit + 1):
        resp = client.get("/health")
        responses.append(resp)

    # The 31st request should be rate limited (429)
    last_resp = responses[-1]
    assert last_resp.status_code == 429
    data = last_resp.json()
    assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in last_resp.headers
