"""手元確認用の保護済みコマ。配信用の窓へは出さない。"""

from __future__ import annotations

from collections import OrderedDict

import numpy as np


class ProtectFrameCache:
    def __init__(self, limit: int = 64) -> None:
        self._limit = max(1, int(limit))
        self._data: OrderedDict[str, tuple[np.ndarray, bool, bool]] = OrderedDict()

    def has(self, key: str) -> bool:
        return key in self._data

    def room(self) -> int:
        return max(0, self._limit - len(self._data))

    def get(self, key: str) -> tuple[np.ndarray, bool, bool] | None:
        hit = self._data.get(key)
        if hit is None:
            return None
        self._data.move_to_end(key)
        return hit

    def put(self, key: str, frame: np.ndarray, faces: bool, texts: bool) -> None:
        self._data[key] = (frame, faces, texts)
        self._data.move_to_end(key)
        while len(self._data) > self._limit:
            self._data.popitem(last=False)

    def drop(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()
