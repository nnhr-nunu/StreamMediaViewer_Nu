"""最初の案内・絞り込みで空・緊急キー・送る前の確認・写真の自動の下準備。"""

from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
from PySide6.QtCore import QEvent, QSize, Qt, QThread
from PySide6.QtGui import QIcon, QKeyEvent, QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox

from stream_media_viewer import prep_flow
from stream_media_viewer.app import StreamMediaViewerApp
from stream_media_viewer.i18n import t
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.settings import AppSettings
from stream_media_viewer.ui.operator_window import _list_icon


def _app(qtbot, settings: AppSettings | None = None) -> StreamMediaViewerApp:
    app = StreamMediaViewerApp(settings or AppSettings())
    qtbot.addWidget(app.operator)
    qtbot.addWidget(app.output)
    return app


def _photo(path: Path, **kwargs) -> MediaItem:
    when = kwargs.pop("when", None)
    return MediaItem(path=path, kind="image", captured_at=when, has_gps=False, **kwargs)


def test_start_page_offers_recent_folders_as_buttons(qtbot, tmp_path: Path) -> None:
    trip = tmp_path / "京都旅行"
    trip.mkdir()
    gone = tmp_path / "消えたフォルダ"
    settings = AppSettings()
    settings.recent_folders = [str(trip), str(gone)]
    app = _app(qtbot, settings)
    opened: list[str] = []
    app._open_folder_path = opened.append  # type: ignore[method-assign]
    app.operator.recent_folder_requested.disconnect()
    app.operator.recent_folder_requested.connect(app._open_folder_path)
    buttons = app.operator.guide_page.recent_buttons()
    # 無くなったフォルダは出さない
    assert [button.text() for button in buttons] == ["京都旅行"]
    buttons[0].click()
    assert opened == [str(trip)]


def test_filters_hiding_everything_say_so_and_can_be_cleared(qtbot, tmp_path: Path) -> None:
    app = _app(qtbot)
    app.settings.last_folder = str(tmp_path)
    app.operator.set_library_ready(True)
    app._items = [_photo(tmp_path / "a.jpg")]
    app._refresh_list()
    app.operator.chk_star_only.setChecked(True)
    page = app.operator.guide_page
    assert page.mode == "filtered"
    # フォルダが空、とは言わない
    assert app.operator.guide.text() == t("ja", "filtered_empty")
    assert not page.btn_clear_filters.isHidden()
    page.btn_clear_filters.click()
    assert not app.operator.chk_star_only.isChecked()
    assert len(app._visible) == 1


def test_empty_folder_offers_another_folder(qtbot, tmp_path: Path) -> None:
    app = _app(qtbot)
    app.settings.last_folder = str(tmp_path)
    app._items = []
    app._show_nothing()
    page = app.operator.guide_page
    assert app.operator.guide.text() == t("ja", "folder_empty")
    assert not page.btn_pick.isHidden()


def test_folder_without_dates_turns_the_date_filter_off(qtbot, tmp_path: Path) -> None:
    app = _app(qtbot)
    op = app.operator
    op.set_library_ready(True)
    app._items = [_photo(tmp_path / "a.jpg", when=datetime(2024, 5, 1))]
    app._apply_folder_dates(reset=True)
    op.chk_dates.setChecked(True)
    assert op.date_group.isEnabled()
    app._items = [_photo(tmp_path / "b.jpg")]
    app._apply_folder_dates(reset=True)
    assert not op.date_group.isEnabled()
    assert not op.chk_dates.isChecked()
    assert "2000" not in op.date_from.text()


def test_adding_videos_keeps_the_chosen_dates(qtbot, tmp_path: Path) -> None:
    from PySide6.QtCore import QDate

    app = _app(qtbot)
    op = app.operator
    app._items = [
        _photo(tmp_path / "a.jpg", when=datetime(2024, 5, 1)),
        _photo(tmp_path / "b.jpg", when=datetime(2024, 5, 9)),
    ]
    app._apply_folder_dates(reset=True)
    op.date_from.setDate(QDate(2024, 5, 3))
    op.chk_dates.setChecked(True)
    app._items.append(
        MediaItem(
            path=tmp_path / "c.mp4", kind="video", captured_at=datetime(2024, 5, 20), has_gps=False
        )
    )
    app._apply_folder_dates(reset=False)
    assert op.date_from.date() == QDate(2024, 5, 3)
    assert op.date_to.maximumDate() == QDate(2024, 5, 20)


