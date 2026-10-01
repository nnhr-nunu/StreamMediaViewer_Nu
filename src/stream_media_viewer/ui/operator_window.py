"""操作画面。配信へは app 経由の送信だけ。"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut, QTransform
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QSizePolicy,
    QSlider,
    QStackedLayout,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from stream_media_viewer import OPERATOR_WINDOW_TITLE
from stream_media_viewer.detect.blur import DEFAULT_BRUSH_WIDTH, MAX_BRUSH_WIDTH, MIN_BRUSH_WIDTH
from stream_media_viewer.i18n import t
from stream_media_viewer.library.filters import PLACE_NONE
from stream_media_viewer.library.item import MediaItem
from stream_media_viewer.library.sort import parse_list_sort
from stream_media_viewer.render.enhance import parse_enhance_level
from stream_media_viewer.safety.output_gate import OutputGate, OutputReason
from stream_media_viewer.ui.app_icon import apply_app_icon
from stream_media_viewer.ui.capture_exclude import exclude_from_capture
from stream_media_viewer.ui.drop_hint import CalendarDateEdit, DropHintCombo
from stream_media_viewer.ui.flow_layout import FlowLayout
from stream_media_viewer.ui.glyph_icon import set_glyph
from stream_media_viewer.ui.guide_page import GuidePage
from stream_media_viewer.ui.help_dialog import HelpDialog
from stream_media_viewer.ui.list_thumb import with_video_mark
from stream_media_viewer.ui.overlays import MAX_LOUPE_PX, MIN_LOUPE_PX, OPERATOR_LOUPE_PX
from stream_media_viewer.ui.preview_canvas import PreviewCanvas
from stream_media_viewer.ui.styles import DARK_QSS

_LIST_ICON = QSize(220, 220)
_LIST_GRID = QSize(228, 238)
_PREVIEW_MIN = 520
_LIST_SHARE = 0.42
_TWO_COL_MIN = 400
_CAPTION_H = 40
_ROLE_PIX = Qt.ItemDataRole.UserRole
_ROLE_KIND = Qt.ItemDataRole.UserRole + 1
_ROLE_ROT = Qt.ItemDataRole.UserRole + 2
_ROLE_PATH = Qt.ItemDataRole.UserRole + 3
# これより狭いと上の段の「写真の下準備」の進み具合を隠す（🎦のカーソル説明に残る）
_PREP_LABEL_MIN_W = 1000
_STATUS_KEYS = {
    OutputReason.STARTUP: ("status_hidden", "hidden"),
    OutputReason.PANIC: ("status_panic", "hidden"),
    OutputReason.STANDBY: ("status_standby", "standby"),
}


def _bar_button() -> QToolButton:
    button = QToolButton()
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
    button.setAutoRaise(False)
    button.setMinimumSize(64, 52)
    return button


def _caption(button: QToolButton, glyph: str, short: str, tip: str) -> None:
    set_glyph(button, glyph, short, tip)


def _list_icon(pixmap: QPixmap) -> QIcon:
    """選んだ行でも縮小画の色を変えない（選択の色は行の背景で分かる）。"""
    icon = QIcon()
    icon.addPixmap(pixmap, QIcon.Mode.Normal)
    icon.addPixmap(pixmap, QIcon.Mode.Selected)
    return icon


def _repolish(widget: QWidget) -> None:
    """property を変えたあと、見た目の指定を掛け直す。"""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class OperatorWindow(QMainWindow):
    open_folder_requested = Signal()
    recent_folder_requested = Signal(str)
    clear_filters_requested = Signal()
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
    prepare_videos_requested = Signal()
    clear_marks_requested = Signal()
    enhance_cycle_requested = Signal()
    settings_requested = Signal()
    language_cycle_requested = Signal()
    rotate_left_requested = Signal()
    rotate_right_requested = Signal()
    region_clicked = Signal(float, float)
    hide_item_requested = Signal(int)
    audio_changed = Signal()
    false_undo_requested = Signal()
    brush_width_changed = Signal(int)
    closing = Signal()

    def __init__(self, gate: OutputGate) -> None:
        super().__init__()
        self._gate = gate
        self.lang = "ja"
        self.setWindowTitle(OPERATOR_WINDOW_TITLE)
        apply_app_icon(self)
        self.setMinimumSize(900, 560)
        self._fit_initial_size()
        self.setStyleSheet(DARK_QSS)

        root = QWidget()
        outer = QVBoxLayout(root)

        top = QHBoxLayout()
        self.btn_folder = _bar_button()
        self.chk_face = QCheckBox()
        self.chk_face.setChecked(True)
        self.chk_text = QCheckBox()
        self.btn_enhance = _bar_button()
        self.btn_enhance.setMinimumWidth(96)
        self.enhance_level = "weak"
        self._playing = False
        self._fit_cache: dict[tuple, QPixmap] = {}
        self._list_paths: list[str] = []
        self._fit_icon_size = 0
        self.btn_prep_videos = _bar_button()
        self.btn_settings = _bar_button()
        # 写真の下準備は自動。進み具合だけ小さく出す
        self.prep_label = QLabel()
        self.prep_label.setObjectName("meta")
        self._prep_tip = ""
        self._live_probe = lambda: False
        top.addWidget(self.btn_folder)
        top.addWidget(self.chk_face)
        top.addWidget(self.chk_text)
        top.addWidget(self.btn_enhance)
        top.addWidget(self.btn_prep_videos)
        top.addWidget(self.prep_label)
        top.addStretch()
        top.addWidget(self.btn_settings)
        outer.addLayout(top)

        self.filter_box = QGroupBox()
        filters = FlowLayout(self.filter_box, h_spacing=8, v_spacing=6)
        filters.setContentsMargins(8, 6, 8, 6)
        self.chk_star_only = QCheckBox()
        self.chk_photos = QCheckBox()
        self.chk_videos = QCheckBox()
        self.chk_filter_face = QCheckBox()
        self.chk_dates = QCheckBox()
        self.combo_place = DropHintCombo()
        self.combo_place.setMinimumWidth(150)
        self.combo_folder = DropHintCombo()
        self.combo_folder.setMinimumWidth(176)
        self.date_from = CalendarDateEdit()
        self.date_to = CalendarDateEdit()
        self.date_from.setMinimumWidth(118)
        self.date_to.setMinimumWidth(118)
        self.date_from.setMaximumWidth(132)
        self.date_to.setMaximumWidth(132)
        for box in (
            self.chk_star_only,
            self.chk_videos,
            self.chk_filter_face,
            self.chk_dates,
        ):
            box.setChecked(False)
        self.chk_photos.setChecked(True)
        for box in (self.chk_star_only, self.chk_filter_face, self.chk_photos, self.chk_videos):
            filters.addWidget(box)
        filters.addWidget(self.combo_folder)
        filters.addWidget(self.combo_place)
        self.date_group = QWidget()
        date_row = QHBoxLayout(self.date_group)
        date_row.setContentsMargins(0, 0, 0, 0)
        date_row.setSpacing(4)
        self.lbl_date_range = QLabel("～")
        self.lbl_date_range.setObjectName("meta")
        date_row.addWidget(self.chk_dates)
        date_row.addWidget(self.date_from)
        date_row.addWidget(self.lbl_date_range)
        date_row.addWidget(self.date_to)
        filters.addWidget(self.date_group)
        self.chk_hidden = QCheckBox()
        self.chk_hidden.setChecked(False)
        filters.addWidget(self.chk_hidden)
        self.sort_box = QGroupBox()
        self.combo_sort = DropHintCombo()
        self.combo_sort.setMinimumWidth(128)
        sort_lay = QHBoxLayout(self.sort_box)
        sort_lay.setContentsMargins(10, 8, 10, 8)
        sort_lay.addWidget(self.combo_sort)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)
        filter_row.addWidget(self.filter_box, stretch=1)
        filter_row.addWidget(self.sort_box, alignment=Qt.AlignmentFlag.AlignTop)
        outer.addLayout(filter_row)

        body = QHBoxLayout()
        self.list = QListWidget()
        self.list.setViewMode(QListView.ViewMode.IconMode)
        self.list.setFlow(QListView.Flow.LeftToRight)
        self.list.setWrapping(True)
        self.list.setMovement(QListView.Movement.Static)
        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setUniformItemSizes(True)
        self.list.setIconSize(_LIST_ICON)
        self.list.setGridSize(_LIST_GRID)
        self.list.setSpacing(0)
        self.list.setMinimumWidth(220)
        self.list.setWordWrap(False)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._list_menu)
        body.addWidget(self.list)

        preview_col = QVBoxLayout()
        self.meta = QLabel()
        self.meta.setObjectName("meta")
        self.meta.setWordWrap(True)
        preview_stage = QWidget()
        preview_host = QWidget()
        self._preview_stack = QStackedLayout(preview_host)
        self.preview = PreviewCanvas()
        self.guide_page = GuidePage()
        self.guide = self.guide_page.title
        self.scan_count = self.guide_page.scan_count
        self.scan_progress = self.guide_page.scan_progress
        self._preview_stack.addWidget(self.preview)
        self._preview_stack.addWidget(self.guide_page)
        overlay = QGridLayout(preview_stage)
        overlay.setContentsMargins(0, 0, 0, 0)
        overlay.addWidget(preview_host, 0, 0)
        self.btn_star = QToolButton()
        self.btn_star.setObjectName("starOverlay")
        self.btn_star.setCheckable(True)
        self.btn_star.setFixedSize(48, 48)
        self.btn_star.setAutoRaise(True)
        overlay.addWidget(
            self.btn_star, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        self.btn_star.raise_()
        self.output_status = QLabel()
        self.output_status.setObjectName("outputStatus")
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.addWidget(self.meta, stretch=1)
        meta_row.addWidget(self.output_status, alignment=Qt.AlignmentFlag.AlignTop)
        preview_col.addLayout(meta_row)
        preview_col.addWidget(preview_stage, stretch=1)
        self.lbl_in = QLabel()
        self.lbl_in.setObjectName("meta")
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setObjectName("rangeIn")
        self.lbl_out = QLabel()
        self.lbl_out.setObjectName("meta")
        self.timeline_out = QSlider(Qt.Orientation.Horizontal)
        self.timeline_out.setObjectName("rangeOut")
        self.chk_loop = QCheckBox()
        self.chk_audio = QCheckBox()
        self.chk_audio.setChecked(True)
        row_in = QHBoxLayout()
        row_in.addWidget(self.lbl_in)
        row_in.addWidget(self.timeline, stretch=1)
        row_out = QHBoxLayout()
        row_out.addWidget(self.lbl_out)
        row_out.addWidget(self.timeline_out, stretch=1)
        loop_row = QHBoxLayout()
        loop_row.setContentsMargins(0, 0, 0, 0)
        loop_row.setSpacing(16)
        loop_row.addWidget(self.chk_loop)
        loop_row.addWidget(self.chk_audio)
        loop_row.addStretch()
        preview_col.addLayout(row_in)
        preview_col.addLayout(row_out)
        preview_col.addLayout(loop_row)
        body.addLayout(preview_col, stretch=1)
        outer.addLayout(body, stretch=1)

        # 幅が足りないときだけ、手動ぼかし・拡大の枠をここ（下の段の上）へ移す
        self._tools_host = QWidget()
        self._tools_row = QHBoxLayout(self._tools_host)
        self._tools_row.setContentsMargins(0, 0, 0, 0)
        self._tools_row.addStretch()
        self._tools_host.setVisible(False)
        bar_host = QWidget()
        bar = QHBoxLayout(bar_host)
        bar.setContentsMargins(0, 0, 0, 0)
        self._bar = bar
        self.btn_prev = _bar_button()
        self.btn_next = _bar_button()
        self.btn_send = _bar_button()
        self.btn_panic = _bar_button()
        self.btn_send.setObjectName("sendButton")
        self.btn_panic.setObjectName("panicButton")
        self.btn_manual = _bar_button()
        self.btn_rot_left = _bar_button()
        self.btn_rot_right = _bar_button()
        self.btn_loupe = _bar_button()
        self.btn_loupe.setCheckable(True)
        self.lbl_loupe = QLabel()
        self.lbl_loupe.setObjectName("meta")
        self.slider_loupe = QSlider(Qt.Orientation.Horizontal)
        self.slider_loupe.setRange(MIN_LOUPE_PX, MAX_LOUPE_PX)
        self.slider_loupe.setValue(OPERATOR_LOUPE_PX)
        self.slider_loupe.setMinimumWidth(120)
        self.slider_loupe.setMaximumWidth(200)
        self.btn_false_face = _bar_button()
        self.btn_undo = _bar_button()
        self.btn_rect = _bar_button()
        self.btn_brush = _bar_button()
        self.btn_clear_marks = _bar_button()
        self.lbl_brush = QLabel()
        self.lbl_brush.setObjectName("meta")
        self.slider_brush = QSlider(Qt.Orientation.Horizontal)
        self.slider_brush.setRange(MIN_BRUSH_WIDTH, MAX_BRUSH_WIDTH)
        self.slider_brush.setValue(DEFAULT_BRUSH_WIDTH)
        self.slider_brush.setMinimumWidth(120)
        self.slider_brush.setMaximumWidth(200)
        self.btn_manual.setMinimumWidth(88)
        self.btn_rot_left.setMinimumWidth(72)
        self.btn_rot_right.setMinimumWidth(72)
        self.btn_false_face.setMinimumWidth(120)
        self.btn_false_face.setVisible(False)
        self.btn_false_face.setCheckable(True)
        self.btn_false_undo = _bar_button()
        self.btn_false_undo.setMinimumWidth(96)
        self.btn_false_undo.setVisible(False)
        self.btn_prep_videos.setMinimumWidth(108)
        self.btn_play = _bar_button()
        self.btn_lang = _bar_button()
        self.btn_lang.setMinimumWidth(56)
        self.btn_help = _bar_button()
        self.btn_help.setMinimumWidth(56)
        self.btn_manual.setCheckable(True)
        self.btn_rect.setCheckable(True)
        self.btn_brush.setCheckable(True)
        self.btn_rect.setMinimumWidth(108)
        self.manual_tools = QFrame()
        self.manual_tools.setObjectName("manualTools")
        tools = QHBoxLayout(self.manual_tools)
        tools.setContentsMargins(8, 4, 8, 4)
        tools.setSpacing(6)
        self.loupe_tools = QFrame()
        self.loupe_tools.setObjectName("manualTools")
        loupe_row = QHBoxLayout(self.loupe_tools)
        loupe_row.setContentsMargins(8, 4, 8, 4)
        loupe_row.setSpacing(6)
        loupe_row.addWidget(self.lbl_loupe)
        loupe_row.addWidget(self.slider_loupe)
        for widget in (
            self.btn_prev,
            self.btn_next,
            self.btn_send,
            self.btn_panic,
            self.btn_manual,
        ):
            widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            bar.addWidget(widget)
        for widget in (
            self.btn_rect,
            self.btn_brush,
            self.lbl_brush,
            self.slider_brush,
            self.btn_undo,
            self.btn_clear_marks,
        ):
            tools.addWidget(widget)
        bar.addWidget(self.manual_tools)
        bar.addWidget(self.btn_rot_left)
        bar.addWidget(self.btn_rot_right)
        bar.addWidget(self.btn_loupe)
        bar.addWidget(self.loupe_tools)
        bar.addStretch()
        bar.addWidget(self.btn_play)
        bar.addWidget(self.btn_false_face)
        bar.addWidget(self.btn_false_undo)
        bar.addWidget(self.btn_lang)
        bar.addWidget(self.btn_help)
        outer.addWidget(self._tools_host)
        outer.addWidget(bar_host)
        self._bar_host = bar_host
        # 下の段が収まらないときだけ記号だけにするボタン（前・次・送る・隠すは文字も残す）
        self._compact_buttons = (
            self.btn_manual,
            self.btn_rot_left,
            self.btn_rot_right,
            self.btn_loupe,
            self.btn_play,
            self.btn_false_face,
            self.btn_false_undo,
            self.btn_lang,
            self.btn_help,
        )
        self._bar_compact = False
        self._bar_full_need = 0
        self._bar_min_w: dict[QToolButton, int] = {}

        self._relayout_timer = QTimer(self)
        self._relayout_timer.setSingleShot(True)
        self._relayout_timer.timeout.connect(self._relayout_list)
        self.setCentralWidget(root)
        self._bind()
        self.set_media_kind(None)
        self._set_manual(False)
        self._apply_loupe(False)
        self.retranslate()
        self._relayout_list()
        self.show_start([])

    def _fit_initial_size(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            return
        avail = screen.availableGeometry()
        width = min(1280, max(900, avail.width() - 48))
        height = min(800, max(560, avail.height() - 72))
        self.resize(width, height)

    def clamp_to_screen(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        width = min(self.width(), max(self.minimumWidth(), avail.width() - 24))
        height = min(self.height(), max(self.minimumHeight(), avail.height() - 48))
        if width != self.width() or height != self.height():
            self.resize(width, height)
        frame = self.frameGeometry()
        x = min(max(avail.x(), frame.x()), avail.right() - frame.width() + 1)
        y = min(max(avail.y(), frame.y()), avail.bottom() - frame.height() + 1)
        if x != frame.x() or y != frame.y():
            self.move(x, y)

    def _bind(self) -> None:
        self.btn_folder.clicked.connect(self.open_folder_requested.emit)
        self.btn_send.clicked.connect(self.send_requested.emit)
        self.btn_panic.clicked.connect(self.panic_requested.emit)
        self.btn_prev.clicked.connect(self.prev_requested.emit)
        self.btn_next.clicked.connect(self.next_requested.emit)
        self.btn_play.clicked.connect(self.play_requested.emit)
        self.btn_star.clicked.connect(self.star_requested.emit)
        self.btn_undo.clicked.connect(self.undo_requested.emit)
        self.btn_prep_videos.clicked.connect(self.prepare_videos_requested.emit)
        self.guide_page.pick_requested.connect(self.open_folder_requested.emit)
        self.guide_page.recent_requested.connect(self.recent_folder_requested.emit)
        self.guide_page.clear_filters_requested.connect(self.clear_filters_requested.emit)
        self.btn_clear_marks.clicked.connect(self.clear_marks_requested.emit)
        self.slider_brush.valueChanged.connect(self._on_brush_width)
        self.slider_loupe.valueChanged.connect(self._on_loupe_px)
        self.btn_star.toggled.connect(self._on_star_toggled)
        self.btn_enhance.clicked.connect(self.enhance_cycle_requested.emit)
        self.btn_loupe.toggled.connect(self._on_loupe)
        self.btn_false_undo.clicked.connect(self.false_undo_requested.emit)
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        self.list.currentRowChanged.connect(self.item_selected.emit)
        self.preview.mark_added.connect(self.mark_added.emit)
        self.preview.clicked.connect(self.play_requested.emit)
        self.preview.region_clicked.connect(self.region_clicked.emit)
        self.btn_help.clicked.connect(self._show_help)
        self.btn_lang.clicked.connect(self.language_cycle_requested.emit)
        self.btn_false_face.toggled.connect(self._sync_false_face_caption)
        self.btn_rot_left.clicked.connect(self.rotate_left_requested.emit)
        self.btn_rot_right.clicked.connect(self.rotate_right_requested.emit)
        self.btn_manual.clicked.connect(lambda: self._set_manual(self.btn_manual.isChecked()))
        self.btn_rect.clicked.connect(lambda: self._tool("rect"))
        self.btn_brush.clicked.connect(lambda: self._tool("stroke"))
        self.chk_face.toggled.connect(lambda _=False: self.settings_changed.emit())
        self.chk_text.toggled.connect(lambda _=False: self.settings_changed.emit())
        self.chk_loop.toggled.connect(lambda _=False: self.loop_changed.emit())
        self.chk_audio.toggled.connect(lambda _=False: self.audio_changed.emit())
        for box in (
            self.chk_star_only,
            self.chk_photos,
            self.chk_videos,
            self.chk_filter_face,
            self.chk_dates,
            self.chk_hidden,
        ):
            box.toggled.connect(lambda _=False: self.filters_changed.emit())
        self.combo_place.currentIndexChanged.connect(lambda _=0: self.filters_changed.emit())
        self.combo_folder.currentIndexChanged.connect(lambda _=0: self.filters_changed.emit())
        self.combo_sort.currentIndexChanged.connect(lambda _=0: self.filters_changed.emit())
        self.chk_dates.toggled.connect(self._sync_date_style)
        self.date_from.picked.connect(self._on_date_picked)
        self.date_to.picked.connect(self._on_date_picked)
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
        # ショートカットが拾えずに窓まで届いたテンキーの受け皿（片手の操作と緊急は必ず効かせる）
        self._fallback_keys = {
            Qt.Key.Key_0: self.panic_requested,
            Qt.Key.Key_Escape: self.panic_requested,
            Qt.Key.Key_4: self.prev_requested,
            Qt.Key.Key_6: self.next_requested,
            Qt.Key.Key_5: self.play_requested,
            Qt.Key.Key_Enter: self.send_requested,
            Qt.Key.Key_Return: self.send_requested,
        }

    def keyPressEvent(self, event) -> None:  # noqa: N802
        modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
        signal = self._fallback_keys.get(event.key())
        if signal is not None and modifiers == Qt.KeyboardModifier.NoModifier:
            event.accept()
            signal.emit()
            return
        super().keyPressEvent(event)

    def _set_manual(self, on: bool) -> None:
        if on:
            self._apply_loupe(False)
        self.btn_manual.setChecked(on)
        if on:
            if self.preview.mode not in {"rect", "stroke"}:
                self._tool("rect")
                return
        else:
            self.preview.mode = "off"
        self._sync_manual_extras()

    def _tool(self, mode: str) -> None:
        self._apply_loupe(False)
        self.btn_manual.setChecked(True)
        self.preview.mode = mode
        self._sync_manual_extras()

    def _sync_manual_extras(self) -> None:
        on = self.btn_manual.isChecked()
        stroke = on and self.preview.mode == "stroke"
        self.btn_brush.setChecked(on and self.preview.mode == "stroke")
        self.btn_rect.setChecked(on and self.preview.mode == "rect")
        self.manual_tools.setVisible(on)
        self._place_tool_frames()
        self.lbl_brush.setVisible(stroke)
        self.slider_brush.setVisible(stroke)

    def _mode(self, mode: str) -> None:
        if mode in {"rect", "stroke"}:
            self._tool(mode)
            return
        self._set_manual(False)

    def _on_date_picked(self) -> None:
        # カレンダーで日付を選んだら、その絞り込みを効かせる（選んだのに効かない、を防ぐ）
        if not self.chk_dates.isChecked():
            self.chk_dates.setChecked(True)

    def _sync_date_style(self, *_args) -> None:
        inactive = not self.chk_dates.isChecked()
        for edit in (self.date_from, self.date_to):
            edit.setProperty("inactive", inactive)
            _repolish(edit)

    def set_prep_text(self, text: str) -> None:
        """写真の下準備の進み具合。狭くて隠れたときは🎦のカーソル説明で見られる。"""
        self.prep_label.setText(text)
        self.prep_label.setToolTip(t(self.lang, "photo_prep_tip") if text else "")
        self._prep_tip = text
        self._sync_prep_tip()

    def _sync_prep_tip(self) -> None:
        tip = t(self.lang, "prepare_videos")
        if self._prep_tip:
            tip = f"{tip}\n{self._prep_tip}"
        self.btn_prep_videos.setToolTip(tip)

    def set_library_ready(self, ready: bool) -> None:
        """フォルダを開くまで、絞り込み・並び順・動画の下準備は押せなくする（押しても何も起きないため）。"""
        for widget in (self.filter_box, self.sort_box, self.btn_prep_videos):
            widget.setEnabled(ready)

    def set_dates_available(self, available: bool) -> None:
        """撮影日のわかるファイルが無いときは、日付の絞り込みを薄くして押せなくする。"""
        for edit in (self.date_from, self.date_to):
            edit.setSpecialValueText("" if available else "----/--/--")
            if not available:
                edit.blockSignals(True)
                edit.setDate(edit.minimumDate())
                edit.blockSignals(False)
        if not available and self.chk_dates.isChecked():
            self.chk_dates.setChecked(False)
        self.date_group.setEnabled(available)
        tip = "" if available else t(self.lang, "filter_no_dates")
        self.date_group.setToolTip(tip)

    def set_live_probe(self, probe) -> None:
        """いま確認している物が、配信に出している物と同じかを返す関数。状態の表示に使う。"""
        self._live_probe = probe

    def _on_brush_width(self, value: int) -> None:
        self.preview.brush_width = value
        self.brush_width_changed.emit(value)

    def _on_loupe_px(self, value: int) -> None:
        self.preview.set_loupe_px(value)

    def _on_star_toggled(self, on: bool) -> None:
        self.btn_star.setText("⭐" if on else "☆")
        self.btn_star.setToolTip(t(self.lang, "star"))

    def _on_loupe(self, on: bool) -> None:
        self._apply_loupe(on)

    def _apply_loupe(self, on: bool) -> None:
        self.btn_loupe.blockSignals(True)
        self.btn_loupe.setChecked(on)
        self.btn_loupe.blockSignals(False)
        if on:
            self.btn_manual.setChecked(False)
            self.preview.mode = "off"
            self._sync_manual_extras()
        self.loupe_tools.setVisible(on)
        self._place_tool_frames()
        self.preview.set_loupe(on)
        self.preview.set_loupe_px(self.slider_loupe.value())

    def closeEvent(self, event) -> None:  # noqa: N802
        super().closeEvent(event)
        if event.isAccepted():
            self.closing.emit()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        exclude_from_capture(self)
        self._place_tool_frames(remeasure=True)

    def retranslate(self) -> None:
        lang = self.lang
        _caption(self.btn_folder, "📁", t(lang, "btn_folder"), t(lang, "open_folder"))
        _caption(self.btn_send, "⬆", t(lang, "btn_send"), t(lang, "send"))
        _caption(self.btn_panic, "■", t(lang, "btn_panic"), t(lang, "panic"))
        _caption(self.btn_prev, "◀", t(lang, "btn_prev"), t(lang, "prev"))
        _caption(self.btn_next, "▶", t(lang, "btn_next"), t(lang, "next"))
        self.set_playing(self._playing)
        self.btn_star.setText("⭐" if self.btn_star.isChecked() else "☆")
        self.btn_star.setToolTip(t(lang, "star"))
        _caption(self.btn_undo, "↩", t(lang, "btn_undo"), t(lang, "undo"))
        _caption(self.btn_manual, "💧", t(lang, "btn_manual"), t(lang, "manual"))
        _caption(self.btn_rot_left, "↺", t(lang, "btn_rot_left"), t(lang, "rot_left"))
        _caption(self.btn_rot_right, "↻", t(lang, "btn_rot_right"), t(lang, "rot_right"))
        _caption(self.btn_loupe, "🔍", t(lang, "btn_loupe"), t(lang, "loupe"))
        self.lbl_loupe.setText(t(lang, "loupe_size"))
        _caption(self.btn_rect, "▢", t(lang, "btn_rect"), t(lang, "rect"))
        _caption(self.btn_brush, "🖌", t(lang, "btn_brush"), t(lang, "brush"))
        _caption(self.btn_clear_marks, "✕", t(lang, "btn_clear_marks"), t(lang, "clear_marks"))
        self.lbl_brush.setText(t(lang, "brush_width"))
        _caption(self.btn_prep_videos, "🎦", t(lang, "btn_prep_videos"), t(lang, "prepare_videos"))
        self._sync_prep_tip()
        _caption(self.btn_settings, "⚙", t(lang, "btn_settings"), t(lang, "settings"))
        # 下の名前は「押すと何語になるか」。あ/A だけでは行き先が分からないため
        _caption(self.btn_lang, "あ/A", t(lang, "lang_next"), t(lang, "language"))
        _caption(self.btn_help, "?", t(lang, "btn_help"), t(lang, "help_title"))
        self._sync_false_face_caption()
        _caption(self.btn_false_undo, "↩", t(lang, "btn_false_undo"), t(lang, "false_undo"))
        # 🔍 は拡大のボタンで使うので、絞り込みの見出しには付けない
        self.filter_box.setTitle(t(lang, "filters_title"))
        self.sort_box.setTitle(t(lang, "sort_title"))
        self.chk_face.setText(t(lang, "face_blur"))
        self.chk_face.setToolTip(t(lang, "face_blur_tip"))
        self.chk_text.setText(t(lang, "text_blur"))
        self.chk_text.setToolTip(t(lang, "text_blur_tip"))
        self.set_enhance_level(self.enhance_level)
        self.chk_loop.setText(t(lang, "loop"))
        self.chk_loop.setToolTip(t(lang, "loop_tip"))
        self.chk_audio.setText(t(lang, "audio"))
        self.chk_audio.setToolTip(t(lang, "audio_hint"))
        self.chk_star_only.setText("⭐")
        self.chk_star_only.setToolTip(t(lang, "filter_star"))
        self.chk_photos.setText(t(lang, "filter_photo"))
        self.chk_photos.setToolTip(t(lang, "filter_photo_tip"))
        self.chk_videos.setText(t(lang, "filter_video"))
        self.chk_videos.setToolTip(t(lang, "filter_video_tip"))
        self.chk_filter_face.setText("😊")
        self.chk_filter_face.setToolTip(t(lang, "filter_face"))
        self.chk_dates.setText(t(lang, "filter_dates"))
        self.chk_dates.setToolTip(t(lang, "filter_dates_tip"))
        self.chk_hidden.setText(t(lang, "filter_hidden"))
        self.chk_hidden.setToolTip(t(lang, "filter_hidden_tip"))
        self._fill_sort()
        self._set_combo_all(self.combo_place, "filter_place_all")
        if self.combo_place.count() >= 2 and self.combo_place.itemData(1) == PLACE_NONE:
            self.combo_place.setItemText(1, t(lang, "filter_gps_no"))
        self._set_combo_all(self.combo_folder, "filter_folder_all")
        self.lbl_in.setText(t(lang, "range_in"))
        self.lbl_out.setText(t(lang, "range_out"))
        self.timeline.setToolTip(t(lang, "range_in_tip"))
        self.timeline_out.setToolTip(t(lang, "range_out_tip"))
        self.guide_page.set_lang(lang)
        if not self.date_group.isEnabled():
            self.date_group.setToolTip(t(lang, "filter_no_dates"))
        self._sync_date_style()
        self.refresh_status()
        self._place_tool_frames(remeasure=True)

    def _set_combo_all(self, combo: QComboBox, key: str) -> None:
        if combo.count() == 0:
            combo.addItem(t(self.lang, key), "")
            return
        combo.setItemText(0, t(self.lang, key))

    def set_places(self, names: list[str], selected: str) -> None:
        combo = self.combo_place
        if combo.view().isVisible():
            return
        wanted = ["" , PLACE_NONE, *names]
        current = [combo.itemData(i) for i in range(combo.count())]
        if current == wanted and str(combo.currentData() or "") == selected:
            return
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(t(self.lang, "filter_place_all"), "")
        combo.addItem(t(self.lang, "filter_gps_no"), PLACE_NONE)
        for name in names:
            combo.addItem(name, name)
        index = combo.findData(selected)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def set_folders(self, names: list[str], selected: str) -> None:
        if self.combo_folder.view().isVisible():
            return
        self._fill_combo(self.combo_folder, "filter_folder_all", names, selected)

    def _fill_combo(self, combo: QComboBox, all_key: str, names: list[str], selected: str) -> None:
        wanted = ["", *names]
        current = [combo.itemData(i) for i in range(combo.count())]
        if current == wanted and str(combo.currentData() or "") == selected:
            return
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

    def selected_sort(self) -> str:
        return parse_list_sort(self.combo_sort.currentData())

    def set_sort(self, mode: str) -> None:
        wanted = parse_list_sort(mode)
        index = self.combo_sort.findData(wanted)
        if index < 0:
            return
        self.combo_sort.blockSignals(True)
        self.combo_sort.setCurrentIndex(index)
        self.combo_sort.blockSignals(False)

    def _fill_sort(self) -> None:
        current = self.selected_sort() if self.combo_sort.count() else "date_asc"
        self.combo_sort.blockSignals(True)
        self.combo_sort.clear()
        self.combo_sort.addItem(t(self.lang, "sort_date_asc"), "date_asc")
        self.combo_sort.addItem(t(self.lang, "sort_date_desc"), "date_desc")
        self.combo_sort.addItem(t(self.lang, "sort_name"), "name")
        index = self.combo_sort.findData(current)
        self.combo_sort.setCurrentIndex(index if index >= 0 else 0)
        self.combo_sort.blockSignals(False)

    def set_enhance_level(self, level: str) -> None:
        self.enhance_level = parse_enhance_level(level)
        lang = self.lang
        state = t(lang, f"enhance_{self.enhance_level}")
        self.btn_enhance.setText(f"✨{t(lang, 'enhance_title')}\n{state}")
        self.btn_enhance.setToolTip(t(lang, "enhance_hint"))

    def set_playing(self, playing: bool) -> None:
        self._playing = bool(playing)
        lang = self.lang
        if self._playing:
            _caption(self.btn_play, "⏹", t(lang, "btn_stop"), t(lang, "pause"))
            return
        _caption(self.btn_play, "⏯", t(lang, "btn_play"), t(lang, "play"))

    def _sync_false_face_caption(self) -> None:
        lang = self.lang
        state = t(lang, "toggle_on" if self.btn_false_face.isChecked() else "toggle_off")
        # 狭いときは名前を外し、ON／OFF だけ残す（名前はカーソル説明に出る）
        name = "" if self.btn_false_face.property("compact") else t(lang, "btn_false_face")
        self.btn_false_face.setText(f"❗️{name}\n{state}")
        self.btn_false_face.setToolTip(t(lang, "false_face"))

    def _list_menu(self, pos) -> None:
        row = self.list.indexAt(pos).row()
        if row < 0:
            return
        menu = QMenu(self)
        key = "unhide_item" if self.chk_hidden.isChecked() else "hide_item"
        chosen = menu.addAction(t(self.lang, key))
        picked = menu.exec(self.list.mapToGlobal(pos)) is chosen
        menu.deleteLater()
        if picked:
            self.hide_item_requested.emit(row)

    def set_media_kind(self, kind: str | None) -> None:
        video = kind == "video"
        self.preview.click_toggles_play = video
        self.preview.setCursor(
            Qt.CursorShape.PointingHandCursor if video else Qt.CursorShape.ArrowCursor
        )
        for widget in (
            self.btn_play,
            self.lbl_in,
            self.timeline,
            self.lbl_out,
            self.timeline_out,
            self.chk_loop,
            self.chk_audio,
        ):
            widget.setVisible(video)
        self._place_tool_frames(remeasure=True)

    def set_range_visible(self, visible: bool) -> None:
        self.set_media_kind("video" if visible else "image")

    def show_guide(
        self,
        text: str,
        *,
        done: int | None = None,
        total: int | None = None,
        pick: bool = False,
        recents: list[str] | None = None,
    ) -> None:
        """確認欄に知らせを出す。案内と同じ文を上の行に重ねて出さない。"""
        self.guide_page.show_message(text, done=done, total=total, pick=pick, recents=recents)
        self._show_guide_page()

    def show_start(self, recents: list[str]) -> None:
        """最初の案内（フォルダを選ぶボタンと最近のフォルダ）。"""
        self.guide_page.show_start(recents)
        self._show_guide_page()

    def show_filtered_empty(self) -> None:
        """絞り込みで全部隠れたとき。フォルダが空と言わず、解除ボタンを出す。"""
        self.guide_page.show_filtered_empty()
        self._show_guide_page()

    def _show_guide_page(self) -> None:
        self.meta.setText("")
        self.meta.setToolTip("")
        self._preview_stack.setCurrentWidget(self.guide_page)
        self.btn_star.setVisible(False)

    def set_scan_progress(self, done: int, total: int) -> None:
        if self._preview_stack.currentWidget() is not self.guide_page:
            return
        self.guide_page.set_scan_progress(done, total)

    def reveal_preview(self) -> None:
        self._preview_stack.setCurrentWidget(self.preview)
        self.btn_star.setVisible(True)

    def showing_guide(self) -> bool:
        return self._preview_stack.currentWidget() is self.guide_page

    def set_items(
        self,
        items: list[MediaItem],
        labels: list[str],
        icons: list[QPixmap | None] | None = None,
        tips: list[str] | None = None,
        rotations: list[int] | None = None,
    ) -> None:
        paths = [str(item.path) for item in items]
        same = paths == self._list_paths and self.list.count() == len(paths)
        if same:
            for index, label in enumerate(labels):
                row = self.list.item(index)
                if row is None:
                    break
                row.setText(label)
                if tips and index < len(tips):
                    row.setToolTip(tips[index])
                rot = rotations[index] if rotations and index < len(rotations) else 0
                if int(row.data(_ROLE_ROT) or 0) != int(rot):
                    self.set_row_rotation(index, rot)
                pixmap = icons[index] if icons and index < len(icons) else None
                if pixmap is not None and row.data(_ROLE_PIX) is not pixmap:
                    self.set_row_icon(index, pixmap, video=items[index].kind == "video")
            return
        self._list_paths = paths
        self.list.blockSignals(True)
        self.list.clear()
        for index, label in enumerate(labels):
            row = QListWidgetItem(label)
            pixmap = icons[index] if icons and index < len(icons) else None
            if pixmap is not None:
                row.setData(_ROLE_PIX, pixmap)
            kind = items[index].kind if index < len(items) else "image"
            row.setData(_ROLE_KIND, kind)
            row.setData(_ROLE_PATH, paths[index] if index < len(paths) else "")
            rot = rotations[index] if rotations and index < len(rotations) else 0
            row.setData(_ROLE_ROT, int(rot))
            fitted = self._row_icon(row)
            if fitted is not None and not fitted.isNull():
                row.setIcon(_list_icon(fitted))
            if tips and index < len(tips):
                row.setToolTip(tips[index])
            row.setSizeHint(self.list.gridSize())
            row.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.list.addItem(row)
        self.list.blockSignals(False)

    def set_row_icon(self, row: int, pixmap: QPixmap, *, video: bool = False) -> None:
        item = self.list.item(row)
        if item is None:
            return
        item.setData(_ROLE_PIX, pixmap)
        item.setData(_ROLE_KIND, "video" if video else "image")
        self._fit_cache.pop(
            (str(item.data(_ROLE_PATH) or ""), self.list.iconSize().width(), int(item.data(_ROLE_ROT) or 0), item.data(_ROLE_KIND)),
            None,
        )
        fitted = self._row_icon(item)
        if fitted is None or fitted.isNull():
            return
        item.setIcon(_list_icon(fitted))

    def set_row_rotation(self, row: int, degrees: int) -> None:
        item = self.list.item(row)
        if item is None:
            return
        item.setData(_ROLE_ROT, int(degrees))
        fitted = self._row_icon(item)
        if fitted is None or fitted.isNull():
            return
        item.setIcon(_list_icon(fitted))

    def _row_icon(self, item: QListWidgetItem) -> QPixmap | None:
        stored = item.data(_ROLE_PIX)
        if not isinstance(stored, QPixmap) or stored.isNull():
            return None
        rotation = int(item.data(_ROLE_ROT) or 0)
        kind = item.data(_ROLE_KIND)
        path = str(item.data(_ROLE_PATH) or "")
        size = self.list.iconSize().width()
        key = (path, size, rotation, kind)
        cached = self._fit_cache.get(key)
        if cached is not None and not cached.isNull():
            return cached
        if rotation:
            stored = stored.transformed(
                QTransform().rotate(rotation),
                Qt.TransformationMode.FastTransformation,
            )
        if kind == "video":
            stored = with_video_mark(stored, size)
        fitted = self._fit_icon(stored)
        if fitted is not None:
            self._fit_cache[key] = fitted
        return fitted

    def _fit_icon(self, pixmap: QPixmap | None) -> QPixmap | None:
        if pixmap is None or pixmap.isNull():
            return None
        size = self.list.iconSize()
        if size.width() < 2:
            return pixmap
        return pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.prep_label.setVisible(self.width() >= _PREP_LABEL_MIN_W)
        self._place_tool_frames()
        self._relayout_list(rescale=False)
        self._relayout_timer.start(60)

    def _relayout_list(self, rescale: bool = True) -> None:
        body = max(720, self.width() - 24)
        list_w = max(220, min(body - _PREVIEW_MIN, int(body * _LIST_SHARE)))
        two = list_w >= _TWO_COL_MIN
        cols = 2 if two else 1
        inner = max(160, list_w - 24)
        cell_w = inner // cols
        icon = max(140, min(520, cell_w - 6))
        if icon != self._fit_icon_size:
            self._fit_cache.clear()
            self._fit_icon_size = icon
        cell_h = icon + _CAPTION_H
        self.list.setIconSize(QSize(icon, icon))
        self.list.setGridSize(QSize(cell_w, cell_h))
        self.list.setMinimumWidth(list_w)
        self.list.setMaximumWidth(list_w)
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item is None:
                continue
            item.setSizeHint(QSize(cell_w, cell_h))
            if not rescale:
                continue
            fitted = self._row_icon(item)
            if fitted is not None:
                item.setIcon(_list_icon(fitted))

    def set_false_face_visible(self, visible: bool) -> None:
        if self.btn_false_face.isHidden() != (not visible):
            self.btn_false_face.setVisible(visible)
            self._place_tool_frames(remeasure=True)

    def _bar_need(self) -> int:
        """下の段のボタン（手動ぼかし・拡大の枠を除く）を並べるのに要る幅。"""
        bar = self._bar
        spacing = bar.spacing() if bar.spacing() >= 0 else 6
        widths = []
        for index in range(bar.count()):
            widget = bar.itemAt(index).widget()
            if widget is None or widget.isHidden():
                continue
            if widget is self.manual_tools or widget is self.loupe_tools:
                continue
            widths.append(widget.sizeHint().width())
        return sum(widths) + spacing * max(0, len(widths) - 1)

    def _set_bar_compact(self, on: bool) -> None:
        if self._bar_compact == on:
            return
        self._bar_compact = on
        for button in self._compact_buttons:
            if on:
                self._bar_min_w.setdefault(button, button.minimumWidth())
                button.setMinimumWidth(40)
            else:
                button.setMinimumWidth(self._bar_min_w.get(button, button.minimumWidth()))
            button.setProperty("compact", on)
            if button is not self.btn_false_face:
                button.setToolButtonStyle(
                    Qt.ToolButtonStyle.ToolButtonIconOnly
                    if on
                    else Qt.ToolButtonStyle.ToolButtonTextUnderIcon
                )
            _repolish(button)
        self._sync_false_face_caption()

    def _fit_bar(self, *, remeasure: bool = False) -> None:
        """下の段が収まらないときは、前・次・送る・隠す のほかを記号だけにする。"""
        # 出す前の窓は幅が仮の値なので決めない（出したときの大きさで決める）
        room = self._bar_host.width()
        if not self.isVisible() or room <= 0:
            return
        if remeasure:
            self._set_bar_compact(False)
        if not self._bar_compact:
            self._bar_full_need = self._bar_need()
            if self._bar_full_need > room:
                self._set_bar_compact(True)
        elif room >= self._bar_full_need:
            self._set_bar_compact(False)
            self._bar_full_need = self._bar_need()
            if self._bar_full_need > room:
                self._set_bar_compact(True)

    def _place_tool_frames(self, *, remeasure: bool = False) -> None:
        """枠はふだん元のボタンの右。下の段に収まらないときだけ、1 段上に並べる。"""
        bar = getattr(self, "_bar", None)
        if bar is None or not hasattr(self, "_bar_host"):
            return
        self._fit_bar(remeasure=remeasure)
        frames = [
            (self.manual_tools, self.btn_manual),
            (self.loupe_tools, self.btn_loupe),
        ]
        spacing = bar.spacing() if bar.spacing() >= 0 else 6
        width = 0
        for index in range(bar.count()):
            widget = bar.itemAt(index).widget()
            if widget is None or widget.isHidden():
                continue
            if any(widget is frame for frame, _ in frames):
                continue
            width += widget.sizeHint().width() + spacing
        for frame, _ in frames:
            if not frame.isHidden():
                width += frame.sizeHint().width() + spacing
        inline = width <= max(0, self.centralWidget().width() if self.centralWidget() else 0)
        for frame, anchor in frames:
            in_bar = bar.indexOf(frame) >= 0
            if inline and not in_bar:
                self._tools_row.removeWidget(frame)
                bar.insertWidget(bar.indexOf(anchor) + 1, frame)
            elif not inline and in_bar:
                bar.removeWidget(frame)
                # 手動ぼかし → 拡大 の順。最後の伸び縮みの前に入れて左に寄せる
                self._tools_row.insertWidget(self._tools_row.count() - 1, frame)
        if not inline:
            for frame, _ in frames:
                self._tools_row.removeWidget(frame)
            for frame, _ in frames:
                self._tools_row.insertWidget(self._tools_row.count() - 1, frame)
        self._tools_host.setVisible(
            not inline and any(not frame.isHidden() for frame, _ in frames)
        )

    def set_false_undo_visible(self, visible: bool) -> None:
        if self.btn_false_undo.isHidden() != (not visible):
            self.btn_false_undo.setVisible(visible)
            self._place_tool_frames(remeasure=True)

    def _help_dialog(self) -> HelpDialog:
        return HelpDialog(self, self.lang)

    def _show_help(self) -> None:
        dialog = self._help_dialog()
        dialog.exec()
        dialog.deleteLater()

    def refresh_status(self) -> None:
        reason = self._gate.reason
        live = reason is OutputReason.LIVE
        self.btn_send.setEnabled(self._gate.ready)
        if bool(self.btn_send.property("live")) != live:
            self.btn_send.setProperty("live", live)
            _repolish(self.btn_send)
        if live:
            key = "status_live_this" if self._live_probe() else "status_live_other"
            state = "live"
        else:
            key, state = _STATUS_KEYS.get(reason, ("status_hidden", "hidden"))
        self.output_status.setText(t(self.lang, key))
        self.output_status.setToolTip(t(self.lang, "status_tip"))
        if self.output_status.property("state") != state:
            self.output_status.setProperty("state", state)
            _repolish(self.output_status)
