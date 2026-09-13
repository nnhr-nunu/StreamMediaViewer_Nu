from stream_media_viewer.ui.settings_dialog import SettingsDialog, SettingsDraft


def test_settings_dialog_keeps_blur_strength(qtbot) -> None:
    dialog = SettingsDialog(
        None,
        SettingsDraft(
            blur_strength=25,
            face_blur=True,
            text_blur=False,
            video_audio=False,
            enhance_level="weak",
            language="ja",
        ),
    )
    qtbot.addWidget(dialog)
    dialog.slider.setValue(41)
    dialog.chk_text.setChecked(True)
    dialog.cmb_lang.setCurrentIndex(1)
    dialog.chk_subfolders.setChecked(False)
    draft = dialog.draft()
    assert draft.blur_strength == 41
    assert draft.text_blur is True
    assert draft.language == "en"
    assert draft.include_subfolders is False
    from stream_media_viewer import display_version

    assert display_version() in dialog.version_label.text()
