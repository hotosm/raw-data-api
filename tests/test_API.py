from fastapi.testclient import TestClient

from API.main import app

client = TestClient(app)


def test_status():
    response = client.get("/latest/status/")
    assert response.status_code == 200

def test_snapshot():
    response = client.post("/latest/snapshot/", json={
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [83.96919250488281, 28.194446860487773],
                                [83.99751663208006, 28.194446860487773],
                                [83.99751663208006, 28.214869548073377],
                                [83.96919250488281, 28.214869548073377],
                                [83.96919250488281, 28.194446860487773],
                            ]
                        ],
                    }
                })
    assert response.status_code == 200
    res = response.json()
    track_link = res['track_link']
    response = client.get(f"/latest{track_link}")
    assert response.status_code == 200
    res = response.json()
    check_status = res["status"]
    print(check_status)
    assert check_status == "PENDING" or check_status == "RUNNING" or check_status == "SUCCESS"

