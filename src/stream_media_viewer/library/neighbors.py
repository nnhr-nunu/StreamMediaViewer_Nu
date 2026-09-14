"""一覧の前後。確認の先読みに使う。"""

from __future__ import annotations


def neighbor_rows(index: int, count: int) -> tuple[int, ...]:
    if count < 2:
        return ()
    nxt = (index + 1) % count
    prev = (index - 1) % count
    if nxt == prev:
        return (nxt,)
    return (nxt, prev)
