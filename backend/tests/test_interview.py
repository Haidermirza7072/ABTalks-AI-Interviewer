def test_interview_lifecycle(client):
    """Test complete happy-path interview flow: start -> respond -> feedback."""
    # 1. Start interview
    start_resp = client.post("/interview/start", json={"candidate_id": "cand_101"})
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    assert start_data["turn_count"] == 1
    assert "first_question" in start_data
    assert len(start_data["first_question"]) > 0

    # 2. Submit answer (turn 1 -> turn 2)
    resp1 = client.post(f"/interview/{session_id}/respond", json={
        "answer": "I structure FastAPI apps using modular router packages, Pydantic v2 schemas for request validation, and domain context services."
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["turn_count"] == 2
    assert "next_question" in data1

    # 3. Submit answer (turn 2 -> turn 3, can_conclude = True)
    resp2 = client.post(f"/interview/{session_id}/respond", json={
        "answer": "For session state management, I use an in-memory dictionary with disk persistence and background TTL cleanup jobs."
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["turn_count"] == 3
    assert data2["can_conclude"] is True

    # 4. Generate final feedback
    fb_resp = client.post(f"/interview/{session_id}/feedback")
    assert fb_resp.status_code == 200
    fb_data = fb_resp.json()
    assert 1 <= fb_data["readiness_score"] <= 10
    assert len(fb_data["strengths"]) > 0
    assert len(fb_data["growth_areas"]) > 0
    assert fb_data["is_partial"] is False

def test_start_interview_invalid_candidate(client):
    """Test starting interview with non-existent candidate returns 404."""
    response = client.post("/interview/start", json={"candidate_id": "cand_non_existent"})
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "CANDIDATE_NOT_FOUND"

def test_respond_invalid_session(client):
    """Test responding to non-existent session returns 404."""
    response = client.post("/interview/invalid_session_id/respond", json={"answer": "Some valid answer."})
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "SESSION_NOT_FOUND"

def test_respond_validation_error(client):
    """Test submitting empty answer triggers 422 validation error."""
    start_resp = client.post("/interview/start", json={"candidate_id": "cand_101"})
    session_id = start_resp.json()["session_id"]

    response = client.post(f"/interview/{session_id}/respond", json={"answer": ""})
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"

def test_abort_interview(client):
    """Test aborting interview early returns partial feedback report."""
    start_resp = client.post("/interview/start", json={"candidate_id": "cand_101"})
    session_id = start_resp.json()["session_id"]

    abort_resp = client.post(f"/interview/{session_id}/abort")
    assert abort_resp.status_code == 200
    data = abort_resp.json()
    assert data["is_partial"] is True
    assert "disclaimer" in data
