"""app/services/flags.py: flags read from a JSON file at request time, not at startup."""

import io
import json
import logging
from pathlib import Path

import pytest

from app.services import flags as flags_module
from app.services.flags import FlagFile


class FakeClock:
    """Time that moves only when a test says so, so the ttl can be crossed without sleeping."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def write_flags(path: Path, values: object) -> Path:
    path.write_text(json.dumps(values))
    return path


def test_without_a_source_every_flag_keeps_its_default() -> None:
    flags = FlagFile(None)

    assert flags.is_enabled("watch_detail_page", default=False) is False
    assert flags.is_enabled("watch_detail_page", default=True) is True


def test_a_flag_in_the_file_overrides_its_default(tmp_path: Path) -> None:
    source = write_flags(tmp_path / "flags.json", {"watch_detail_page": True})

    assert FlagFile(str(source)).is_enabled("watch_detail_page", default=False) is True


def test_a_flag_the_file_does_not_mention_keeps_its_default(tmp_path: Path) -> None:
    source = write_flags(tmp_path / "flags.json", {"something_else": True})

    assert FlagFile(str(source)).is_enabled("watch_detail_page", default=False) is False


def test_an_edit_takes_effect_once_the_ttl_has_passed(tmp_path: Path) -> None:
    """The point of the file: flip a flag by editing it, with no restart in between."""
    source = write_flags(tmp_path / "flags.json", {"watch_detail_page": False})
    clock = FakeClock()
    flags = FlagFile(str(source), ttl_seconds=30, clock=clock)
    assert flags.is_enabled("watch_detail_page", default=False) is False

    write_flags(source, {"watch_detail_page": True})
    clock.now = 29
    assert flags.is_enabled("watch_detail_page", default=False) is False  # still cached

    clock.now = 30
    assert flags.is_enabled("watch_detail_page", default=False) is True


def test_a_ttl_of_zero_reads_the_file_every_time(tmp_path: Path) -> None:
    source = write_flags(tmp_path / "flags.json", {"watch_detail_page": False})
    flags = FlagFile(str(source), ttl_seconds=0, clock=FakeClock())
    flags.is_enabled("watch_detail_page", default=False)

    write_flags(source, {"watch_detail_page": True})

    assert flags.is_enabled("watch_detail_page", default=False) is True


def test_a_missing_file_falls_back_to_the_default(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    flags = FlagFile(str(tmp_path / "no-such-file.json"))

    with caplog.at_level(logging.WARNING, logger="makarios.flags"):
        assert flags.is_enabled("watch_detail_page", default=False) is False
    assert "Keeping the last flag values" in caplog.text


@pytest.mark.parametrize("broken", ["{not json", "[true]", ""])
def test_a_broken_edit_keeps_the_last_values_that_read_cleanly(tmp_path: Path, broken: str) -> None:
    """A typo in the file mustn't switch a released feature back off, or crash the page."""
    source = write_flags(tmp_path / "flags.json", {"watch_detail_page": True})
    flags = FlagFile(str(source), ttl_seconds=0, clock=FakeClock())
    assert flags.is_enabled("watch_detail_page", default=False) is True

    source.write_text(broken)

    assert flags.is_enabled("watch_detail_page", default=False) is True


def test_a_value_that_is_not_a_boolean_is_ignored(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """ "false" as a string is truthy in Python, so a string must never count as on."""
    source = write_flags(tmp_path / "flags.json", {"watch_detail_page": "false"})

    with caplog.at_level(logging.WARNING, logger="makarios.flags"):
        assert FlagFile(str(source)).is_enabled("watch_detail_page", default=True) is True
    assert "is not true or false" in caplog.text


def test_a_failing_source_is_retried_once_per_ttl_not_every_request(tmp_path: Path) -> None:
    source = tmp_path / "flags.json"
    clock = FakeClock()
    flags = FlagFile(str(source), ttl_seconds=30, clock=clock)
    flags.is_enabled("watch_detail_page", default=False)  # missing: a failed read

    write_flags(source, {"watch_detail_page": True})
    assert flags.is_enabled("watch_detail_page", default=False) is False

    clock.now = 30
    assert flags.is_enabled("watch_detail_page", default=False) is True


def test_a_url_source_is_fetched_over_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """How a flags file in S3 is read: through a (presigned) https URL."""
    requested = []

    def fake_urlopen(url: str, timeout: float) -> io.BytesIO:
        requested.append((url, timeout))
        return io.BytesIO(b'{"watch_detail_page": true}')

    monkeypatch.setattr(flags_module.urllib.request, "urlopen", fake_urlopen)
    url = "https://bucket.s3.amazonaws.com/me/config/flags.json?X-Amz-Signature=abc"

    assert FlagFile(url).is_enabled("watch_detail_page", default=False) is True
    assert requested == [(url, flags_module.FETCH_TIMEOUT_SECONDS)]


def test_an_unreachable_url_falls_back_to_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    def unreachable(url: str, timeout: float) -> io.BytesIO:
        raise OSError("timed out")

    monkeypatch.setattr(flags_module.urllib.request, "urlopen", unreachable)

    flags = FlagFile("https://bucket.s3.amazonaws.com/me/config/flags.json")
    assert flags.is_enabled("watch_detail_page", default=False) is False