def test_numpad_zero_hides_the_stream_even_while_a_dialog_is_open(qtbot) -> None:
    app = _app(qtbot)
    hidden: list[int] = []
    app._panic_keys._on_panic = lambda: hidden.append(1)
    app.operator.show()
    box = QMessageBox(app.operator)
    box.setText("?")
    box.open()
    qtbot.waitUntil(lambda: QApplication.activeModalWidget() is box, timeout=3000)
    press = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_0, Qt.KeyboardModifier.KeypadModifier, "0")
    QApplication.sendEvent(box, press)
    assert hidden == [1]
    qtbot.waitUntil(lambda: not box.isVisible(), timeout=3000)


def test_zero_without_a_dialog_is_left_to_the_operator_window(qtbot) -> None:
    app = _app(qtbot)
    hidden: list[int] = []
    app._panic_keys._on_panic = lambda: hidden.append(1)
    press = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_0, Qt.KeyboardModifier.NoModifier, "0")
    assert app._panic_keys.eventFilter(app.operator, press) is False
    assert hidden == []


def _ready_to_send(app: StreamMediaViewerApp, tmp_path: Path, *, face: bool) -> MediaItem:
    item = _photo(tmp_path / "a.jpg", has_face=face)
    app._items = [item]
    app._visible = [0]
    app._index = 0
    app._preview = np.zeros((8, 8, 3), dtype=np.uint8)
    app.gate.begin_load()
    app.gate.mark_processed()
    return item


def test_photo_with_faces_asks_every_time_and_enter_sends(qtbot, tmp_path: Path) -> None:
    app = _app(qtbot)
    _ready_to_send(app, tmp_path, face=True)
    asked: list[str] = []
    answers = iter([False, True])
    app._ask_send = lambda key: asked.append(key) or next(answers)  # type: ignore[method-assign]
    app._on_send()
    assert not app.gate.window_visible
    app._on_send()
    assert app.gate.window_visible
    assert asked == ["confirm_faces", "confirm_faces"]


def test_blur_off_asks_once_and_not_about_blurred_faces(qtbot, tmp_path: Path) -> None:
    app = _app(qtbot)
    app.settings.face_blur = False
    app.settings.blur_off_confirmed = False
    _ready_to_send(app, tmp_path, face=True)
    asked: list[str] = []
    app._ask_send = lambda key: asked.append(key) or True  # type: ignore[method-assign]
    app._on_send()
    app._on_send()
    assert asked == ["confirm_no_blur"]


def test_send_confirm_defaults_to_send(qtbot, monkeypatch) -> None:
    app = _app(qtbot)
    seen: dict[str, object] = {}

    def fake_exec(box: QMessageBox) -> int:
        seen["default"] = box.defaultButton().text()
        seen["escape"] = box.escapeButton().text()
        return 0

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    assert app._ask_send("confirm_faces") is False
    assert seen == {"default": t("ja", "confirm_send"), "escape": t("ja", "confirm_cancel")}


class _FakePrefetch:
    started: list[tuple[str, object]] = []

    def __init__(self, path, settings, note, key, folder_id) -> None:
        from PySide6.QtCore import QObject, Signal

        class _Sig(QObject):
            ready = Signal(str, object, bool, bool)

        self._sig = _Sig()
        self.ready = self._sig.ready
        self.path = path
        self.key = key

    def start(self, priority=None) -> None:
        _FakePrefetch.started.append((self.path.name, priority))

    def isFinished(self) -> bool:  # noqa: N802
        return True

    def requestInterruption(self) -> None:  # noqa: N802
        pass

    def wait(self, *_a) -> bool:
        return True


