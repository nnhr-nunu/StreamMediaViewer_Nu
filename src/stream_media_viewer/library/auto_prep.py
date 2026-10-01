"""写真の下準備を自動で少しずつ進める順番と休み方。

フォルダを開いたら、見ている写真に近い順にぼかしを作り置きする。
PC を重くしないため 1 枚ずつ、かかった時間の数倍は休む。配信中はさらに控えめにする。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from stream_media_viewer.library.item import MediaItem

# 休みは「1 枚にかかった時間 × 倍率」。何も出していないとき（配信前）と配信中で変える
REST_FACTOR_IDLE = 2.0
REST_FACTOR_LIVE = 5.0
MIN_REST_MS = 300
MAX_REST_MS = 8000
# 止めている理由が消えたかを見に行く間隔
PAUSE_POLL_MS = 1500
# 1 回に「もう済んでいるか」を確かめる数。多いと操作画面が一瞬止まる
CHECKS_PER_TICK = 40


def rest_ms(elapsed_s: float, *, live: bool) -> int:
    factor = REST_FACTOR_LIVE if live else REST_FACTOR_IDLE
    wanted = int(max(0.0, elapsed_s) * 1000 * factor)
    return min(MAX_REST_MS, max(MIN_REST_MS, wanted))


def nearest_rows(total: int, current: int) -> list[int]:
    """current から近い順の行（current 自身は含めない）。同じ距離なら次の行を先に。"""
    order: list[int] = []
    for distance in range(1, total):
        for row in (current + distance, current - distance):
            if 0 <= row < total:
                order.append(row)
    return order


class AutoPrepQueue:
    """自動の下準備の順番と進み具合。Qt には触らない（テストしやすくする）。"""

    def __init__(self) -> None:
        self._queue: list[MediaItem] = []
        self._done: set[str] = set()
        self._total = 0
        self.inflight = False

    def forget(self) -> None:
        """設定が変わって作り置きが使えなくなったとき。全部を確かめ直す。"""
        self._done.clear()
        self._queue = []
        self._total = 0

    def forget_path(self, path: str) -> None:
        """そのファイルだけ手動ぼかしや向きが変わったとき。"""
        self._done.discard(path)

    def rebuild(
        self,
        visible: list[MediaItem],
        current: int,
        others: Iterable[MediaItem] = (),
    ) -> None:
        """見ている写真に近い順 → 一覧に出ていない写真、の順に並べ直す。"""
        ordered: list[MediaItem] = []
        seen: set[str] = set()

        def add(item: MediaItem) -> None:
            key = str(item.path)
            if item.kind != "image" or not item.readable or key in seen:
                return
            seen.add(key)
            ordered.append(item)

        if 0 <= current < len(visible):
            add(visible[current])
        for row in nearest_rows(len(visible), current):
            add(visible[row])
        for item in visible:
            add(item)
        for item in others:
            add(item)
        self._total = len(ordered)
        self._queue = [item for item in ordered if str(item.path) not in self._done]

    def take_next(self, is_ready: Callable[[MediaItem], bool]) -> MediaItem | None:
        """次に作る写真。済んでいるものは飛ばす（1 回に確かめる数は限る）。"""
        checks = 0
        while self._queue and checks < CHECKS_PER_TICK:
            item = self._queue.pop(0)
            checks += 1
            if is_ready(item):
                self._done.add(str(item.path))
                continue
            return item
        return None

    def mark_done(self, item: MediaItem) -> None:
        self._done.add(str(item.path))

    @property
    def pending(self) -> bool:
        return bool(self._queue)

    def progress(self) -> tuple[int, int]:
        remaining = len(self._queue) + (1 if self.inflight else 0)
        return max(0, self._total - remaining), self._total
