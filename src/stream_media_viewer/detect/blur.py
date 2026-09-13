from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

DEFAULT_BRUSH_WIDTH = 88
MIN_BRUSH_WIDTH = 28
MAX_BRUSH_WIDTH = 160


@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int


def expand_box(box: Box, image_w: int, image_h: int, pad: float = 0.28) -> Box:
    dx = int(box.w * pad)
    dy = int(box.h * pad)
    x = max(0, box.x - dx)
    y = max(0, box.y - dy)
    w = min(image_w - x, box.w + 2 * dx)
    h = min(image_h - y, box.h + 2 * dy)
    return Box(x, y, max(1, w), max(1, h))


def gaussian_region(bgr: np.ndarray, box: Box, strength: int = 81) -> None:
    k = max(3, strength | 1)
    x2 = min(bgr.shape[1], box.x + box.w)
    y2 = min(bgr.shape[0], box.y + box.h)
    roi = bgr[box.y : y2, box.x : x2]
    if roi.size == 0:
        return
    bgr[box.y : y2, box.x : x2] = cv2.GaussianBlur(roi, (k, k), 0)


def gaussian_oval(bgr: np.ndarray, box: Box, strength: int = 81) -> None:
    """矩形の角は残し、顔の形に近い楕円でぼかす。"""
    k = max(3, strength | 1)
    x2 = min(bgr.shape[1], box.x + box.w)
    y2 = min(bgr.shape[0], box.y + box.h)
    roi = bgr[box.y : y2, box.x : x2]
    if roi.size == 0:
        return
    rh, rw = roi.shape[:2]
    if rh < 4 or rw < 4:
        gaussian_region(bgr, box, strength)
        return
    blurred = cv2.GaussianBlur(roi, (k, k), 0)
    mask = np.zeros((rh, rw), dtype=np.float32)
    axes = (max(1, rw // 2 - 1), max(1, rh // 2 - 1))
    cv2.ellipse(mask, (rw // 2, rh // 2), axes, 0, 0, 360, 1.0, -1)
    feather = max(3, (min(rw, rh) // 8) | 1)
    mask = cv2.GaussianBlur(mask, (feather, feather), 0)
    alpha = mask[..., None]
    mixed = blurred.astype(np.float32) * alpha + roi.astype(np.float32) * (1.0 - alpha)
    bgr[box.y : y2, box.x : x2] = mixed.astype(np.uint8)


def apply_marks(bgr: np.ndarray, marks: list[dict], strength: int = 81) -> None:
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
            mask = np.zeros((h, w), dtype=np.uint8)
            width_frac = float(mark.get("width") or 0.04)
            thickness = max(MIN_BRUSH_WIDTH, int(width_frac * w))
            for a, b in zip(pts, pts[1:], strict=False):
                p1 = (int(float(a[0]) * w), int(float(a[1]) * h))
                p2 = (int(float(b[0]) * w), int(float(b[1]) * h))
                cv2.line(mask, p1, p2, 255, thickness, cv2.LINE_AA)
            bgr[mask > 0] = blurred[mask > 0]
