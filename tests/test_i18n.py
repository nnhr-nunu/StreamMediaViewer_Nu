from stream_media_viewer.i18n import STRINGS


def test_japanese_and_english_cover_the_same_keys() -> None:
    assert set(STRINGS["ja"]) == set(STRINGS["en"])
