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
from typing import Any, ClassVar

from fastapi import FastAPI
from markupsafe import Markup
from sqladmin import Admin, BaseView, ModelView, expose
from sqladmin.audit import AuditBackend, AuditEntry
from sqladmin.authentication import AuthenticationBackend, get_current_user_id
from sqladmin.fields import SelectField
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from wtforms import Field, Form, IntegerField, ValidationError, validators
from wtforms.widgets import TextInput

from app.config import Settings
from app.models import AdminUser, BoxPapers, Condition, Photo, Watch, WatchStatus
from app.paths import TEMPLATES_DIR
from app.services import admin_accounts, images, inventory
from app.services import photos as photo_service
from app.services.login_throttle import LoginThrottle
from app.services.media import MediaStore

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
        Watch.slug,
    ]
    # The last column links to the watch's photos page, the one way in, since
    # SQLAdmin's own edit form has no place for files. It's the slug column
    # relabelled: a relationship column like Watch.photos would make SQLAdmin
    # treat the link as a list of photos, one link per character.
    column_formatters = {Watch.slug: lambda watch, _: photos_link(watch)}
    column_labels = {Watch.slug: "Photos"}
    column_searchable_list = [Watch.brand, Watch.model, Watch.reference]
    column_default_sort = [(Watch.listed_at, True)]

    # The slug is the watch's address on the site, so it's generated when the
    # watch is added and never edited. Photos have their own page
    # (WatchPhotosAdmin); the listing date is set once, by the database.
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

    async def after_model_change(
        self, data: dict[str, Any], model: Watch, is_created: bool, request: Request
    ) -> Response | None:
        """After adding a watch with plain Save, go straight to its photos.

        A new listing needs photos next, and this saves an owner on a phone
        from finding the watch in the list first. "Save and add another" and
        "Save and continue editing" do what they say.
        """
        form = await request.form()
        if is_created and form.get("save") == "Save":
            return RedirectResponse(photos_url(request, model.id), status_code=302)
        return None


def photos_url(request: Request, watch_id: int) -> str:
    return str(request.url_for("admin:view-watch-photos", watch_id=watch_id))


def thumbnail_url(request: Request, photo: Photo) -> str:
    """The photo's smallest file, as responsive_img's image_url() would build it."""
    folder = "" if photo.is_upload else "img/"
    path = folder + images.file_name(photo.image, images.WIDTHS[0])
    return str(request.url_for(photo.mount, path=path))


def photos_link(watch: Watch) -> Markup:
    # A formatter gets no request to build a URL from, so this one is written
    # out; mount_admin always mounts the admin at /admin.
    return Markup('<a href="/admin/watch/{}/photos">Photos</a>').format(watch.id)


# What the photos page says after each change, keyed by ?done= in the redirect.
PHOTO_NOTICES = {
    "added": "Photo added.",
    "moved": "Order saved. The first photo is the one the cards show.",
    "deleted": "Photo deleted.",
}

# Room for the form's other fields and the multipart boundaries around the file.
FORM_OVERHEAD_BYTES = 64 * 1024


