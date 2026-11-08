"""The catalog page (#25), built behind MAKARIOS_CATALOG_PAGE_ENABLED until it ships.

The route reads settings through a dependency, so each test hands it settings
with the flag set the way that test needs, the same override that swaps in
the test database.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app

client = TestClient(app)


def set_catalog_flag(monkeypatch: pytest.MonkeyPatch, *, enabled: bool) -> None:
    """Serve the app with the flag set; monkeypatch removes the override afterwards."""
    flagged = Settings(_env_file=None, catalog_page_enabled=enabled)
    monkeypatch.setitem(app.dependency_overrides, get_settings, lambda: flagged)


def test_with_the_flag_off_the_catalog_page_does_not_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Off is what production runs: a buyer finds a plain 404, like any unknown URL."""
    set_catalog_flag(monkeypatch, enabled=False)

    response = client.get("/watches")

    assert response.status_code == 404
    assert response.json() == client.get("/no-such-page").json()


def test_with_the_flag_on_the_catalog_page_renders(monkeypatch: pytest.MonkeyPatch) -> None:
    set_catalog_flag(monkeypatch, enabled=True)

    response = client.get("/watches")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "The collection" in response.text


def test_the_unfinished_catalog_page_is_kept_out_of_search_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_catalog_flag(monkeypatch, enabled=True)

    response = client.get("/watches")

    assert '<meta name="robots" content="noindex">' in response.text
