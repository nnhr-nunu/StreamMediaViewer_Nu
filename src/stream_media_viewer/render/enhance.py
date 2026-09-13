"""配信に出す前の、ごく弱い見た目の補正。元ファイルは触らない。"""

from __future__ import annotations

import cv2
import numpy as np

CONTRAST = 1.12
SATURATION = 1.15


def enhance_bgr(bgr: np.ndarray, *, enabled: bool) -> np.ndarray:
    if not enabled or bgr.size == 0:
        return bgr
    contrast = cv2.convertScaleAbs(bgr, alpha=CONTRAST, beta=0)
    hsv = cv2.cvtColor(contrast, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * SATURATION, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
