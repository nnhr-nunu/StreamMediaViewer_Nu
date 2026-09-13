from stream_media_viewer.safety.output_gate import OutputGate, OutputReason


def test_starts_hidden() -> None:
    gate = OutputGate()
    assert gate.window_visible is False
    assert gate.masked is True
    assert gate.reason is OutputReason.STARTUP
    assert gate.send_to_output() is False


def test_send_requires_processed() -> None:
    gate = OutputGate()
    gate.begin_load()
    assert gate.send_to_output() is False
    gate.mark_processed()
    assert gate.send_to_output() is True
    assert gate.reason is OutputReason.LIVE
    assert gate.window_visible is True
    assert gate.masked is False


def test_preview_load_keeps_live() -> None:
    gate = OutputGate()
    gate.begin_load()
    gate.mark_processed()
    gate.send_to_output()
    gate.begin_load()
    assert gate.reason is OutputReason.LIVE
    assert gate.window_visible is True
    assert gate.ready is False
    assert gate.send_to_output() is False
    gate.mark_processed()
    assert gate.send_to_output() is True


def test_panic_hides_until_resend() -> None:
    gate = OutputGate()
    gate.begin_load()
    gate.mark_processed()
    gate.send_to_output()
    gate.panic()
    assert gate.window_visible is False
    assert gate.send_to_output() is True
    assert gate.window_visible is True


def test_standby_shows_until_live_or_panic() -> None:
    gate = OutputGate()
    gate.enable_standby(True)
    assert gate.reason is OutputReason.STANDBY
    assert gate.window_visible is True
    gate.panic()
    assert gate.window_visible is False
