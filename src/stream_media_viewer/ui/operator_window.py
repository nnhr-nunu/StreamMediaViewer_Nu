"""操作画面。配信へは app 経由の送信だけ。"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSlider,
    QStackedLayout,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from stream_media_viewer import OPERATOR_WINDOW_TITLE
from stream_media_viewer.i18n import t
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.render.enhance import parse_enhance_level
from stream_media_viewer.safety.output_gate import OutputGate, OutputReason
from stream_media_viewer.ui.preview_canvas import PreviewCanvas
from stream_media_viewer.ui.styles import DARK_QSS

_LIST_ICON = QSize(168, 168)
_LIST_GRID = QSize(200, 214)


def _bar_button() -> QToolButton:
    button = QToolButton()
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
    button.setAutoRaise(False)
    button.setMinimumSize(64, 52)
    return button


def _caption(button: QToolButton, glyph: str, short: str, tip: str) -> None:
    button.setText(f"{glyph}\n{short}")
    button.setToolTip(tip)


class OperatorWindow(QMainWindow):
    open_folder_requested = Signal()
    send_requested = Signal()
    panic_requested = Signal()
    prev_requested = Signal()
    next_requested = Signal()
    play_requested = Signal()
    star_requested = Signal()
    undo_requested = Signal()
    item_selected = Signal(int)
    mark_added = Signal(dict)
    settings_changed = Signal()
    filters_changed = Signal()
    loop_changed = Signal()
    standby_requested = Signal()
    prepare_requested = Signal()
    prepare_folder_requested = Signal()
    clear_cache_requested = Signal()
    enhance_cycle_requested = Signal()
    settings_requested = Signal()

    def __init__(self, gate: OutputGate) -> None:
        super().__init__()
        self._gate = gate
        self.lang = "ja"
        self.setWindowTitle(OPERATOR_WINDOW_TITLE)
        self.resize(1280, 800)
        self.setStyleSheet(DARK_QSS)

        root = QWidget()
        outer = QVBoxLayout(root)

        top = QHBoxLayout()
        self.btn_folder = _bar_button()
        self.chk_face = QCheckBox()
        self.chk_face.setChecked(True)
        self.chk_text = QCheckBox()
        self.btn_enhance = _bar_button()
        self.enhance_level = "weak"
        self.btn_standby = _bar_button()
        self.btn_folder_prep = _bar_button()
        self.btn_clear_cache = _bar_button()
        self.btn_settings = _bar_button()
        self.cache_label = QLabel()
        self.cache_label.setObjectName("meta")
        top.addWidget(self.btn_folder)
        top.addWidget(self.chk_face)
        top.addWidget(self.chk_text)
        top.addWidget(self.btn_enhance)
        top.addWidget(self.btn_standby)
        top.addWidget(self.btn_folder_prep)
        top.addWidget(self.btn_clear_cache)
        top.addWidget(self.cache_label)
        top.addStretch()
        top.addWidget(self.btn_settings)
        outer.addLayout(top)

        filters = QHBoxLayout()
        self.chk_star_only = QCheckBox()
        self.chk_photos = QCheckBox()
        self.chk_videos = QCheckBox()
        self.chk_faces = QCheckBox()
        self.chk_gps = QCheckBox()
        self.chk_no_gps = QCheckBox()
        self.chk_dates = QCheckBox()
        self.combo_place = QComboBox()
        self.combo_place.setMinimumWidth(140)
        self.combo_folder = QComboBox()
        self.combo_folder.setMinimumWidth(140)
        self.date_from = QDateEdit()
        self.date_to = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_to.setCalendarPopup(True)
        for box in (
            self.chk_star_only,
            self.chk_photos,
            self.chk_videos,
            self.chk_faces,
            self.chk_gps,
            self.chk_no_gps,
            self.chk_dates,
        ):
            box.setChecked(False)
            filters.addWidget(box)
        filters.addWidget(self.combo_folder)
        filters.addWidget(self.combo_place)
        filters.addWidget(self.date_from)
        filters.addWidget(self.date_to)
        filters.addStretch()
        outer.addLayout(filters)

        body = QHBoxLayout()
        self.list = QListWidget()
        self.list.setViewMode(QListView.ViewMode.IconMode)
        self.list.setFlow(QListView.Flow.TopToBottom)
        self.list.setWrapping(False)
        self.list.setMovement(QListView.Movement.Static)
        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setUniformItemSizes(True)
        self.list.setIconSize(_LIST_ICON)
        self.list.setGridSize(_LIST_GRID)
        self.list.setSpacing(8)
        self.list.setMinimumWidth(220)
        self.list.setMaximumWidth(280)
        self.list.setWordWrap(True)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        body.addWidget(self.list)

        preview_col = QVBoxLayout()
        self.meta = QLabel()
        self.meta.setObjectName("meta")
        preview_host = QWidget()
        self._preview_stack = QStackedLayout(preview_host)
        self.preview = PreviewCanvas()
        self.guide = QLabel()
        self.guide.setObjectName("guide")
        self.guide.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.guide.setWordWrap(True)
        self._preview_stack.addWidget(self.preview)
        self._preview_stack.addWidget(self.guide)
        preview_col.addWidget(self.meta)
        preview_col.addWidget(preview_host, stretch=1)
        self.lbl_in = QLabel()
        self.lbl_in.setObjectName("meta")
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setObjectName("rangeIn")
        self.lbl_out = QLabel()
        self.lbl_out.setObjectName("meta")
        self.timeline_out = QSlider(Qt.Orientation.Horizontal)
        self.timeline_out.setObjectName("rangeOut")
        self.chk_loop = QCheckBox()
        row_in = QHBoxLayout()
        row_in.addWidget(self.lbl_in)
        row_in.addWidget(self.timeline, stretch=1)
        row_out = QHBoxLayout()
        row_out.addWidget(self.lbl_out)
        row_out.addWidget(self.timeline_out, stretch=1)
        preview_col.addLayout(row_in)
        preview_col.addLayout(row_out)
        preview_col.addWidget(self.chk_loop)
        body.addLayout(preview_col, stretch=1)
        outer.addLayout(body, stretch=1)

        bar_host = QWidget()
        bar = QHBoxLayout(bar_host)
        bar.setContentsMargins(0, 0, 0, 0)
        self.btn_prev = _bar_button()
        self.btn_next = _bar_button()
        self.btn_send = _bar_button()
        self.btn_panic = _bar_button()
        self.btn_star = _bar_button()
        self.btn_undo = _bar_button()
        self.btn_rect = _bar_button()
        self.btn_brush = _bar_button()
        self.btn_play = _bar_button()
        self.btn_prep = _bar_button()
        self.btn_rect.setCheckable(True)
        self.btn_brush.setCheckable(True)
        self.btn_rect.setChecked(True)
        self.btn_star.setCheckable(True)
        for widget in (
            self.btn_prev,
            self.btn_next,
            self.btn_send,
            self.btn_panic,
            self.btn_star,
            self.btn_undo,
            self.btn_rect,
            self.btn_brush,
        ):
            bar.addWidget(widget)
        bar.addStretch()
        bar.addWidget(self.btn_play)
        bar.addWidget(self.btn_prep)
        outer.addWidget(bar_host)

        self.setCentralWidget(root)
        self._bind()
        self.set_media_kind(None)
        self.retranslate()
        self.show_guide(t("ja", "empty_guide"))

    def _bind(self) -> None:
        self.btn_folder.clicked.connect(self.open_folder_requested.emit)
        self.btn_send.clicked.connect(self.send_requested.emit)
        self.btn_panic.clicked.connect(self.panic_requested.emit)
        self.btn_prev.clicked.connect(self.prev_requested.emit)
        self.btn_next.clicked.connect(self.next_requested.emit)
        self.btn_play.clicked.connect(self.play_requested.emit)
        self.btn_star.clicked.connect(self.star_requested.emit)
        self.btn_undo.clicked.connect(self.undo_requested.emit)
        self.btn_standby.clicked.connect(self.standby_requested.emit)
        self.btn_prep.clicked.connect(self.prepare_requested.emit)
        self.btn_folder_prep.clicked.connect(self.prepare_folder_requested.emit)
        self.btn_clear_cache.clicked.connect(self.clear_cache_requested.emit)
        self.btn_enhance.clicked.connect(self.enhance_cycle_requested.emit)
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        self.list.currentRowChanged.connect(self.item_selected.emit)
        self.preview.mark_added.connect(self.mark_added.emit)
        self.preview.clicked.connect(self.play_requested.emit)
        self.btn_rect.clicked.connect(lambda: self._mode("rect"))
        self.btn_brush.clicked.connect(lambda: self._mode("stroke"))
        self.chk_face.toggled.connect(lambda _=False: self.settings_changed.emit())
        self.chk_text.toggled.connect(lambda _=False: self.settings_changed.emit())
        self.chk_loop.toggled.connect(lambda _=False: self.loop_changed.emit())
        for box in (
            self.chk_star_only,
            self.chk_photos,
            self.chk_videos,
            self.chk_faces,
            self.chk_gps,
            self.chk_no_gps,
            self.chk_dates,
        ):
            box.toggled.connect(lambda _=False: self.filters_changed.emit())
        self.combo_place.currentIndexChanged.connect(lambda _=0: self.filters_changed.emit())
        self.combo_folder.currentIndexChanged.connect(lambda _=0: self.filters_changed.emit())
        self.date_from.dateChanged.connect(lambda _=None: self.filters_changed.emit())
        self.date_to.dateChanged.connect(lambda _=None: self.filters_changed.emit())
        QShortcut(QKeySequence("A"), self, self.prev_requested.emit)
        QShortcut(QKeySequence("D"), self, self.next_requested.emit)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.prev_requested.emit)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.next_requested.emit)
        QShortcut(QKeySequence("4"), self, self.prev_requested.emit)
        QShortcut(QKeySequence("6"), self, self.next_requested.emit)
        QShortcut(QKeySequence("Return"), self, self.send_requested.emit)
        QShortcut(QKeySequence("Enter"), self, self.send_requested.emit)
        QShortcut(QKeySequence("Esc"), self, self.panic_requested.emit)
        QShortcut(QKeySequence("0"), self, self.panic_requested.emit)
        QShortcut(QKeySequence("Space"), self, self.play_requested.emit)
        QShortcut(QKeySequence("5"), self, self.play_requested.emit)
        QShortcut(QKeySequence("F"), self, self.star_requested.emit)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo_requested.emit)

    def _mode(self, mode: str) -> None:
        self.preview.mode = mode
        self.btn_rect.setChecked(mode == "rect")
        self.btn_brush.setChecked(mode == "stroke")

    def retranslate(self) -> None:
        lang = self.lang
        _caption(self.btn_folder, "📁", t(lang, "btn_folder"), t(lang, "open_folder"))
        _caption(self.btn_send, "⬆", t(lang, "btn_send"), t(lang, "send"))
        _caption(self.btn_panic, "⬛", t(lang, "btn_panic"), t(lang, "panic"))
        _caption(self.btn_prev, "◀", t(lang, "btn_prev"), t(lang, "prev"))
        _caption(self.btn_next, "▶", t(lang, "btn_next"), t(lang, "next"))
        _caption(self.btn_play, "⏯", t(lang, "btn_play"), t(lang, "play"))
        _caption(self.btn_star, "☆", t(lang, "btn_star"), t(lang, "star"))
        _caption(self.btn_undo, "↩", t(lang, "btn_undo"), t(lang, "undo"))
        _caption(self.btn_rect, "▢", t(lang, "btn_rect"), t(lang, "rect"))
        _caption(self.btn_brush, "🖌", t(lang, "btn_brush"), t(lang, "brush"))
        _caption(self.btn_prep, "⏳", t(lang, "btn_prep"), t(lang, "prepare"))
        _caption(self.btn_standby, "🖼", t(lang, "btn_standby"), t(lang, "standby"))
        _caption(self.btn_folder_prep, "📂", t(lang, "btn_folder_prep"), t(lang, "prepare_folder"))
        _caption(self.btn_clear_cache, "🗑", t(lang, "btn_clear"), t(lang, "clear_cache"))
        _caption(self.btn_settings, "⚙", t(lang, "btn_settings"), t(lang, "settings"))
        self.chk_face.setText(t(lang, "face_blur"))
        self.chk_text.setText(t(lang, "text_blur"))
        self.set_enhance_level(self.enhance_level)
        self.chk_loop.setText(t(lang, "loop"))
        self.chk_star_only.setText("⭐ " + t(lang, "filter_star"))
        self.chk_photos.setText(t(lang, "filter_photo"))
        self.chk_videos.setText(t(lang, "filter_video"))
        self.chk_faces.setText("⚠ " + t(lang, "filter_face"))
        self.chk_gps.setText(t(lang, "filter_gps"))
        self.chk_no_gps.setText(t(lang, "filter_gps_no"))
        self.chk_dates.setText(t(lang, "filter_dates"))
        self._set_combo_all(self.combo_place, "filter_place_all")
        self._set_combo_all(self.combo_folder, "filter_folder_all")
        self.lbl_in.setText(t(lang, "range_in"))
        self.lbl_out.setText(t(lang, "range_out"))
        self.timeline.setToolTip(t(lang, "range_in"))
        self.timeline_out.setToolTip(t(lang, "range_out"))
        if self._preview_stack.currentWidget() is self.guide and not self.list.count():
            self.show_guide(t(lang, "empty_guide"))

    def _set_combo_all(self, combo: QComboBox, key: str) -> None:
        if combo.count() == 0:
            combo.addItem(t(self.lang, key), "")
            return
        combo.setItemText(0, t(self.lang, key))

    def set_places(self, names: list[str], selected: str) -> None:
        self._fill_combo(self.combo_place, "filter_place_all", names, selected)

    def set_folders(self, names: list[str], selected: str) -> None:
        self._fill_combo(self.combo_folder, "filter_folder_all", names, selected)

    def _fill_combo(self, combo: QComboBox, all_key: str, names: list[str], selected: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(t(self.lang, all_key), "")
        for name in names:
            combo.addItem(name, name)
        index = combo.findData(selected)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def selected_place(self) -> str:
        return str(self.combo_place.currentData() or "")

    def selected_folder(self) -> str:
        return str(self.combo_folder.currentData() or "")

    def set_enhance_level(self, level: str) -> None:
        self.enhance_level = parse_enhance_level(level)
        lang = self.lang
        self.btn_enhance.setText(t(lang, f"enhance_{self.enhance_level}"))
        self.btn_enhance.setToolTip(t(lang, "enhance_hint"))

    def set_media_kind(self, kind: str | None) -> None:
        video = kind == "video"
        self.preview.click_toggles_play = video
        self.preview.setCursor(
            Qt.CursorShape.PointingHandCursor if video else Qt.CursorShape.ArrowCursor
        )
        for widget in (
            self.btn_play,
            self.btn_prep,
            self.lbl_in,
            self.timeline,
            self.lbl_out,
            self.timeline_out,
            self.chk_loop,
        ):
            widget.setVisible(video)

    def set_range_visible(self, visible: bool) -> None:
        self.set_media_kind("video" if visible else "image")

    def show_guide(self, text: str) -> None:
        self.guide.setText(text)
        self._preview_stack.setCurrentWidget(self.guide)

    def reveal_preview(self) -> None:
        self._preview_stack.setCurrentWidget(self.preview)

    def set_items(
        self,
        items: list[MediaItem],
        labels: list[str],
        icons: list[QPixmap | None] | None = None,
        tips: list[str] | None = None,
    ) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        for index, label in enumerate(labels):
            row = QListWidgetItem(label)
            pixmap = icons[index] if icons and index < len(icons) else None
            if pixmap is not None and not pixmap.isNull():
                row.setIcon(QIcon(pixmap))
            if tips and index < len(tips):
                row.setToolTip(tips[index])
            row.setSizeHint(_LIST_GRID)
            row.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.list.addItem(row)
        self.list.blockSignals(False)

    def set_row_icon(self, row: int, pixmap: QPixmap) -> None:
        item = self.list.item(row)
        if item is None or pixmap.isNull():
            return
        item.setIcon(QIcon(pixmap))

    def refresh_status(self) -> None:
        live = self._gate.reason is OutputReason.LIVE
        self.btn_send.setEnabled(self._gate.ready and self._gate.reason is not OutputReason.PANIC)
        self.btn_send.setStyleSheet("background:#6b3fa0;" if live else "")
