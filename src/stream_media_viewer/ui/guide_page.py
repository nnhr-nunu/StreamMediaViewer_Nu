"""確認欄の案内（最初・読み込み中・何も出せないとき）。配信用の窓には出さない。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from stream_media_viewer import OUTPUT_WINDOW_TITLE
from stream_media_viewer.i18n import t

# 最初の案内に並べる最近のフォルダの数（多いと案内が埋もれる）
MAX_RECENTS = 4


class GuidePage(QWidget):
    """案内は 3 種類。最初（フォルダ選び）／知らせ（読み込み中・空）／絞り込みで空。

    文字だけで終わらせず、次にやることをその場のボタンで押せるようにする。
    """

    pick_requested = Signal()
    recent_requested = Signal(str)
    clear_filters_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._lang = "ja"
        self._mode = "start"
        self._text = ""
        self._pick = False
        self._recents: list[str] = []
        self.title = QLabel()
        self.title.setObjectName("guide")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)
        self.scan_count = QLabel()
        self.scan_count.setObjectName("meta")
        self.scan_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scan_progress = QProgressBar()
        self.scan_progress.setTextVisible(True)
        self.scan_progress.setFormat("%v / %m")
        self.scan_progress.setMinimumHeight(18)
        self.scan_progress.setFixedWidth(360)
        self.btn_pick = QPushButton()
        self.btn_pick.setObjectName("guidePick")
        self.btn_pick.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick.clicked.connect(self.pick_requested.emit)
        self.recent_title = QLabel()
        self.recent_title.setObjectName("guideNote")
        self.recent_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._recent_host = QWidget()
        self._recent_col = QVBoxLayout(self._recent_host)
        self._recent_col.setContentsMargins(0, 0, 0, 0)
        self._recent_col.setSpacing(6)
        self.btn_clear_filters = QPushButton()
        self.btn_clear_filters.setObjectName("guideAction")
        self.btn_clear_filters.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_filters.clicked.connect(self.clear_filters_requested.emit)
        self.steps = QLabel()
        self.steps.setObjectName("guideSteps")
        self.obs = QLabel()
        self.obs.setObjectName("guideNote")
        self.obs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.obs.setWordWrap(True)

        # 低い窓でも潰れないよう、中身はスクロールできる箱に入れる
        self._body = QWidget()
        self._body.setObjectName("guideBody")
        scroll = QScrollArea(self)
        scroll.setObjectName("guideScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._body)
        scroll.viewport().setAutoFillBackground(False)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._compact = False

        col = QVBoxLayout(self._body)
        col.setSpacing(8)
        col.setContentsMargins(24, 0, 24, 0)
        col.addStretch()
        center = Qt.AlignmentFlag.AlignHCenter
        for widget in (
            self.title,
            self.scan_count,
            self.scan_progress,
            self.btn_pick,
            self.recent_title,
            self._recent_host,
            self.btn_clear_filters,
            self.steps,
            self.obs,
        ):
            # 折り返す文は横いっぱいに置く（中寄せの指定をすると幅が足りず文が切れる）
            wraps = isinstance(widget, QLabel) and widget.wordWrap()
            if wraps:
                col.addWidget(widget)
            else:
                col.addWidget(widget, alignment=center)
        col.addStretch()
        self._render()

    @property
    def mode(self) -> str:
        return self._mode

    def set_lang(self, lang: str) -> None:
        self._lang = lang
        self._render()

    def show_start(self, recents: list[str]) -> None:
        """最初の案内。フォルダを選ぶボタンと、最近のフォルダを出す。"""
        self._mode = "start"
        self._recents = list(recents)[:MAX_RECENTS]
        self._render()

    def show_message(
        self,
        text: str,
        *,
        done: int | None = None,
        total: int | None = None,
        pick: bool = False,
        recents: list[str] | None = None,
    ) -> None:
        """読み込み中や空のときの知らせ。pick=True ならフォルダを選び直すボタンも出す。"""
        self._mode = "message"
        self._text = text
        self._pick = pick
        self._recents = list(recents or [])[:MAX_RECENTS]
        scanning = done is not None and total is not None
        self.scan_progress.setVisible(scanning)
        self.scan_count.setVisible(scanning)
        if scanning:
            self.set_scan_progress(done or 0, total or 0)
        self._render()

    def show_filtered_empty(self) -> None:
        self._mode = "filtered"
        self._render()

    def set_scan_progress(self, done: int, total: int) -> None:
        self.scan_progress.setVisible(True)
        self.scan_count.setVisible(True)
        if total <= 0:
            self.scan_progress.setRange(0, 0)
            key = "scanning_found" if done > 0 else "scanning_search"
            self.scan_count.setText(t(self._lang, key).format(n=done))
            return
        self.scan_progress.setRange(0, total)
        self.scan_progress.setValue(max(0, min(done, total)))
        self.scan_count.setText(f"{done} / {total}")

    def _render(self) -> None:
        lang = self._lang
        start = self._mode == "start"
        message = self._mode == "message"
        if start:
            self.title.setText(t(lang, "start_title"))
        elif message:
            self.title.setText(self._text)
        else:
            self.title.setText(t(lang, "filtered_empty"))
        if not message:
            self.scan_progress.setVisible(False)
            self.scan_count.setVisible(False)
        show_pick = start or (message and self._pick)
        self.btn_pick.setText("📁  " + t(lang, "start_pick"))
        self.btn_pick.setVisible(show_pick)
        self._fill_recents(self._recents if show_pick else [])
        self.recent_title.setText(t(lang, "start_recent"))
        self.btn_clear_filters.setText(t(lang, "clear_filters"))
        self.btn_clear_filters.setVisible(self._mode == "filtered")
        self.steps.setText(t(lang, "start_steps"))
        self.obs.setText(t(lang, "start_obs").format(title=OUTPUT_WINDOW_TITLE))
        self._fit_height()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._fit_height()

    def _fit_height(self) -> None:
        """高さが足りないときは手順と OBS の説明を畳む（？の使い方にも同じことがある）。"""
        start = self._mode == "start"
        self.steps.setVisible(start)
        self.obs.setVisible(start)
        if not start or self.height() <= 0:
            return
        need = self._body.layout().sizeHint().height()
        self._compact = need > self.height()
        self.steps.setVisible(not self._compact)
        self.obs.setVisible(not self._compact)

    def _fill_recents(self, recents: list[str]) -> None:
        while self._recent_col.count():
            widget = self._recent_col.takeAt(0).widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()
        for path in recents:
            button = QPushButton(Path(path).name or path)
            button.setObjectName("guideRecent")
            button.setToolTip(path)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, p=path: self.recent_requested.emit(p))
            self._recent_col.addWidget(button)
        self.recent_title.setVisible(bool(recents))
        self._recent_host.setVisible(bool(recents))

    def recent_buttons(self) -> list[QPushButton]:
        found = []
        for index in range(self._recent_col.count()):
            widget = self._recent_col.itemAt(index).widget()
            if isinstance(widget, QPushButton):
                found.append(widget)
        return found
