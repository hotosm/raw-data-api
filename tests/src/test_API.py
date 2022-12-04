from fastapi.testclient import TestClient

from API.main import app

client = TestClient(app)


def test_status():
    response = client.get("/latest/status/")
    assert response.status_code == 200
