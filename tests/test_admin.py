"""The admin at /admin: who gets in, who doesn't, and what a signed-in owner can do.

Each test builds its own app around the test's database, with a throttle
whose clock the test controls, so nothing here waits fifteen real minutes.
"""

from collections.abc import Callable
from html.parser import HTMLParser

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request

from app.admin import client_address, mount_admin
from app.config import Settings
from app.main import app as real_app
from app.models import Watch
from app.services import admin_accounts
from app.services.login_throttle import LoginThrottle
from tests.conftest import production_settings

PASSWORD = "correct horse battery staple"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def session_maker(engine: Engine) -> Callable[[], Session]:
    return sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def owner(session: Session) -> str:
    admin_accounts.set_password(session, "owner", PASSWORD)
    return "owner"


def admin_client(
    session_maker: Callable[[], Session],
    clock: FakeClock,
    settings: Settings | None = None,
) -> TestClient:
    app = FastAPI()
    mount_admin(
        app,
        settings or Settings(_env_file=None),
        session_maker,
        LoginThrottle(clock=clock),
    )
    return TestClient(app)


@pytest.fixture
def client(session_maker: Callable[[], Session], clock: FakeClock) -> TestClient:
    return admin_client(session_maker, clock)


def log_in(
    client: TestClient, username: str, password: str, forwarded_for: str | None = None
) -> httpx.Response:
    return client.post(
        "/admin/login",
        data={"username": username, "password": password},
        headers={"X-Forwarded-For": forwarded_for} if forwarded_for else None,
        follow_redirects=False,
    )


def test_the_real_app_mounts_the_admin_behind_the_login() -> None:
    response = TestClient(real_app).get("/admin/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"].endswith("/admin/login")


