"""Photo upload (#68): the media store, the photos service, and the admin's photos page.

Every test writes to its own temporary media folder, never to the repo's media/.
"""

import io
import logging
import re
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.admin import mount_admin
from app.config import Settings
from app.main import app as real_app
from app.models import Photo, Watch
from app.paths import STATIC_DIR
from app.services import admin_accounts, images
from app.services import photos as photo_service
from app.services.images import WIDTHS, PhotoRejected, file_name
from app.services.media import CACHE_FOREVER, MediaStore, mount_media
from tests.conftest import production_settings

PASSWORD = "correct horse battery staple"


def jpeg(colour: tuple[int, int, int] = (30, 180, 60)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1600, 2000), colour).save(buffer, "JPEG")
    return buffer.getvalue()


@pytest.fixture
def media(tmp_path: Path) -> Path:
    return tmp_path / "media"


@pytest.fixture
def store(media: Path) -> MediaStore:
    return MediaStore(media)


@pytest.fixture
def session_maker(engine: Engine) -> Callable[[], Session]:
    return sessionmaker(engine, expire_on_commit=False)


def build_client(
    session_maker: Callable[[], Session], settings: Settings, base_url: str = "http://testserver"
) -> TestClient:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    mount_media(app, settings.media_dir)
    mount_admin(app, settings, session_maker)
    client = TestClient(app, base_url=base_url)
    client.post("/admin/login", data={"username": "owner", "password": PASSWORD})
    return client


@pytest.fixture
def client(session: Session, session_maker: Callable[[], Session], media: Path) -> TestClient:
    admin_accounts.set_password(session, "owner", PASSWORD)
    return build_client(session_maker, Settings(_env_file=None, media_dir=media))


@pytest.fixture
def watch(session: Session) -> Watch:
    """A placeholder watch with no photos of its own yet."""
    watch = Watch(
        slug="halden-fjord-diver",
        brand="Halden",
        model="Fjord Diver",
        reference="HF-200",
        condition="EXCELLENT",
        box_papers="WATCH_ONLY",
    )
    session.add(watch)
    session.commit()
    return watch


def page_url(watch: Watch) -> str:
    return f"/admin/watch/{watch.id}/photos"


def upload(
    client: TestClient, watch: Watch, alt: str = "Front, in daylight", data: bytes | None = None
) -> httpx.Response:
    return client.post(
        page_url(watch),
        data={"action": "add", "alt": alt},
        files={"photo": ("watch.jpg", data if data is not None else jpeg(), "image/jpeg")},
        follow_redirects=False,
    )


def act(client: TestClient, watch: Watch, action: str, photo_id: int) -> httpx.Response:
    return client.post(
        page_url(watch),
        data={"action": action, "photo_id": str(photo_id)},
        follow_redirects=False,
    )


def stored_photos(session: Session, watch: Watch) -> list[Photo]:
    session.expire_all()
    return list(
        session.scalars(select(Photo).where(Photo.watch_id == watch.id).order_by(Photo.position))
    )


def webp_files(media: Path) -> list[str]:
    return sorted(path.name for path in media.rglob("*.webp"))


# The media store.


def test_the_store_writes_every_width_and_deletes_them(store: MediaStore, media: Path) -> None:
    name = store.save(images.process_photo(jpeg()))

    assert re.fullmatch(r"uploads/[0-9a-f]{16}", name)
    assert webp_files(media) == sorted(file_name(name.split("/")[1], width) for width in WIDTHS)
    assert store.exists(name)
    assert not list(media.rglob("*.partial"))

    store.delete(name)

    assert webp_files(media) == []


@pytest.mark.parametrize(
    "name", ["uploads/../../app/main", "placeholder/watch-01", "uploads/NOTHEX0000000000"]
)
def test_the_store_refuses_to_delete_anything_it_did_not_name(store: MediaStore, name: str) -> None:
    """A bad value in the database must never point delete() at another file."""
    with pytest.raises(ValueError, match="not an uploaded photo"):
        store.delete(name)


