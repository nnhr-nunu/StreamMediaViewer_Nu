"""確認や設定の小窓・メニューが出ていても、テンキー0で必ず配信から隠す。

小窓が開いているあいだは操作画面のキー（0 / Esc）が届かない。
Esc は小窓を閉じる（やめる）意味でも使われるので、ここで拾うのは 0 だけ。
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QApplication, QDialog, QWidget


def _belongs_to(widget: QWidget | None, owner: QWidget) -> bool:
    """widget が owner（操作画面）から開いた小窓・メニューか。別の窓のものは触らない。"""
    while widget is not None:
        if widget is owner:
            return True
        widget = widget.parentWidget()
    return False


class PanicKeyFilter(QObject):
    """parent は操作画面。操作画面が出ていて、そこから開いた小窓のときだけ働く。"""

    def __init__(self, on_panic: Callable[[], None], parent: QWidget) -> None:
        super().__init__(parent)
        self._on_panic = on_panic
        self._owner = parent

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() != QEvent.Type.KeyPress or event.key() != Qt.Key.Key_0:
            return False
        modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
        if modifiers != Qt.KeyboardModifier.NoModifier:
            return False
        try:
            if not self._owner.isVisible():
                return False
        except RuntimeError:
            return False
        popup = QApplication.activePopupWidget()
        modal = QApplication.activeModalWidget()
        target = popup or modal
        if target is None or not _belongs_to(target, self._owner):
            # 小窓が無いときは操作画面のショートカットに任せる（2 回隠さない）
            return False
        self._on_panic()
        # 隠したあとに Enter で「送る」が通らないよう、開いていた小窓は閉じる（やめる扱い）
        if isinstance(target, QDialog):
            target.reject()
        else:
            target.close()
        return True
