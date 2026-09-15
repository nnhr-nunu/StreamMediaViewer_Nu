from pathlib import Path


def test_darwin_pins_keep_macos_12() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "PySide6>=6.7.0,<6.10; sys_platform == 'darwin'" in text
    assert "opencv-python>=4.10.0,<4.11; sys_platform == 'darwin'" in text


def test_macos_install_uses_macos12_wheels() -> None:
    text = Path("scripts/ci_macos_install.py").read_text(encoding="utf-8")
    assert "macosx_12_0_x86_64" in text
    assert "macosx_12_0_universal2" in text
    assert "macosx_12_0_arm64" in text
    workflow = Path(".github/workflows/build-windows.yml").read_text(encoding="utf-8")
    assert "scripts/ci_macos_install.py" in workflow
    assert "scripts/ci_macos_minos.py" in workflow
    assert "python-3.10.11-macos11.pkg" in workflow
    assert "python_from: python.org" in workflow
