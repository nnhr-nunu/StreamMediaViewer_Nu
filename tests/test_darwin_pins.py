from pathlib import Path


def test_darwin_pins_keep_macos_12() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "PySide6>=6.7.0,<6.10; sys_platform == 'darwin'" in text
    assert "opencv-python>=4.10.0,<4.11; sys_platform == 'darwin'" in text
