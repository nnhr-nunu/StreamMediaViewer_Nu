"""手元操作ウィンドウ。配信出力へは OutputGate 経由でのみ送る。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stream_media_viewer import OPERATOR_WINDOW_TITLE
from stream_media_viewer.safety.output_gate import OutputGate, OutputReason


class OperatorWindow(QMainWindow):
    send_requested = Signal()
    panic_requested = Signal()
    panic_cleared = Signal()

    def __init__(self, gate: OutputGate) -> None:
        super().__init__()
        self._gate = gate
        self.setWindowTitle(OPERATOR_WINDOW_TITLE)
        self.resize(960, 640)

        root = QWidget()
        layout = QVBoxLayout(root)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.preview_label = QLabel("プレビュー（未読込）")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(360)
        self.preview_label.setStyleSheet("background: #1a1a1a; color: #ddd; border-radius: 8px;")
        layout.addWidget(self.preview_label, stretch=1)

        buttons = QHBoxLayout()
        self.mark_ready_button = QPushButton("処理完了（仮）")
        self.mark_ready_button.setToolTip("Phase 1 で自動ぼかし完了に置き換える仮ボタン")
        self.send_button = QPushButton("配信へ送信")
        self.panic_button = QPushButton("緊急マスク")
        self.clear_panic_button = QPushButton("マスク解除（再送信が必要）")
        buttons.addWidget(self.mark_ready_button)
        buttons.addWidget(self.send_button)
        buttons.addWidget(self.panic_button)
        buttons.addWidget(self.clear_panic_button)
        layout.addLayout(buttons)

        hint = QLabel("A/D 前後（未実装） / Enter 送信 / Space・Esc 緊急マスク")
        hint.setStyleSheet("color: #888;")
        layout.addWidget(hint)

        self.setCentralWidget(root)
        self._bind_shortcuts()
        self.mark_ready_button.clicked.connect(self._on_mark_ready)
        self.send_button.clicked.connect(self.send_requested.emit)
        self.panic_button.clicked.connect(self.panic_requested.emit)
        self.clear_panic_button.clicked.connect(self.panic_cleared.emit)
        self.refresh_status()

    def _bind_shortcuts(self) -> None:
        QShortcut(QKeySequence("Return"), self, self.send_requested.emit)
        QShortcut(QKeySequence("Ctrl+Return"), self, self.send_requested.emit)
        QShortcut(QKeySequence("Space"), self, self.panic_requested.emit)
        QShortcut(QKeySequence("Esc"), self, self.panic_requested.emit)

    def _on_mark_ready(self) -> None:
        self._gate.mark_processed()
        self.refresh_status()

    def refresh_status(self) -> None:
        reason = self._gate.reason.value
        masked = "マスク中" if self._gate.masked else "配信中"
        self.status_label.setText(
            f"配信出力: {masked}（{reason}） / 処理完了: {'はい' if self._gate.ready else 'いいえ'}"
        )
        self.send_button.setEnabled(
            self._gate.ready and self._gate.reason is not OutputReason.PANIC
        )