class WatchPhotosAdmin(BaseView):
    """The photos page for one watch: add, reorder and delete its photos.

    Plain HTML forms, so it works with JavaScript off and on a phone. Each
    change is a POST that redirects back to the page (post/redirect/get), so
    refreshing never re-submits an upload.

    mount_admin makes a subclass with the store, the session factory and
    whether storage is ready, because SQLAdmin creates the view itself, with
    no arguments.
    """

    name = "Photos"
    icon = "fa-solid fa-camera"

    store: ClassVar[MediaStore]
    session_maker: ClassVar[Callable[[], Session]]
    storage_ready: ClassVar[bool]

    def is_visible(self, request: Request) -> bool:
        # Not in the sidebar: it's reached from a watch, never on its own.
        return False

    @expose("/watch/{watch_id:int}/photos", methods=["GET", "POST"], identity="watch-photos")
    async def photos(self, request: Request) -> Response:
        watch_id: int = request.path_params["watch_id"]
        if request.method == "GET":
            notice = PHOTO_NOTICES.get(request.query_params.get("done", ""))
            return await self._page(request, watch_id, notice=notice)

        if await self._storage_problem() is not None:
            return await self._page(request, watch_id, status=503)

        # Checked before the body is read, so an oversized upload is refused
        # without first being written to a temporary file.
        length = int(request.headers.get("content-length") or 0)
        if length > images.MAX_UPLOAD_BYTES + FORM_OVERHEAD_BYTES:
            limit = images.MAX_UPLOAD_BYTES // (1024 * 1024)
            error = f"That file is too big. Photos can be up to {limit} MB."
            return await self._page(request, watch_id, error=error, status=413)

        form = await request.form()
        action = form.get("action")
        who = get_current_user_id(request)
        try:
            if action == "add":
                upload = form.get("photo")
                alt = str(form.get("alt") or "")
                if not isinstance(upload, UploadFile) or not upload.filename:
                    raise images.PhotoRejected("Choose a photo to add.")
                data = await upload.read(images.MAX_UPLOAD_BYTES + 1)
                photo_id = await run_in_threadpool(self._add, watch_id, data, alt)
                audit_log.info("admin photo add watch=%s photo=%s by=%s", watch_id, photo_id, who)
                done = "added"
            elif action in ("up", "down", "delete"):
                photo_id = int(str(form.get("photo_id")))
                await run_in_threadpool(self._change, watch_id, photo_id, action)
                audit_log.info(
                    "admin photo %s watch=%s photo=%s by=%s", action, watch_id, photo_id, who
                )
                done = "deleted" if action == "delete" else "moved"
            else:
                return Response("Unknown action.", status_code=400)
        except images.PhotoRejected as rejected:
            alt = str(form.get("alt") or "")
            return await self._page(request, watch_id, error=str(rejected), alt=alt, status=400)
        except (ValueError, photo_service.PhotoNotFound):
            return Response("No such photo.", status_code=404)

        return RedirectResponse(f"{photos_url(request, watch_id)}?done={done}", status_code=303)

    async def _page(
        self,
        request: Request,
        watch_id: int,
        *,
        error: str | None = None,
        notice: str | None = None,
        alt: str = "",
        status: int = 200,
    ) -> Response:
        watch = await run_in_threadpool(self._load, watch_id)
        context = {
            "watch": watch,
            "photos": [
                {
                    "id": photo.id,
                    "alt": photo.alt,
                    "thumb": thumbnail_url(request, photo),
                }
                for photo in watch.photos
            ],
            "storage_problem": await self._storage_problem(),
            "max_megabytes": images.MAX_UPLOAD_BYTES // (1024 * 1024),
            "max_alt": photo_service.MAX_ALT_LENGTH,
            "min_size": f"{images.WIDTHS[-1]}×{images.height_for(images.WIDTHS[-1])}",
            "error": error,
            "notice": notice,
            "alt": alt,
            "edit_url": request.url_for("admin:edit", identity="watch", pk=watch.id),
        }
        return await self.templates.TemplateResponse(
            request, "watch_photos.html", context, status_code=status
        )

    async def _storage_problem(self) -> str | None:
        """Why uploads are off, or None: "unset" (no volume configured) or "unwritable"."""
        if not self.storage_ready:
            return "unset"
        if not await run_in_threadpool(self.store.writable):
            return "unwritable"
        return None

    def _load(self, watch_id: int) -> Watch:
        with self.session_maker() as session:
            query = select(Watch).where(Watch.id == watch_id).options(selectinload(Watch.photos))
            watch = session.scalars(query).one_or_none()
            if watch is None:
                raise HTTPException(status_code=404)
            return watch

    def _add(self, watch_id: int, data: bytes, alt: str) -> int:
        with self.session_maker() as session:
            watch = self._watch(session, watch_id)
            return photo_service.add_photo(session, self.store, watch, data, alt).id

    def _change(self, watch_id: int, photo_id: int, action: str) -> None:
        with self.session_maker() as session:
            watch = self._watch(session, watch_id)
            if action == "delete":
                photo_service.delete_photo(session, self.store, watch, photo_id)
            else:
                photo_service.move_photo(session, watch, photo_id, -1 if action == "up" else 1)

    @staticmethod
    def _watch(session: Session, watch_id: int) -> Watch:
        watch = session.get(Watch, watch_id)
        if watch is None:
            raise HTTPException(status_code=404)
        return watch


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
        # Our own admin pages (the photos page); SQLAdmin's templates come after.
        templates_dir=str(TEMPLATES_DIR / "admin"),
    )
    auth.admin = admin
    admin.add_view(WatchAdmin)
    # A subclass per app, so two apps (as in the tests) never share a store.
    photos_view = type(
        "WatchPhotosAdmin",
        (WatchPhotosAdmin,),
        {
            "store": MediaStore(settings.media_dir),
            "session_maker": staticmethod(session_maker),
            "storage_ready": settings.photo_storage_ready,
        },
    )
    admin.add_view(photos_view)
    return admin