def test_media_files_are_cached_for_a_year(client: TestClient, store: MediaStore) -> None:
    name = store.save(images.process_photo(jpeg()))

    response = client.get(f"/media/{file_name(name, 400)}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert response.headers["cache-control"] == CACHE_FOREVER


@pytest.mark.parametrize("path", ["/media/uploads/x.webp.partial", "/media/../app/main.py"])
def test_media_serves_only_finished_webp_files(
    client: TestClient, store: MediaStore, path: str
) -> None:
    store.save(images.process_photo(jpeg()))

    assert client.get(path).status_code == 404


def test_media_before_the_first_upload_is_a_404_not_an_error(client: TestClient) -> None:
    """A fresh volume has no media folder until the first photo is saved."""
    assert client.get("/media/uploads/0123456789abcdef-400.webp").status_code == 404


@pytest.mark.parametrize(
    "settings, ready",
    [
        (Settings(_env_file=None), True),
        (production_settings(), False),
        (production_settings(media_dir=Path("/data/media")), True),
    ],
    ids=["development", "production-without-volume", "production-on-volume"],
)
def test_photo_storage_is_ready_only_where_photos_survive_a_deploy(
    settings: Settings, ready: bool
) -> None:
    assert settings.photo_storage_ready is ready


# The photos service.


def test_a_photo_needs_a_description(session: Session, store: MediaStore, watch: Watch) -> None:
    with pytest.raises(PhotoRejected, match="Describe the photo"):
        photo_service.add_photo(session, store, watch, jpeg(), "   ")

    assert webp_files(store.root) == []


def test_a_refused_file_stores_nothing(session: Session, store: MediaStore, watch: Watch) -> None:
    with pytest.raises(PhotoRejected, match="isn't a photo"):
        photo_service.add_photo(session, store, watch, b"not a photo", "Front")

    assert webp_files(store.root) == []
    assert stored_photos(session, watch) == []


def test_files_are_removed_if_the_photo_cannot_be_saved(
    session: Session, store: MediaStore, watch: Watch, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_commit() -> None:
        raise RuntimeError("database went away")

    monkeypatch.setattr(session, "commit", failing_commit)

    with pytest.raises(RuntimeError):
        photo_service.add_photo(session, store, watch, jpeg(), "Front")

    assert webp_files(store.root) == []


def test_deleting_a_placeholder_photo_leaves_its_files(session: Session, store: MediaStore) -> None:
    """Placeholder images belong to the repository, not to the media store."""
    watch = session.get(Watch, 1)
    assert watch is not None
    placeholder = watch.photos[0]

    photo_service.delete_photo(session, store, watch, placeholder.id)

    assert (STATIC_DIR / "img" / file_name(placeholder.image, 400)).exists()


# The admin's photos page.


def test_the_photos_page_needs_a_login(session_maker: Callable[[], Session], watch: Watch) -> None:
    app = FastAPI()
    mount_admin(app, Settings(_env_file=None), session_maker)

    response = TestClient(app).get(page_url(watch), follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"].endswith("/admin/login")


def test_the_watch_list_links_to_each_watch_s_photos(client: TestClient, watch: Watch) -> None:
    assert f'<a href="{page_url(watch)}">Photos</a>' in client.get("/admin/watch/list").text


def test_saving_a_new_watch_goes_to_its_photos(client: TestClient, session: Session) -> None:
    fields = {
        "brand": "Norvell",
        "model": "Deepline 500",
        "reference": "ND-500",
        "condition": "GOOD",
        "box_papers": "WATCH_ONLY",
        "status": "AVAILABLE",
    }

    saved = client.post("/admin/watch/create", data=fields | {"save": "Save"})
    another = client.post(
        "/admin/watch/create",
        data=fields | {"save": "Save and add another"},
        follow_redirects=False,
    )

    query = select(Watch).where(Watch.reference == "ND-500").order_by(Watch.id)
    [first, _] = session.scalars(query)
    assert saved.url.path == page_url(first)
    assert "No photos yet" in saved.text
    assert another.headers["location"].endswith("/admin/watch/create")


def test_an_owner_can_upload_a_photo(
    client: TestClient,
    session: Session,
    watch: Watch,
    media: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="makarios.admin.audit")

    response = upload(client, watch, alt="  Front,   in daylight ")

    assert response.status_code == 303
    page = client.get(response.headers["location"])
    assert "Photo added." in page.text
    [photo] = stored_photos(session, watch)
    assert photo.alt == "Front, in daylight"
    assert photo.position == 0
    assert photo.is_upload
    assert len(webp_files(media)) == len(WIDTHS)
    assert f"/media/{file_name(photo.image, 400)}" in page.text
    [entry] = [r.getMessage() for r in caplog.records if "admin photo add" in r.getMessage()]
    assert "by=owner" in entry


def test_a_photo_without_a_description_is_refused(
    client: TestClient, session: Session, watch: Watch, media: Path
) -> None:
    response = upload(client, watch, alt="")

    assert response.status_code == 400
    assert "Describe the photo" in response.text
    assert stored_photos(session, watch) == []
    assert webp_files(media) == []


def test_a_file_that_is_not_a_photo_is_refused_on_the_page(
    client: TestClient, watch: Watch
) -> None:
    response = upload(client, watch, alt="Front", data=b"%PDF-1.7 not a photo")

    assert response.status_code == 400
    assert "Upload a JPEG, PNG or WebP" in response.text
    # What the owner typed is kept, so only the file needs choosing again.
    assert 'value="Front"' in response.text


def test_an_oversized_upload_is_refused_before_it_is_read(
    client: TestClient, watch: Watch, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(images, "MAX_UPLOAD_BYTES", 1024)

    response = upload(client, watch, data=b"\0" * 200_000)

    assert response.status_code == 413
    assert "too big" in response.text


def test_choosing_no_file_is_refused(client: TestClient, watch: Watch) -> None:
    response = client.post(page_url(watch), data={"action": "add", "alt": "Front"})

    assert response.status_code == 400
    assert "Choose a photo" in response.text


def test_photos_can_be_reordered_and_the_first_is_on_the_cards(
    client: TestClient, session: Session, watch: Watch
) -> None:
    upload(client, watch, alt="Front")
    upload(client, watch, alt="Back", data=jpeg((30, 60, 220)))
    front, back = stored_photos(session, watch)

    moved = act(client, watch, "up", back.id)

    assert moved.status_code == 303
    assert [photo.alt for photo in stored_photos(session, watch)] == ["Back", "Front"]
    session.refresh(watch)
    assert watch.primary_photo is not None
    assert watch.primary_photo.alt == "Back"
    # The first photo can't move further up: nothing changes.
    act(client, watch, "up", back.id)
    assert [photo.position for photo in stored_photos(session, watch)] == [0, 1]


def test_deleting_a_photo_removes_its_files_and_closes_the_gap(
    client: TestClient, session: Session, watch: Watch, media: Path
) -> None:
    for alt in ("Front", "Back", "Clasp"):
        upload(client, watch, alt=alt)
    front, _, _ = stored_photos(session, watch)
    front_id, front_token = front.id, front.image.removeprefix("uploads/")

    response = act(client, watch, "delete", front_id)

    assert response.status_code == 303
    remaining = stored_photos(session, watch)
    assert [(photo.alt, photo.position) for photo in remaining] == [("Back", 0), ("Clasp", 1)]
    assert len(webp_files(media)) == 2 * len(WIDTHS)
    assert not any(front_token in name for name in webp_files(media))


def test_another_watch_s_photo_cannot_be_changed_from_this_page(
    client: TestClient, session: Session, watch: Watch
) -> None:
    other = session.get(Watch, 1)
    assert other is not None

    assert act(client, watch, "delete", other.photos[0].id).status_code == 404
    assert act(client, watch, "delete", 999_999).status_code == 404


def test_an_unknown_watch_has_no_photos_page(client: TestClient) -> None:
    assert client.get("/admin/watch/999999/photos").status_code == 404


def test_uploads_are_off_when_storage_would_not_survive_a_deploy(
    session: Session, session_maker: Callable[[], Session], watch: Watch, tmp_path: Path
) -> None:
    """Production with MAKARIOS_MEDIA_DIR unset: refuse rather than lose photos at a deploy."""
    admin_accounts.set_password(session, "owner", PASSWORD)
    settings = production_settings(media_dir=Path("media"))
    client = build_client(session_maker, settings, base_url="https://testserver")

    page = client.get(page_url(watch))
    refused = upload(client, watch)

    assert "Photo storage isn't set up" in page.text
    assert 'type="file"' not in page.text
    assert refused.status_code == 503
    assert stored_photos(session, watch) == []


def test_uploads_are_off_when_the_folder_cannot_be_written(
    client: TestClient, session: Session, watch: Watch, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Railway volume is root's until set up; say so rather than fail mid-upload."""
    monkeypatch.setattr(MediaStore, "writable", lambda self: False)

    page = client.get(page_url(watch))
    refused = upload(client, watch)

    assert "write to its photo folder" in page.text
    assert refused.status_code == 503
    assert stored_photos(session, watch) == []


def test_the_store_is_not_writable_when_its_folder_cannot_be_made(tmp_path: Path) -> None:
    blocker = tmp_path / "a-file"
    blocker.write_text("not a folder")

    assert not MediaStore(blocker / "media").writable()
    assert MediaStore(tmp_path / "media").writable()


def test_an_uploaded_photo_is_served_from_media_on_the_landing_page(
    session: Session,
) -> None:
    watch = session.get(Watch, 1)
    assert watch is not None
    watch.photos.insert(0, Photo(image="uploads/0123456789abcdef", alt="The real piece"))
    for position, photo in enumerate(watch.photos):
        photo.position = position
    session.commit()

    landing = TestClient(real_app).get("/").text

    assert "/media/uploads/0123456789abcdef-400.webp 400w" in landing
    assert "/media/uploads/0123456789abcdef-1200.webp 1200w" in landing
    assert 'alt="The real piece"' in landing