@pytest.mark.parametrize("path", ["/admin/", "/admin/watch/list", "/admin/watch/edit/1"])
def test_anonymous_requests_are_sent_to_the_login(client: TestClient, path: str) -> None:
    response = client.get(path, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"].endswith("/admin/login")


def test_the_login_form_is_served(client: TestClient) -> None:
    response = client.get("/admin/login")

    assert response.status_code == 200
    assert 'name="password"' in response.text


def test_a_wrong_password_is_rejected(client: TestClient, owner: str) -> None:
    response = log_in(client, owner, "not the password at all")

    assert response.status_code == 400
    assert client.get("/admin/", follow_redirects=False).status_code == 302


def test_an_unknown_username_is_rejected_the_same_way(client: TestClient, owner: str) -> None:
    """Same status, same page: the response mustn't reveal which usernames exist."""
    unknown = log_in(client, "nobody", PASSWORD)
    wrong_password = log_in(client, owner, "not the password at all")

    assert unknown.status_code == wrong_password.status_code == 400
    assert unknown.text == wrong_password.text


def test_the_right_password_reaches_the_watch_list(client: TestClient, owner: str) -> None:
    response = log_in(client, owner, PASSWORD)

    assert response.status_code == 302
    watches = client.get("/admin/watch/list")
    assert watches.status_code == 200
    assert "Aurelian" in watches.text


def test_logging_out_ends_the_session(client: TestClient, owner: str) -> None:
    log_in(client, owner, PASSWORD)

    client.get("/admin/logout")

    assert client.get("/admin/", follow_redirects=False).status_code == 302


def test_a_new_password_signs_the_owner_out(
    client: TestClient, owner: str, session: Session
) -> None:
    """Changing a stolen password must lock out whoever already signed in with it."""
    log_in(client, owner, PASSWORD)

    admin_accounts.set_password(session, owner, "a completely different passphrase")

    assert client.get("/admin/", follow_redirects=False).status_code == 302


def test_removing_an_owner_signs_them_out(client: TestClient, owner: str, session: Session) -> None:
    log_in(client, owner, PASSWORD)

    admin_accounts.remove(session, owner)

    assert client.get("/admin/", follow_redirects=False).status_code == 302


def test_a_forged_session_cookie_is_ignored(client: TestClient, owner: str) -> None:
    """The cookie is signed: one made without the secret key doesn't count."""
    log_in(client, owner, PASSWORD)
    client.cookies.set("makarios_admin", "eyJ1c2VyX2lkIjogMX0=.forged.signature", path="/admin")

    assert client.get("/admin/", follow_redirects=False).status_code == 302


def test_the_sixth_failure_is_refused_even_with_the_right_password(
    client: TestClient, owner: str
) -> None:
    for _ in range(5):
        assert log_in(client, owner, "wrong guess").status_code == 400

    refused = log_in(client, owner, PASSWORD)

    assert refused.status_code == 429
    assert "Try again in 15 minutes" in refused.text


def test_the_refusal_lifts_once_the_window_passes(
    client: TestClient, owner: str, clock: FakeClock
) -> None:
    for _ in range(5):
        log_in(client, owner, "wrong guess")

    clock.now += 15 * 60 + 1

    assert log_in(client, owner, PASSWORD).status_code == 302


def test_a_made_up_forwarded_address_does_not_escape_the_throttle(
    client: TestClient, owner: str
) -> None:
    """A guesser can fill the start of X-Forwarded-For; the proxy adds the real address last."""
    for attempt in range(5):
        forwarded = f"10.0.0.{attempt}, 203.0.113.7"
        assert log_in(client, owner, "wrong guess", forwarded).status_code == 400

    assert log_in(client, owner, PASSWORD, "10.0.0.99, 203.0.113.7").status_code == 429


def test_a_second_x_forwarded_for_header_does_not_escape_the_throttle(
    client: TestClient, owner: str
) -> None:
    """The real address may arrive on its own line, after any the visitor sent."""
    headers = [("x-forwarded-for", "10.0.0.1"), ("x-forwarded-for", "203.0.113.7")]
    for _ in range(5):
        client.post(
            "/admin/login",
            data={"username": owner, "password": "wrong guess"},
            headers=httpx.Headers(headers),
        )

    refused = client.post(
        "/admin/login",
        data={"username": owner, "password": PASSWORD},
        headers=httpx.Headers([("x-forwarded-for", "10.0.0.2"), headers[1]]),
    )

    assert refused.status_code == 429


def test_visitors_at_different_addresses_are_counted_apart(client: TestClient, owner: str) -> None:
    for _ in range(5):
        log_in(client, owner, "wrong guess", "203.0.113.7")

    assert log_in(client, owner, PASSWORD, "203.0.113.8").status_code == 302


def request_with(forwarded_for: str | None) -> Request:
    headers = [(b"x-forwarded-for", forwarded_for.encode())] if forwarded_for else []
    return Request({"type": "http", "headers": headers, "client": ("198.51.100.1", 1234)})


@pytest.mark.parametrize(
    "forwarded_for, proxy_hops, expected",
    [
        ("203.0.113.7", 1, "203.0.113.7"),
        ("9.9.9.9, 203.0.113.7", 1, "203.0.113.7"),
        ("9.9.9.9, 203.0.113.7, 172.68.0.1", 1, "172.68.0.1"),
        ("9.9.9.9, 203.0.113.7, 172.68.0.1", 2, "203.0.113.7"),
        # Fewer entries than hops: every one of them came from our proxies.
        ("203.0.113.7", 2, "203.0.113.7"),
        # No header at all: not behind a proxy, as in development.
        (None, 1, "198.51.100.1"),
    ],
)
def test_client_address_counts_from_the_end(
    forwarded_for: str | None, proxy_hops: int, expected: str
) -> None:
    assert client_address(request_with(forwarded_for), proxy_hops) == expected


def test_production_cookies_are_locked_down(
    session_maker: Callable[[], Session], clock: FakeClock, owner: str
) -> None:
    client = admin_client(session_maker, clock, production_settings())

    cookie = log_in(client, owner, PASSWORD).headers["set-cookie"].lower()

    assert cookie.startswith("makarios_admin=")
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie
    assert "path=/admin" in cookie


def test_development_cookies_work_over_plain_http(client: TestClient, owner: str) -> None:
    cookie = log_in(client, owner, PASSWORD).headers["set-cookie"].lower()

    assert "secure" not in cookie


def test_an_owner_can_edit_a_watch(client: TestClient, owner: str, session: Session) -> None:
    watch = session.scalars(select(Watch).order_by(Watch.id)).first()
    assert watch is not None
    log_in(client, owner, PASSWORD)

    form = edit_form(client.get(f"/admin/watch/edit/{watch.id}").text)
    form["price"] = "12345"
    response = client.post(f"/admin/watch/edit/{watch.id}", data=form, follow_redirects=False)

    assert response.status_code == 302
    session.refresh(watch)
    assert watch.price == 12345


def test_the_edit_form_leaves_out_the_slug_and_photos(
    client: TestClient, owner: str, session: Session
) -> None:
    """The slug is the watch's address on the site, and photos wait for upload."""
    log_in(client, owner, PASSWORD)

    form = edit_form(client.get("/admin/watch/edit/1").text)

    assert "slug" not in form
    assert "photos" not in form
    assert {"brand", "model", "price", "status", "featured"} <= form.keys()


def test_owners_cannot_create_or_delete_watches_yet(client: TestClient, owner: str) -> None:
    """Adding and removing watches are their own stories, still to come."""
    log_in(client, owner, PASSWORD)

    assert client.get("/admin/watch/create").status_code in (403, 404)


def edit_form(html: str) -> dict[str, str]:
    """The edit form's fields and their current values, as a browser would submit them."""

    class FormReader(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.fields: dict[str, str] = {}
            self._select: str | None = None
            self._textarea: str | None = None

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            a = dict(attrs)
            name = a.get("name")
            if tag == "input" and name:
                kind = a.get("type", "text")
                if kind == "checkbox":
                    if "checked" in a:
                        self.fields[name] = a.get("value") or "y"
                elif kind not in ("submit", "button"):
                    self.fields[name] = a.get("value") or ""
            elif tag == "select" and name:
                self._select = name
            elif tag == "option" and self._select and "selected" in a:
                self.fields[self._select] = a.get("value") or ""
            elif tag == "textarea" and name:
                self._textarea = name
                self.fields[name] = ""

        def handle_endtag(self, tag: str) -> None:
            if tag == "select":
                self._select = None
            elif tag == "textarea":
                self._textarea = None

        def handle_data(self, data: str) -> None:
            if self._textarea:
                self.fields[self._textarea] += data

    reader = FormReader()
    reader.feed(html)
    return reader.fields
