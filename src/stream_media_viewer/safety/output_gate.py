"""配信に出す／隠す／送れるかの正本。"""

from __future__ import annotations

from enum import Enum


class OutputReason(str, Enum):
    STARTUP = "startup"
    STANDBY = "standby"
    LIVE = "live"
    PANIC = "panic"


class OutputGate:
    def __init__(self) -> None:
        self._reason = OutputReason.STARTUP
        self._preview_ready = False

    @property
    def reason(self) -> OutputReason:
        return self._reason

    @property
    def ready(self) -> bool:
        return self._preview_ready

    @property
    def masked(self) -> bool:
        """配信用にメディアを出していない。"""
        return self._reason != OutputReason.LIVE

    @property
    def window_visible(self) -> bool:
        return self._reason in {OutputReason.LIVE, OutputReason.STANDBY}

    def begin_load(self) -> None:
        """次の確認用。配信中の絵は落とさない。"""
        self._preview_ready = False

    def mark_processed(self) -> None:
        self._preview_ready = True

    def send_to_output(self) -> bool:
        if not self._preview_ready:
            return False
        self._reason = OutputReason.LIVE
        return True

    def panic(self) -> None:
        self._reason = OutputReason.PANIC

    def enable_standby(self, on: bool) -> None:
        if self._reason in {OutputReason.LIVE, OutputReason.PANIC}:
            return
        self._reason = OutputReason.STANDBY if on else OutputReason.STARTUP
