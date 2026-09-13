from stream_media_viewer import OPERATOR_WINDOW_TITLE, OUTPUT_WINDOW_TITLE
from stream_media_viewer.app import StreamMediaViewerApp
from stream_media_viewer.settings import AppSettings


def test_two_windows_start_hidden(qtbot) -> None:
    app = StreamMediaViewerApp(AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    assert app.operator.windowTitle() == OPERATOR_WINDOW_TITLE
    assert app.output.windowTitle() == OUTPUT_WINDOW_TITLE
    assert app.gate.window_visible is False
    app.gate.begin_load()
    app.gate.mark_processed()
    app.gate.send_to_output()
    app._sync_windows()
    assert app.gate.window_visible is True
    app._on_panic()
    assert app.gate.window_visible is False
