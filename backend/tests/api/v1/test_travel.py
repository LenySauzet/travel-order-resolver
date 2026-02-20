from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.app.main import app

client = TestClient(app)

def test_shortest_path_success():
    # Assuming "Abancourt" (id: 0) and "Amiens" (id: 12) are valid and connected
    # We use query parameters
    response = client.get("/api/v1/shortest-path?start_id=0&end_id=12")
    assert response.status_code == 200
    data = response.json()
    assert "duration_minutes" in data
    assert "path" in data
    assert isinstance(data["path"], list)
    # If path exists, duration should be positive
    if data["duration_minutes"] >= 0:
        assert len(data["path"]) >= 2
        assert data["path"][0]["id"] == 0
        assert data["path"][-1]["id"] == 12

def test_shortest_path_not_found():
    # Use IDs that are unlikely to be connected or exist in graph if graph is sparse
    # or ensure we mock a case where no path exists.
    # For now, we test the endpoint structure.
    # ID 999999 likely doesn't exist
    response = client.get("/api/v1/shortest-path?start_id=0&end_id=999999")
    assert response.status_code == 200
    data = response.json()
    # Expecting -1.0 for no path/not found as per our previous fix
    assert data["duration_minutes"] == -1.0
    assert data["path"] == []

def test_shortest_path_invalid_params():
    response = client.get("/api/v1/shortest-path")
    assert response.status_code == 422  # Missing required params
