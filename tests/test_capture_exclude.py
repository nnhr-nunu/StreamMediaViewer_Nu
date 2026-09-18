import sys
from collections.abc import Iterator

import pytest

from stream_media_viewer.ui.capture_exclude import (
    configure_dev_allow_capture,
    should_exclude_from_capture,
)


@pytest.fixture(autouse=True)
def _reset_dev_allow_capture() -> Iterator[None]:
    configure_dev_allow_capture(False)
    yield
    configure_dev_allow_capture(False)


def _reset_capture_policy(monkeypatch, *, frozen: bool, allow: bool) -> None:
    monkeypatch.setattr(sys, "frozen", frozen, raising=False)
    configure_dev_allow_capture(allow)


def test_source_launch_excludes_capture_by_default(monkeypatch) -> None:
    _reset_capture_policy(monkeypatch, frozen=False, allow=False)
    assert should_exclude_from_capture() is True


def test_source_launch_honors_hidden_dev_allow_capture(monkeypatch) -> None:
    _reset_capture_policy(monkeypatch, frozen=False, allow=True)
    assert should_exclude_from_capture() is False


def test_frozen_release_ignores_hidden_dev_allow_capture(monkeypatch) -> None:
    _reset_capture_policy(monkeypatch, frozen=True, allow=True)
    assert should_exclude_from_capture() is True
