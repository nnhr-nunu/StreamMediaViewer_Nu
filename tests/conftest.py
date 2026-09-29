from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolated_user_config(tmp_path_factory: pytest.TempPathFactory, monkeypatch) -> Path:
    """テストが本物の設定・事前処理・縮小画・ログのフォルダに書かないようにする。

    アプリ本体（persist や回転など）は保存先を引数で受けず user_config_dir() に書くため、
    何もしないと開発者の settings.json が既定値で上書きされる。
    """
    config = tmp_path_factory.mktemp("user_config")
    for module in (
        "stream_media_viewer.settings",
        "stream_media_viewer.playback.preload",
        "stream_media_viewer.library.thumbs",
        "stream_media_viewer.errors",
    ):
        monkeypatch.setattr(f"{module}.user_config_dir", lambda: config)
    return config
