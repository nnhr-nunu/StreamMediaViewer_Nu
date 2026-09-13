from pathlib import Path

from stream_media_viewer import __version__, display_version


def test_display_version_uses_package_version() -> None:
    assert display_version() == f"v{__version__}"


def test_package_version_matches_pyproject() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{__version__}"' in text
