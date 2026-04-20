from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_index_is_served():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "上传论文" in response.text
    assert "/static/app.js" in response.text


def test_frontend_static_asset_is_served():
    client = TestClient(create_app())

    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "fetch(\"/api/papers/upload\"" in response.text
