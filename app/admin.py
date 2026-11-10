"""The owners' admin area at /admin: SQLAdmin's inventory screens behind our own login.

SQLAdmin builds the list and edit pages from the models. The login is the part
written here, in AdminAuth: SQLAdmin calls its login, logout and authenticate
methods, and leaves what they check up to us.

SQLAdmin brings its own CSS and JavaScript (Tabler and jQuery). The
storefront's no-framework rule is about what buyers download; the admin is two
owners' tool, not a page buyers ever load.
"""

import enum
import logging
from collections.abc import Callable
from datetime import date
from typing import Any

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.audit import AuditBackend, AuditEntry
from sqladmin.authentication import AuthenticationBackend, get_current_user_id
from sqladmin.fields import SelectField
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response
from wtforms import Field, Form, IntegerField, ValidationError, validators
from wtforms.widgets import TextInput

from app.config import Settings
from app.models import AdminUser, BoxPapers, Condition, Watch, WatchStatus
from app.services import admin_accounts, inventory
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
        self.proxy_hops = settings.proxy_hops
        # Set by mount_admin, which creates the Admin this backend serves; the
        # refusal page renders with its templates.
        self.admin: Admin | None = None

    async def login(self, request: Request) -> Response | bool:
        address = client_address(request, self.proxy_hops)
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
            # The full header too, for checking proxy_hops against what the
            # host really sends (see docs/DEPLOY.md).
            audit_log.warning(
                "admin login failed address=%s forwarded=%r",
                address,
                request.headers.getlist("x-forwarded-for"),
            )
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


def client_address(request: Request, proxy_hops: int) -> str:
    """The visitor's IP address, counted from the end of X-Forwarded-For.

    Each proxy a request passes through adds the address it saw to the END of
    this header, and keeps whatever was there already. So a visitor can fill
    the start with anything, and only the last proxy_hops entries are ours.
    The entry at that position is the address our outermost proxy saw.

    request.client won't do here: the server rewrites it from the header's
    FIRST entry, which is the visitor's to choose. Throttling on that would let
    a guesser send a new made-up address with every attempt and never be refused.

    A proxy_hops that's too small errs safely: everyone behind one proxy shares
    a count. Too large, and the visitor picks their own address.
    """
    forwarded = [
        address.strip()
        for header in request.headers.getlist("x-forwarded-for")
        for address in header.split(",")
        if address.strip()
    ]
    if forwarded:
        return forwarded[-min(proxy_hops, len(forwarded))]
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


# Wristwatches were rare before 1900, and a year beyond next year is a typo.
EARLIEST_YEAR = 1900


def strip(value: Any) -> Any:
    """A form filter: drop the spaces a phone keyboard leaves around a word."""
    return value.strip() if isinstance(value, str) else value


def sensible_year(form: Form, field: Field) -> None:
    """A year from 1900 to next year (a new model can carry next year's date).

    Checked against today's date on every save, rather than a year fixed when
    the app started, so the range moves forward on its own.
    """
    if field.data is None:
        return  # Left blank: the year isn't documented.
    latest = date.today().year + 1
    if not EARLIEST_YEAR <= field.data <= latest:
        raise ValidationError(f"Enter a year from {EARLIEST_YEAR} to {latest}.")


PRICE_MESSAGE = "Enter a whole-dollar price above zero, like 12500, or leave it blank."


class WholeDollarField(IntegerField):
    """A price in whole US dollars, typed the way people write one.

    "12500", "12,500" and "$12,500" all mean 12500. Cents, a zero or a
    negative are refused with one plain message, rather than WTForms' "Not a
    valid integer value". Blank is allowed, and means price on request.
    """

    widget = TextInput()

    def process_formdata(self, valuelist: list[Any]) -> None:
        self.data = None
        text = str(valuelist[0]).strip() if valuelist else ""
        if not text:
            return
        digits = text.removeprefix("$").replace(",", "")
        if not (digits.isascii() and digits.isdigit()) or int(digits) < 1:
            raise ValueError(PRICE_MESSAGE)
        self.data = int(digits)


def enum_name(value: Any) -> str:
    """What a select stores for a member: its name (VERY_GOOD), as the database does."""
    return value.name if isinstance(value, enum.Enum) else str(value)


def labelled_choices(enum_class: type[enum.Enum]) -> dict[str, Any]:
    """A select that shows each member's label ("Very Good") but stores its name."""
    return {
        "choices": [(member.name, member.value) for member in enum_class],
        "coerce": enum_name,
    }


def watch_form_args() -> dict[str, dict[str, Any]]:
    """The admin's checks for each field, shown beside the field when they fail.

    SQLAdmin already requires the columns that can't be empty and lets the rest
    be blank; these add what it can't tell from the columns. DataRequired,
    unlike SQLAdmin's InputRequired, also refuses a field of nothing but spaces.

    A function, so every field gets lists of its own each time: SQLAdmin builds
    the form on every request and appends its own validators to these lists.
    Shared lists would pass one field's checks to another, and grow forever.
    """

    def text() -> dict[str, Any]:
        return {"filters": [strip], "validators": [validators.DataRequired(message="Required.")]}

    return {
        "brand": text(),
        "model": text(),
        "reference": text(),
        "year": {
            "description": "Leave blank if the year isn't documented.",
            "validators": [sensible_year],
        },
        "price": {"description": "Leave blank for price on request."},
        "condition": labelled_choices(Condition),
        "box_papers": labelled_choices(BoxPapers),
        "status": labelled_choices(WatchStatus),
    }


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

    # The slug is the watch's address on the site, so it's generated when the
    # watch is added and never edited. Photos wait for upload (#68); the
    # listing date is set once, by the database.
    form_excluded_columns = [Watch.slug, Watch.photos, Watch.listed_at]
    form_overrides = {
        "price": WholeDollarField,
        "condition": SelectField,
        "box_papers": SelectField,
        "status": SelectField,
    }
    # A phone shows its number pad for the price.
    form_widget_args = {"price": {"inputmode": "numeric", "placeholder": "Price on request"}}

    @property
    def form_args(self) -> dict[str, dict[str, Any]]:  # type: ignore[override]
        return watch_form_args()

    can_create = True
    # Removing a watch is its own story; a sold watch is marked sold instead.
    can_delete = False
    can_export = False

    async def on_model_change(
        self, data: dict[str, Any], model: Watch, is_created: bool, request: Request
    ) -> None:
        """Give a new watch its slug, before SQLAdmin saves it.

        SQLAdmin calls this on the event loop, so the database lookup runs on
        the thread pool, like every other blocking call in the admin.
        """
        if is_created:
            model.slug = await run_in_threadpool(self._new_slug, data["brand"], data["model"])

    def _new_slug(self, brand: str, model: str) -> str:
        with self.session_maker() as session:
            return inventory.new_slug(session, brand, model)


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