def test_auto_prep_works_near_the_current_photo_at_low_priority(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    _FakePrefetch.started = []
    monkeypatch.setattr(prep_flow, "PrefetchWorker", _FakePrefetch)
    app = _app(qtbot)
    app.operator.show()
    app.settings.last_folder = str(tmp_path)
    app._items = [_photo(tmp_path / f"{n}.jpg") for n in range(4)]
    app._visible = [0, 1, 2, 3]
    app._index = 2
    app._auto_rebuild()
    monkeypatch.setattr(app, "_auto_is_ready", lambda item, _f: item.path.name == "2.jpg")
    app._auto_prep_tick()
    assert _FakePrefetch.started == [("3.jpg", QThread.Priority.LowestPriority)]
    assert app._auto.progress() == (1, 4)
    assert "1/4" in app.operator.prep_label.text()
    # 1 枚できたら、休んでから次へ（すぐには始めない）
    app._prefetch_worker.ready.emit("k", np.zeros((4, 4, 3), np.uint8), True, False)
    assert app._items[3].has_face
    assert app._auto_timer.isActive()
    assert app._auto_timer.remainingTime() > 0
    assert len(_FakePrefetch.started) == 1


def test_auto_prep_waits_while_a_video_plays(qtbot, tmp_path: Path, monkeypatch) -> None:
    _FakePrefetch.started = []
    monkeypatch.setattr(prep_flow, "PrefetchWorker", _FakePrefetch)
    app = _app(qtbot)
    app.operator.show()
    app.settings.last_folder = str(tmp_path)
    app._items = [_photo(tmp_path / "a.jpg")]
    app._visible = [0]
    app._index = 0
    app._auto_rebuild()
    app._video.playing = True
    app._auto_prep_tick()
    assert _FakePrefetch.started == []
    assert app._auto_timer.isActive()


def test_clearing_prep_data_does_not_rebuild_it_right_away(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    app = _app(qtbot)
    app.settings.last_folder = str(tmp_path)

    def pick_this_folder(box: QMessageBox) -> int:
        button = next(b for b in box.buttons() if b.text() == t("ja", "clear_this_folder"))
        button.click()
        return 0

    monkeypatch.setattr(QMessageBox, "exec", pick_this_folder)
    text = app._clear_cache()
    assert t("ja", "cache_size").split(":")[0] in text
    assert app._auto_hold
    app._auto_schedule(0)
    assert not app._auto_timer.isActive()
    assert app.operator.prep_label.text() == ""


def test_selected_thumbnail_keeps_its_colors() -> None:
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.darkYellow)
    icon: QIcon = _list_icon(pixmap)
    normal = icon.pixmap(QSize(16, 16), QIcon.Mode.Normal).toImage()
    selected = icon.pixmap(QSize(16, 16), QIcon.Mode.Selected).toImage()
    assert normal.pixelColor(8, 8) == selected.pixelColor(8, 8)


def test_photo_rows_drop_the_ready_mark(qtbot, tmp_path: Path, monkeypatch) -> None:
    Image.new("RGB", (8, 8)).save(tmp_path / "a.jpg")
    app = _app(qtbot)
    monkeypatch.setattr("stream_media_viewer.app.cache_is_ready", lambda *_a: True)
    assert "✓" not in app._row_label(_photo(tmp_path / "a.jpg"))
    video = MediaItem(path=tmp_path / "v.mp4", kind="video", captured_at=None, has_gps=False)
    assert "✓" in app._row_label(video)


def test_dialogs_of_another_window_are_left_alone(qtbot) -> None:
    from PySide6.QtWidgets import QWidget

    app = _app(qtbot)
    app.operator.show()
    hidden: list[int] = []
    app._panic_keys._on_panic = lambda: hidden.append(1)
    stranger = QWidget()
    qtbot.addWidget(stranger)
    box = QMessageBox(stranger)
    box.open()
    qtbot.waitUntil(lambda: QApplication.activeModalWidget() is box, timeout=3000)
    press = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_0, Qt.KeyboardModifier.KeypadModifier, "0")
    assert app._panic_keys.eventFilter(box, press) is False
    assert hidden == []
    box.reject()
