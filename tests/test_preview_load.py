from pathlib import Path

import numpy as np
from PIL import Image

from stream_media_viewer.library.preview_load import ImageLoadWorker


def test_image_load_worker_emits_bgr(qtbot, tmp_path: Path) -> None:
    src = tmp_path / "a.jpg"
    Image.new("RGB", (12, 8), (10, 20, 30)).save(src)
    got: list[tuple[tuple[int, ...], int]] = []
    worker = ImageLoadWorker(src, 4)
    worker.loaded.connect(lambda bgr, seq: got.append((tuple(bgr.shape), int(seq))))
    worker.start()
    qtbot.waitUntil(lambda: bool(got), timeout=5000)
    assert got[0][1] == 4
    assert got[0][0][2] == 3
    assert got[0][0][0] == 8
    assert got[0][0][1] == 12


def test_background_work_keeps_the_settings_it_started_with(tmp_path: Path, monkeypatch) -> None:
    # 下準備の鍵は始めたときの設定で作る。途中で顔ぼかしをオフにしても、
    # 「顔ぼかしオン」の鍵に素顔の絵を入れないよう、中身も始めたときの設定で作る。
    from stream_media_viewer.library.preview_load import PrefetchWorker
    from stream_media_viewer.playback.preload import PreloadWorker
    from stream_media_viewer.settings import AppSettings

    src = tmp_path / "a.jpg"
    Image.new("RGB", (32, 24), (10, 20, 30)).save(src)
    seen: list[tuple[bool, int, int]] = []

    def spy(bgr, settings, note, **_kwargs):
        seen.append((settings.face_blur, settings.blur_strength, note.rotation))
        return bgr.copy(), False, False

    monkeypatch.setattr("stream_media_viewer.library.preview_load.protect_for_note", spy)
    monkeypatch.setattr("stream_media_viewer.playback.preload.protect_for_note", spy)
    settings = AppSettings(face_blur=True, blur_strength=180)
    note = settings.note_for(str(src))
    prefetch = PrefetchWorker(src, settings, note, "k1", "folder")
    preload = PreloadWorker(src, "k2", settings, [], 0, None, "folder")
    settings.face_blur = False
    settings.blur_strength = 5
    note.rotation = 90
    prefetch.run()
    preload.run()
    assert seen == [(True, 180, 0), (True, 180, 0)]
