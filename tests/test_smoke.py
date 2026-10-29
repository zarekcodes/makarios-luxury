import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app
from tests.conftest import production_settings

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page_renders() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Makarios Luxury" in response.text


def test_pages_are_compressed() -> None:
    """Railway doesn't compress responses, so the app must, for phones on slow connections."""
    response = client.get("/", headers={"Accept-Encoding": "gzip"})

    assert response.headers["content-encoding"] == "gzip"


def test_production_hides_the_api_docs(monkeypatch: pytest.MonkeyPatch) -> None:
    production = production_settings()
    monkeypatch.setattr(main, "get_settings", lambda: production)
    production_client = TestClient(main.create_app())

    assert production_client.get("/docs").status_code == 404
    assert production_client.get("/openapi.json").status_code == 404
    assert production_client.get("/api/health").status_code == 200
