"""右下の ？（使い方）。キーの表と OBS への出し方。操作画面だけに出す。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from stream_media_viewer import OUTPUT_WINDOW_TITLE
from stream_media_viewer.i18n import t
from stream_media_viewer.ui.capture_exclude import exclude_from_capture
from stream_media_viewer.ui.styles import DARK_QSS


def _heading(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("helpHeading")
    return label


def _note(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("helpNote")
    label.setWordWrap(True)
    return label


class HelpDialog(QDialog):
    def __init__(self, parent: QWidget | None, lang: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(t(lang, "help_title"))
        self.setStyleSheet(DARK_QSS)
        root = QVBoxLayout(self)
        root.addWidget(_heading(t(lang, "help_keys_title")))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)
        self.key_labels: list[QLabel] = []
        for row, line in enumerate(t(lang, "help_keys").splitlines()):
            action, _, keys = line.partition("\t")
            key = QLabel(keys)
            key.setObjectName("helpKey")
            self.key_labels.append(key)
            grid.addWidget(QLabel(action), row, 0)
            grid.addWidget(key, row, 1)
        root.addLayout(grid)
        root.addWidget(_heading(t(lang, "help_obs_title")))
        root.addWidget(_note(t(lang, "help_obs").format(title=OUTPUT_WINDOW_TITLE)))
        root.addWidget(_heading(t(lang, "help_output_title")))
        root.addWidget(_note(t(lang, "help_output")))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t(lang, "ok"))
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)
        self.resize(520, 460)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        exclude_from_capture(self)
