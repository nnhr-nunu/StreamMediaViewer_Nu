from stream_media_viewer.safety.output_gate import OutputGate, OutputReason


def test_starts_masked() -> None:
    gate = OutputGate()
    assert gate.masked is True
    assert gate.reason is OutputReason.STARTUP
    assert gate.send_to_output() is False


def test_send_requires_processed() -> None:
    gate = OutputGate()
    gate.begin_load()
    assert gate.reason is OutputReason.LOADING
    assert gate.send_to_output() is False
    gate.mark_processed()
    assert gate.reason is OutputReason.AWAITING_SEND
    assert gate.masked is True
    assert gate.send_to_output() is True
    assert gate.masked is False
    assert gate.reason is OutputReason.LIVE


def test_load_masks_live_output() -> None:
    gate = OutputGate()
    gate.begin_load()
    gate.mark_processed()
    gate.send_to_output()
    gate.begin_load()
    assert gate.masked is True
    assert gate.reason is OutputReason.LOADING


def test_panic_overrides_live_and_needs_resend() -> None:
    gate = OutputGate()
    gate.begin_load()
    gate.mark_processed()
    gate.send_to_output()
    gate.panic()
    assert gate.masked is True
    assert gate.reason is OutputReason.PANIC
    assert gate.send_to_output() is False
    gate.clear_panic()
    assert gate.masked is True
    assert gate.send_to_output() is True
    assert gate.masked is False
