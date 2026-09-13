"""操作画面の設定ダイアログ。配信用の窓には出さない。"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from stream_media_viewer import display_version
from stream_media_viewer.i18n import t
from stream_media_viewer.render.enhance import parse_enhance_level
from stream_media_viewer.settings import (
    MAX_BLUR_STRENGTH,
    MIN_BLUR_STRENGTH,
    clamp_blur_strength,
)
from stream_media_viewer.ui.styles import DARK_QSS


@dataclass
class SettingsDraft:
    blur_strength: int
    face_blur: bool
    text_blur: bool
    enhance_level: str
    language: str
    include_subfolders: bool = True
    standby_path: str = ""
    use_standby: bool = False


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None, draft: SettingsDraft) -> None:
        super().__init__(parent)
        self.setStyleSheet(DARK_QSS)
        self._lang = draft.language if draft.language in {"ja", "en"} else "ja"
        self._face_blur = draft.face_blur
        self._text_blur = draft.text_blur
        self._enhance_level = parse_enhance_level(draft.enhance_level)
        self.setWindowTitle(t(self._lang, "settings"))

        self.chk_subfolders = QCheckBox(t(self._lang, "include_subfolders"))
        self.chk_subfolders.setChecked(draft.include_subfolders)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(MIN_BLUR_STRENGTH, MAX_BLUR_STRENGTH)
        self.slider.setValue(clamp_blur_strength(draft.blur_strength))
        self.lbl_strength = QLabel()
        self.lbl_strength.setObjectName("meta")
        self._sync_strength_label()
        self.slider.valueChanged.connect(self._sync_strength_label)

        form = QFormLayout()
        form.addRow(self.chk_subfolders)
        form.addRow(t(self._lang, "blur_strength"), self.slider)
        form.addRow("", self.lbl_strength)

        self.chk_standby = QCheckBox(t(self._lang, "standby"))
        self.chk_standby.setChecked(draft.use_standby)
        self.edit_standby = QLineEdit(draft.standby_path)
        self.edit_standby.setReadOnly(True)
        self.btn_standby = QPushButton(t(self._lang, "standby_pick"))
        self.btn_standby.clicked.connect(self._pick_standby)
        standby_row = QHBoxLayout()
        standby_row.addWidget(self.edit_standby, stretch=1)
        standby_row.addWidget(self.btn_standby)
        form.addRow(self.chk_standby)
        form.addRow(standby_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t(self._lang, "ok"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t(self._lang, "cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        self.version_label = QLabel(display_version())
        self.version_label.setObjectName("meta")
        root.addWidget(self.version_label)
        root.addWidget(buttons)
        self.resize(460, 320)

    def _pick_standby(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, t(self._lang, "standby"))
        if not path:
            self.chk_standby.setChecked(False)
            self.edit_standby.setText("")
            return
        self.edit_standby.setText(path)
        self.chk_standby.setChecked(True)

    def _sync_strength_label(self) -> None:
        self.lbl_strength.setText(str(self.slider.value()))

    def draft(self) -> SettingsDraft:
        return SettingsDraft(
            blur_strength=clamp_blur_strength(self.slider.value()),
            face_blur=self._face_blur,
            text_blur=self._text_blur,
            enhance_level=self._enhance_level,
            language=self._lang,
            include_subfolders=self.chk_subfolders.isChecked(),
            standby_path=self.edit_standby.text().strip(),
            use_standby=self.chk_standby.isChecked() and bool(self.edit_standby.text().strip()),
        )
