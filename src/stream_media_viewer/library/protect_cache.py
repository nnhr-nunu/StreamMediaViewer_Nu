"""手元確認用の保護済みコマ。配信用の窓へは出さない。"""

from __future__ import annotations

from collections import OrderedDict

import cv2
import numpy as np

_JPEG_QUALITY = 85


def _pack_frame(frame: np.ndarray) -> bytes | np.ndarray:
    ok, encoded = cv2.imencode(
        ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY]
    )
    if not ok:
        return frame.copy()
    return encoded.tobytes()


def _unpack_frame(payload: bytes | np.ndarray) -> np.ndarray | None:
    if isinstance(payload, np.ndarray):
        return payload
    raw = np.frombuffer(payload, dtype=np.uint8)
    return cv2.imdecode(raw, cv2.IMREAD_COLOR)


class ProtectFrameCache:
    def __init__(self, limit: int = 16) -> None:
        self._limit = max(1, int(limit))
        self._data: OrderedDict[str, tuple[bytes | np.ndarray, bool, bool]] = OrderedDict()

    def __len__(self) -> int:
        return len(self._data)

    def has(self, key: str) -> bool:
        return key in self._data

    def room(self) -> int:
        return max(0, self._limit - len(self._data))

    def get(self, key: str) -> tuple[np.ndarray, bool, bool] | None:
        hit = self._data.get(key)
        if hit is None:
            return None
        self._data.move_to_end(key)
        packed, faces, texts = hit
        frame = _unpack_frame(packed)
        if frame is None:
            self._data.pop(key, None)
            return None
        return frame, faces, texts

    def put(self, key: str, frame: np.ndarray, faces: bool, texts: bool) -> None:
        self._data[key] = (_pack_frame(frame), faces, texts)
        self._data.move_to_end(key)
        while len(self._data) > self._limit:
            self._data.popitem(last=False)

    def drop(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()
