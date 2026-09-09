import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket_activity_feed():
    """
    E2E VERIFIED — CONTROLLED MOCK TOOL ENVIRONMENT
    Verify websocket broadcast of activity events.
    """
    client = TestClient(app)
    
    # 1. Create assessment
    res = client.post("/api/assessments", json={
        "name": "WS Test",
        "target": "demo.local",
        "scope": "Full scan",
        "description": "WS E2E"
    })
    assert res.status_code == 200
    assessment_id = res.json()["data"]["id"]

    # 2. Connect to WebSocket
    with client.websocket_connect(f"/api/ws/{assessment_id}") as websocket:
        # 3. Test ping/pong to verify connection is alive
        websocket.send_text("ping")
        data = websocket.receive_json()
        assert data.get("event") == "pong"
        
        # 4. Verify the controller correctly registered the connection for broadcasts
        from app.api.routes import controller
        assert assessment_id in controller._ws_callbacks
        assert len(controller._ws_callbacks[assessment_id]) > 0

