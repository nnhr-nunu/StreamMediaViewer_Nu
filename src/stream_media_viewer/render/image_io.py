"""日本語を含むパスでも読み書きできる JPEG 入出力。

Windows の cv2.imread / cv2.imwrite は ANSI 以外の文字を含むパスで黙って失敗する
（ユーザー名が日本語だと AppData 配下のキャッシュが一切使えない）。
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def read_bgr(path: Path) -> np.ndarray | None:
    try:
        raw = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    if raw.size == 0:
        return None
    return cv2.imdecode(raw, cv2.IMREAD_COLOR)


def write_jpeg(path: Path, bgr: np.ndarray, quality: int) -> bool:
    ok, encoded = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        return False
    try:
        encoded.tofile(str(path))
    except OSError:
        return False
    return True
