"""一覧の前後。確認の先読みに使う。"""

from __future__ import annotations

PREFETCH_RADIUS = 5


def neighbor_rows(index: int, count: int, *, radius: int = PREFETCH_RADIUS) -> tuple[int, ...]:
    if count < 2 or radius < 1:
        return ()
    seen: list[int] = []
    known: set[int] = set()
    for step in range(1, radius + 1):
        for row in ((index + step) % count, (index - step) % count):
            if row == index or row in known:
                continue
            known.add(row)
            seen.append(row)
            if len(seen) >= count - 1:
                return tuple(seen)
    return tuple(seen)
