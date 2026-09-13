from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int


def expand_box(box: Box, image_w: int, image_h: int, pad: float = 0.25) -> Box:
    dx = int(box.w * pad)
    dy = int(box.h * pad)
    x = max(0, box.x - dx)
    y = max(0, box.y - dy)
    w = min(image_w - x, box.w + 2 * dx)
    h = min(image_h - y, box.h + 2 * dy)
    return Box(x, y, max(1, w), max(1, h))


def gaussian_region(bgr: np.ndarray, box: Box, strength: int = 25) -> None:
    k = max(3, strength | 1)
    x2 = min(bgr.shape[1], box.x + box.w)
    y2 = min(bgr.shape[0], box.y + box.h)
    roi = bgr[box.y : y2, box.x : x2]
    if roi.size == 0:
        return
    bgr[box.y : y2, box.x : x2] = cv2.GaussianBlur(roi, (k, k), 0)


def apply_marks(bgr: np.ndarray, marks: list[dict], strength: int = 25) -> None:
    h, w = bgr.shape[:2]
    k = max(3, strength | 1)
    for mark in marks:
        kind = mark.get("kind")
        if kind == "rect":
            x = int(float(mark.get("x", 0)) * w)
            y = int(float(mark.get("y", 0)) * h)
            bw = int(float(mark.get("w", 0)) * w)
            bh = int(float(mark.get("h", 0)) * h)
            if mark.get("erase"):
                continue
            gaussian_region(bgr, Box(x, y, bw, bh), strength)
        elif kind == "stroke":
            pts = mark.get("points") or []
            if len(pts) < 2:
                continue
            blurred = cv2.GaussianBlur(bgr, (k, k), 0)
            # blend blurred where overlay darkened by stroke — simpler: blur along thick line mask
            mask = np.zeros((h, w), dtype=np.uint8)
            for a, b in zip(pts, pts[1:], strict=False):
                p1 = (int(float(a[0]) * w), int(float(a[1]) * h))
                p2 = (int(float(b[0]) * w), int(float(b[1]) * h))
                cv2.line(mask, p1, p2, 255, max(24, w // 40), cv2.LINE_AA)
            bgr[mask > 0] = blurred[mask > 0]
