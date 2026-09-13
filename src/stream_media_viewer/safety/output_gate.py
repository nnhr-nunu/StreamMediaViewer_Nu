"""配信出力の安全ゲート。

未承認・処理中・パニック中は、配信側にメディアを出さない。
"""

from __future__ import annotations

from enum import Enum


class OutputReason(str, Enum):
    STARTUP = "startup"
    LOADING = "loading"
    AWAITING_SEND = "awaiting_send"
    LIVE = "live"
    PANIC = "panic"


class OutputGate:
    """配信ウィンドウがマスクか実映像かを決める単一の正本。"""

    def __init__(self) -> None:
        self._reason = OutputReason.STARTUP
        self._ready = False

    @property
    def masked(self) -> bool:
        return self._reason != OutputReason.LIVE

    @property
    def reason(self) -> OutputReason:
        return self._reason

    @property
    def ready(self) -> bool:
        return self._ready

    def begin_load(self) -> None:
        self._ready = False
        if self._reason != OutputReason.PANIC:
            self._reason = OutputReason.LOADING

    def mark_processed(self) -> None:
        """ぼかし処理完了。まだ配信へは出さない。"""
        self._ready = True
        if self._reason == OutputReason.LOADING:
            self._reason = OutputReason.AWAITING_SEND

    def send_to_output(self) -> bool:
        if not self._ready or self._reason == OutputReason.PANIC:
            return False
        self._reason = OutputReason.LIVE
        return True

    def panic(self) -> None:
        self._reason = OutputReason.PANIC

    def clear_panic(self) -> None:
        """パニック解除後も再送信までマスクを維持する。"""
        self._reason = OutputReason.AWAITING_SEND if self._ready else OutputReason.LOADING
