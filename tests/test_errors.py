from stream_media_viewer.errors import log_exception


def test_log_exception_writes_error_log(tmp_path) -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        path = log_exception(exc, tmp_path / "error.log")
    text = path.read_text(encoding="utf-8")
    assert "ValueError" in text
    assert "boom" in text
