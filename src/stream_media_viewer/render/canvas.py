from __future__ import annotations

import numpy as np

OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080


def fit_letterbox(
    bgr: np.ndarray,
    width: int = OUTPUT_WIDTH,
    height: int = OUTPUT_HEIGHT,
) -> np.ndarray:
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    src_h, src_w = bgr.shape[:2]
    if src_h == 0 or src_w == 0:
        return canvas
    scale = min(width / src_w, height / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    import cv2

    resized = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    x = (width - new_w) // 2
    y = (height - new_h) // 2
    canvas[y : y + new_h, x : x + new_w] = resized
    return canvas


def rgb_to_bgr(rgb: np.ndarray) -> np.ndarray:
    import cv2

    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def bgr_to_rgb(bgr: np.ndarray) -> np.ndarray:
    import cv2

    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
