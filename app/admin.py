"""The owners' admin area at /admin: SQLAdmin's inventory screens behind our own login.

SQLAdmin builds the list and edit pages from the models. The login is the part
written here, in AdminAuth: SQLAdmin calls its login, logout and authenticate
methods, and leaves what they check up to us.

SQLAdmin brings its own CSS and JavaScript (Tabler and jQuery). The
storefront's no-framework rule is about what buyers download; the admin is two
owners' tool, not a page buyers ever load.
"""

import logging
from collections.abc import Callable

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.audit import AuditBackend, AuditEntry
from sqladmin.authentication import AuthenticationBackend, get_current_user_id
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response

from app.config import Settings
from app.models import AdminUser, Watch
from app.services import admin_accounts
from app.services.login_throttle import LoginThrottle

# A day without a request signs the owner out. Each admin request re-signs the
# cookie, so the day counts from the last use, not from the login.
SESSION_MAX_AGE_SECONDS = 24 * 60 * 60

audit_log = logging.getLogger("makarios.admin.audit")


class AdminAuth(AuthenticationBackend):
    """Checks the owners' logins, and the session every admin page needs.

    The session lives in Starlette's session cookie, which is signed with the
    secret key: the browser can read it but not change it without breaking the
    signature. It holds the owner's account id and a stamp of their password
    (see admin_accounts.session_stamp), never the password.

    SQLAdmin's hooks are async, while the database and Argon2 are blocking, so
    that work runs on the thread pool, as FastAPI does for a plain `def` route.
    Run on the event loop instead, each 50 ms password check would stall every
    other request.
    """

    def __init__(
        self,
        settings: Settings,
        session_maker: Callable[[], Session],
        throttle: LoginThrottle,
    ) -> None:
        super().__init__(
            secret_key=settings.secret_key,
            session_cookie="makarios_admin",
            max_age=SESSION_MAX_AGE_SECONDS,
            # The browser only sends the cookie to /admin pages, so the
            # storefront never sees it.
            path="/admin",
            # Not sent with requests other sites start, such as a form on
            # another site posting to /admin. SQLAdmin's forms have no CSRF
            # token, so this is what stops that.
            same_site="lax",
            # Only over HTTPS. Off in development, which runs on plain http.
            https_only=settings.is_production,
        )
        self.session_maker = session_maker
        self.throttle = throttle
        # Set by mount_admin, which creates the Admin this backend serves; the
        # refusal page renders with its templates.
        self.admin: Admin | None = None

    async def login(self, request: Request) -> Response | bool:
        address = client_address(request)
        if self.throttle.is_refused(address):
            return await self._refuse(request, address)

        form = await request.form()
        username = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))
        admin = await run_in_threadpool(self._check_login, username, password)

        if admin is None:
            self.throttle.record_failure(address)
            # Not the username: an owner who types their password into the
            # username box would otherwise put it in the log.
            audit_log.warning("admin login failed address=%s", address)
            return False

        self.throttle.reset(address)
        # A fresh session, so nothing from before the login carries into it.
        request.session.clear()
        request.session.update(
            {
                "user_id": admin.id,
                "username": admin.username,
                "stamp": admin_accounts.session_stamp(admin),
            }
        )
        audit_log.info("admin login username=%s address=%s", admin.username, address)
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Whether this request belongs to a signed-in owner whose account is unchanged.

        The account is looked up again on every request, so removing an owner
        or changing their password takes effect immediately rather than when
        the cookie expires.
        """
        user_id = request.session.get("user_id")
        stamp = request.session.get("stamp")
        if user_id is None or stamp is None:
            return False

        valid = await run_in_threadpool(self._session_is_current, user_id, stamp)
        if not valid:
            request.session.clear()
        return valid

    async def get_user_id(self, request: Request) -> str | None:
        """Who is acting, for the audit log: the username, which reads better than an id."""
        return request.session.get("username")

    def _check_login(self, username: str, password: str) -> AdminUser | None:
        with self.session_maker() as session:
            return admin_accounts.check_login(session, username, password)

    def _session_is_current(self, user_id: int, stamp: str) -> bool:
        with self.session_maker() as session:
            admin = session.get(AdminUser, user_id)
            return admin is not None and admin_accounts.session_stamp(admin) == stamp

    async def _refuse(self, request: Request, address: str) -> Response:
        minutes = -(-self.throttle.retry_after(address) // 60)  # rounded up
        audit_log.warning("admin login refused address=%s", address)
        assert self.admin is not None, "mount_admin sets this"
        return await self.admin.templates.TemplateResponse(
            request,
            "sqladmin/login.html",
            {"error": f"Too many failed attempts. Try again in {minutes} minutes."},
            status_code=429,
        )


def client_address(request: Request) -> str:
    """The visitor's IP address.

    Behind the host's proxy this is the address the proxy forwarded, because
    the server trusts its X-Forwarded-For header (see the Dockerfile).
    """
    return request.client.host if request.client else "unknown"


class NamedAuditBackend(AuditBackend):
    """Logs every change made in the admin, and which owner made it.

    SQLAdmin's own LoggingAuditBackend leaves out who acted, which is the
    point of each owner having an account. The log goes to the host's log
    stream, which keeps a limited history; a table would keep it for good.
    """

    async def log(self, entry: AuditEntry, request: Request) -> None:
        audit_log.info(
            "admin %s %s pk=%s by=%s changes=%s",
            entry.action,
            entry.identity,
            entry.pk,
            get_current_user_id(request),
            entry.changes,
        )


class WatchAdmin(ModelView, model=Watch):
    name = "Watch"
    name_plural = "Watches"
    icon = "fa-solid fa-clock"

    column_list = [
        Watch.brand,
        Watch.model,
        Watch.reference,
        Watch.price,
        Watch.status,
        Watch.featured,
    ]
    column_searchable_list = [Watch.brand, Watch.model, Watch.reference]
    column_default_sort = [(Watch.listed_at, True)]

    # The slug is the watch's address on the site, so it stays as it was
    # created. Photos wait for upload (Sprint 6); the listing date is set once.
    form_excluded_columns = [Watch.slug, Watch.photos, Watch.listed_at]

    # Adding and removing watches are their own stories, still to come.
    can_create = False
    can_delete = False
    can_export = False


def mount_admin(
    app: FastAPI,
    settings: Settings,
    session_maker: Callable[[], Session],
    throttle: LoginThrottle | None = None,
) -> Admin:
    auth = AdminAuth(settings, session_maker, throttle or LoginThrottle())
    admin = Admin(
        app,
        session_maker=session_maker,
        base_url="/admin",
        title="Makarios Admin",
        favicon_url="/static/img/brand/favicon.png",
        authentication_backend=auth,
        audit_backend=NamedAuditBackend(),
    )
    auth.admin = admin
    admin.add_view(WatchAdmin)
    return admin
