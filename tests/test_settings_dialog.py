from stream_media_viewer import display_version
from stream_media_viewer.ui.settings_dialog import SettingsDialog, SettingsDraft


def test_settings_dialog_keeps_blur_strength(qtbot) -> None:
    dialog = SettingsDialog(
        None,
        SettingsDraft(
            blur_strength=25,
            face_blur=True,
            text_blur=False,
            enhance_level="weak",
            language="ja",
        ),
    )
    qtbot.addWidget(dialog)
    dialog.slider.setValue(41)
    dialog.chk_subfolders.setChecked(False)
    draft = dialog.draft()
    assert draft.blur_strength == 41
    assert draft.face_blur is True
    assert draft.text_blur is False
    assert draft.enhance_level == "weak"
    assert draft.language == "ja"
    assert draft.include_subfolders is False
    assert display_version() in dialog.version_label.text()
    assert dialog.chk_standby.isChecked() is False
    assert not hasattr(dialog, "chk_face")
    assert not hasattr(dialog, "chk_text")
    assert not hasattr(dialog, "cmb_enhance")
    assert not hasattr(dialog, "cmb_lang")
    assert not hasattr(dialog, "chk_audio")
    assert not hasattr(dialog, "chk_dev_allow_capture")


def test_cancelling_the_file_picker_keeps_the_standby_image(qtbot, monkeypatch) -> None:
    dialog = SettingsDialog(
        None,
        SettingsDraft(
            blur_strength=25,
            face_blur=True,
            text_blur=False,
            enhance_level="weak",
            language="ja",
            standby_path="C:/pics/break.png",
            use_standby=True,
        ),
    )
    qtbot.addWidget(dialog)
    monkeypatch.setattr(
        "stream_media_viewer.ui.settings_dialog.QFileDialog.getOpenFileName",
        lambda *_a, **_k: ("", ""),
    )
    dialog._pick_standby()
    draft = dialog.draft()
    assert draft.standby_path == "C:/pics/break.png"
    assert draft.use_standby is True
