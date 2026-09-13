from stream_media_viewer import OPERATOR_WINDOW_TITLE, OUTPUT_WINDOW_TITLE
from stream_media_viewer.app import StreamMediaViewerApp


def test_two_windows_start_masked(qtbot) -> None:
    app = StreamMediaViewerApp()
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    assert app.operator.windowTitle() == OPERATOR_WINDOW_TITLE
    assert app.output.windowTitle() == OUTPUT_WINDOW_TITLE
    assert app.gate.masked is True
    app.gate.begin_load()
    app.gate.mark_processed()
    app._on_send()
    assert app.gate.masked is False
    app._on_panic()
    assert app.gate.masked is True
