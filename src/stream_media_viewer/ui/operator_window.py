"""操作画面。配信へは app 経由の送信だけ。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSlider,
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


def _icon_button(text: str, tooltip: str) -> QToolButton:
    button = QToolButton()
    button.setText(text)
    button.setToolTip(tooltip)
    button.setAutoRaise(False)
    return button


class OperatorWindow(QMainWindow):
    open_folder_requested = Signal()
    send_requested = Signal()
    panic_requested = Signal()
    prev_requested = Signal()
    next_requested = Signal()
    play_requested = Signal()
    star_requested = Signal()
    undo_requested = Signal()
    language_requested = Signal()
    item_selected = Signal(int)
    mark_added = Signal(dict)
    settings_changed = Signal()
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
        self.btn_folder = _icon_button("📁", "")
        self.btn_lang = _icon_button("あ/A", "")
        self.chk_face = QCheckBox()
        self.chk_face.setChecked(True)
        self.chk_text = QCheckBox()
        self.chk_audio = QCheckBox()
        self.btn_enhance = _icon_button("✨弱", "")
        self.enhance_level = "weak"
        self.btn_standby = _icon_button("🖼", "")
        self.btn_folder_prep = _icon_button("📂⏳", "")
        self.btn_clear_cache = _icon_button("🗑", "")
        self.btn_settings = _icon_button("⚙", "")
        self.cache_label = QLabel()
        self.cache_label.setObjectName("meta")
        top.addWidget(self.btn_folder)
        top.addWidget(self.chk_face)
        top.addWidget(self.chk_text)
        top.addWidget(self.chk_audio)
        top.addWidget(self.btn_enhance)
        top.addWidget(self.btn_standby)
        top.addWidget(self.btn_folder_prep)
        top.addWidget(self.btn_clear_cache)
        top.addWidget(self.cache_label)
        top.addStretch()
        top.addWidget(self.btn_settings)
        top.addWidget(self.btn_lang)
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
        filters.addWidget(self.combo_place)
        filters.addWidget(self.date_from)
        filters.addWidget(self.date_to)
        filters.addStretch()
        outer.addLayout(filters)

        body = QHBoxLayout()
        self.list = QListWidget()
        self.list.setMaximumWidth(320)
        body.addWidget(self.list)

        preview_col = QVBoxLayout()
        self.meta = QLabel()
        self.meta.setObjectName("meta")
        self.preview = PreviewCanvas()
        preview_col.addWidget(self.meta)
        preview_col.addWidget(self.preview, stretch=1)
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

        bar = QHBoxLayout()
        self.btn_prev = _icon_button("◀", "")
        self.btn_play = _icon_button("▶", "")
        self.btn_next = _icon_button("▶▶", "")
        self.btn_send = _icon_button("⬆", "")
        self.btn_panic = _icon_button("⬛", "")
        self.btn_star = _icon_button("☆", "")
        self.btn_undo = _icon_button("↩", "")
        self.btn_rect = _icon_button("▢", "")
        self.btn_brush = _icon_button("🖌", "")
        self.btn_prep = _icon_button("⏳", "")
        self.btn_rect.setCheckable(True)
        self.btn_brush.setCheckable(True)
        self.btn_rect.setChecked(True)
        self.btn_star.setCheckable(True)
        for widget in (
            self.btn_prev,
            self.btn_play,
            self.btn_next,
            self.btn_send,
            self.btn_panic,
            self.btn_star,
            self.btn_undo,
            self.btn_rect,
            self.btn_brush,
            self.btn_prep,
        ):
            bar.addWidget(widget)
        bar.addStretch()
        outer.addLayout(bar)

        self.setCentralWidget(root)
        self._bind()
        self.retranslate()

    def _bind(self) -> None:
        self.btn_folder.clicked.connect(self.open_folder_requested.emit)
        self.btn_send.clicked.connect(self.send_requested.emit)
        self.btn_panic.clicked.connect(self.panic_requested.emit)
        self.btn_prev.clicked.connect(self.prev_requested.emit)
        self.btn_next.clicked.connect(self.next_requested.emit)
        self.btn_play.clicked.connect(self.play_requested.emit)
        self.btn_star.clicked.connect(self.star_requested.emit)
        self.btn_undo.clicked.connect(self.undo_requested.emit)
        self.btn_lang.clicked.connect(self.language_requested.emit)
        self.btn_standby.clicked.connect(self.standby_requested.emit)
        self.btn_prep.clicked.connect(self.prepare_requested.emit)
        self.btn_folder_prep.clicked.connect(self.prepare_folder_requested.emit)
        self.btn_clear_cache.clicked.connect(self.clear_cache_requested.emit)
        self.btn_enhance.clicked.connect(self.enhance_cycle_requested.emit)
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        self.list.currentRowChanged.connect(self.item_selected.emit)
        self.preview.mark_added.connect(self.mark_added.emit)
        self.btn_rect.clicked.connect(lambda: self._mode("rect"))
        self.btn_brush.clicked.connect(lambda: self._mode("stroke"))
        for box in (
            self.chk_face,
            self.chk_text,
            self.chk_audio,
            self.chk_star_only,
            self.chk_photos,
            self.chk_videos,
            self.chk_faces,
            self.chk_gps,
            self.chk_no_gps,
            self.chk_dates,
            self.chk_loop,
        ):
            box.toggled.connect(lambda _=False: self.settings_changed.emit())
        self.combo_place.currentIndexChanged.connect(lambda _=0: self.settings_changed.emit())
        self.date_from.dateChanged.connect(lambda _=None: self.settings_changed.emit())
        self.date_to.dateChanged.connect(lambda _=None: self.settings_changed.emit())
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
        self.btn_folder.setToolTip(t(lang, "open_folder"))
        self.btn_send.setToolTip(t(lang, "send"))
        self.btn_panic.setToolTip(t(lang, "panic"))
        self.btn_prev.setToolTip(t(lang, "prev"))
        self.btn_next.setToolTip(t(lang, "next"))
        self.btn_play.setToolTip(t(lang, "play"))
        self.btn_star.setToolTip(t(lang, "star"))
        self.btn_undo.setToolTip(t(lang, "undo"))
        self.chk_face.setText(t(lang, "face_blur"))
        self.chk_text.setText(t(lang, "text_blur"))
        self.chk_audio.setText(t(lang, "audio"))
        self.chk_audio.setToolTip(t(lang, "audio_hint"))
        self.set_enhance_level(self.enhance_level)
        self.chk_loop.setText(t(lang, "loop"))
        self.chk_star_only.setText("⭐ " + t(lang, "filter_star"))
        self.chk_photos.setText(t(lang, "filter_photo"))
        self.chk_videos.setText(t(lang, "filter_video"))
        self.chk_faces.setText("⚠ " + t(lang, "filter_face"))
        self.chk_gps.setText(t(lang, "filter_gps"))
        self.chk_no_gps.setText(t(lang, "filter_gps_no"))
        self.chk_dates.setText("📅")
        if self.combo_place.count() == 0:
            self.combo_place.addItem(t(lang, "filter_place_all"), "")
        else:
            self.combo_place.setItemText(0, t(lang, "filter_place_all"))
        self.btn_lang.setToolTip(t(lang, "language"))
        self.btn_settings.setToolTip(t(lang, "settings"))
        self.btn_standby.setToolTip(t(lang, "standby"))
        self.btn_rect.setToolTip(t(lang, "rect"))
        self.btn_brush.setToolTip(t(lang, "brush"))
        self.btn_prep.setToolTip(t(lang, "prepare"))
        self.btn_folder_prep.setToolTip(t(lang, "prepare_folder"))
        self.btn_clear_cache.setToolTip(t(lang, "clear_cache"))
        self.lbl_in.setText(t(lang, "range_in"))
        self.lbl_out.setText(t(lang, "range_out"))
        self.timeline.setToolTip(t(lang, "range_in"))
        self.timeline_out.setToolTip(t(lang, "range_out"))

    def set_places(self, names: list[str], selected: str) -> None:
        current = selected
        self.combo_place.blockSignals(True)
        self.combo_place.clear()
        self.combo_place.addItem(t(self.lang, "filter_place_all"), "")
        for name in names:
            self.combo_place.addItem(name, name)
        index = self.combo_place.findData(current)
        self.combo_place.setCurrentIndex(index if index >= 0 else 0)
        self.combo_place.blockSignals(False)

    def selected_place(self) -> str:
        return str(self.combo_place.currentData() or "")

    def set_enhance_level(self, level: str) -> None:
        self.enhance_level = parse_enhance_level(level)
        lang = self.lang
        self.btn_enhance.setText(t(lang, f"enhance_{level}"))
        self.btn_enhance.setToolTip(t(lang, "enhance_hint"))

    def set_range_visible(self, visible: bool) -> None:
        for widget in (self.lbl_in, self.timeline, self.lbl_out, self.timeline_out, self.chk_loop):
            widget.setVisible(visible)

    def set_items(self, items: list[MediaItem], labels: list[str]) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        for label in labels:
            self.list.addItem(QListWidgetItem(label))
        self.list.blockSignals(False)

    def refresh_status(self) -> None:
        live = self._gate.reason is OutputReason.LIVE
        self.btn_send.setEnabled(self._gate.ready and self._gate.reason is not OutputReason.PANIC)
        self.btn_send.setStyleSheet("background:#6b3fa0;" if live else "")
