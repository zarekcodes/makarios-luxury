"""The brand asset script: it builds the icons wherever --out points, and reports them.

scripts/ isn't a package, so the module is loaded from its file. Every build
here writes into pytest's tmp_path, never into app/static/img/brand/.
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_brand_assets.py"
spec = importlib.util.spec_from_file_location("build_brand_assets", SCRIPT)
assert spec is not None and spec.loader is not None
brand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brand)

EXPECTED = {"badge-72.webp", "badge-108.webp", "favicon.png", "apple-touch-icon.png"}


def test_builds_into_a_directory_outside_the_repo(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The bug this guards: reporting a file outside the repo used to crash after writing it."""
    assert brand.main(["--out", str(tmp_path)]) == 0

    assert {path.name for path in tmp_path.iterdir()} == EXPECTED
    assert f"wrote {tmp_path / 'favicon.png'}" in capsys.readouterr().out


def test_builds_into_a_relative_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A relative --out resolves against the current directory, as a shell user expects."""
    monkeypatch.chdir(tmp_path)

    assert brand.main(["--out", "icons"]) == 0

    assert {path.name for path in (tmp_path / "icons").iterdir()} == EXPECTED
    assert str(tmp_path / "icons" / "badge-72.webp") in capsys.readouterr().out


def test_paths_inside_the_repo_are_reported_relative_to_it() -> None:
    assert brand.display_path(brand.DEFAULT_OUT / "favicon.png") == str(
        Path("app") / "static" / "img" / "brand" / "favicon.png"
    )


def test_a_missing_source_is_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert brand.main(["--source", str(tmp_path / "missing.png"), "--out", str(tmp_path)]) == 1

    assert "source logo not found" in capsys.readouterr().err
    assert not any(tmp_path.iterdir())
