"""操作画面の設定ダイアログ。配信用の窓には出さない。"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
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
    video_audio: bool
    enhance_level: str
    language: str
    include_subfolders: bool = True


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None, draft: SettingsDraft) -> None:
        super().__init__(parent)
        self.setStyleSheet(DARK_QSS)
        self._lang = draft.language if draft.language in {"ja", "en"} else "ja"
        self.setWindowTitle(t(self._lang, "settings"))

        self.chk_face = QCheckBox(t(self._lang, "face_blur"))
        self.chk_face.setChecked(draft.face_blur)
        self.chk_text = QCheckBox(t(self._lang, "text_blur"))
        self.chk_text.setChecked(draft.text_blur)
        self.chk_audio = QCheckBox(t(self._lang, "audio"))
        self.chk_audio.setChecked(draft.video_audio)
        self.chk_audio.setToolTip(t(self._lang, "audio_hint"))
        self.chk_subfolders = QCheckBox(t(self._lang, "include_subfolders"))
        self.chk_subfolders.setChecked(draft.include_subfolders)

        self.cmb_enhance = QComboBox()
        self.cmb_enhance.addItem(t(self._lang, "enhance_off"), "off")
        self.cmb_enhance.addItem(t(self._lang, "enhance_weak"), "weak")
        self.cmb_enhance.addItem(t(self._lang, "enhance_strong"), "strong")
        level = parse_enhance_level(draft.enhance_level)
        index = max(0, self.cmb_enhance.findData(level))
        self.cmb_enhance.setCurrentIndex(index)

        self.cmb_lang = QComboBox()
        self.cmb_lang.addItem("日本語", "ja")
        self.cmb_lang.addItem("English", "en")
        self.cmb_lang.setCurrentIndex(0 if self._lang == "ja" else 1)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(MIN_BLUR_STRENGTH, MAX_BLUR_STRENGTH)
        self.slider.setValue(clamp_blur_strength(draft.blur_strength))
        self.lbl_strength = QLabel()
        self._sync_strength_label()
        self.slider.valueChanged.connect(self._sync_strength_label)

        form = QFormLayout()
        form.addRow(self.chk_face)
        form.addRow(self.chk_text)
        form.addRow(self.chk_audio)
        form.addRow(self.chk_subfolders)
        form.addRow(t(self._lang, "enhance_hint_short"), self.cmb_enhance)
        form.addRow(t(self._lang, "blur_strength"), self.slider)
        form.addRow("", self.lbl_strength)
        form.addRow(t(self._lang, "language_choice"), self.cmb_lang)

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
        self.resize(420, 380)

    def _sync_strength_label(self) -> None:
        self.lbl_strength.setText(str(self.slider.value()))

    def draft(self) -> SettingsDraft:
        lang = str(self.cmb_lang.currentData() or "ja")
        enhance = str(self.cmb_enhance.currentData() or "weak")
        return SettingsDraft(
            blur_strength=clamp_blur_strength(self.slider.value()),
            face_blur=self.chk_face.isChecked(),
            text_blur=self.chk_text.isChecked(),
            video_audio=self.chk_audio.isChecked(),
            enhance_level=parse_enhance_level(enhance),
            language=lang if lang in {"ja", "en"} else "ja",
            include_subfolders=self.chk_subfolders.isChecked(),
        )
