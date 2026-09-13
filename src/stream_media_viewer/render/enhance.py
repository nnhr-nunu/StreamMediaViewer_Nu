"""配信に出す前の、ごく弱い見た目の補正。元ファイルは触らない。"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

ENHANCE_LEVELS = ("off", "weak", "strong")
PRESETS = {
    "weak": (1.12, 1.15),
    "strong": (1.28, 1.40),
}


def parse_enhance_level(raw: Any) -> str:
    if raw is True or raw == 1 or str(raw).strip().lower() in {"true", "on", "yes"}:
        return "weak"
    if raw is False or raw == 0 or str(raw).strip().lower() in {"false", "off", "no"}:
        return "off"
    text = str(raw).strip().lower()
    if text in ENHANCE_LEVELS:
        return text
    return "weak"


def next_enhance_level(current: str) -> str:
    level = parse_enhance_level(current)
    index = ENHANCE_LEVELS.index(level)
    return ENHANCE_LEVELS[(index + 1) % len(ENHANCE_LEVELS)]


def enhance_bgr(bgr: np.ndarray, *, level: str = "off") -> np.ndarray:
    parsed = parse_enhance_level(level)
    if parsed == "off" or bgr.size == 0:
        return bgr
    contrast, saturation = PRESETS[parsed]
    stepped = cv2.convertScaleAbs(bgr, alpha=contrast, beta=0)
    hsv = cv2.cvtColor(stepped, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
