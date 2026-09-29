from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

DEFAULT_BRUSH_WIDTH = 120
MIN_BRUSH_WIDTH = 12
MAX_BRUSH_WIDTH = 320
DEFAULT_BLUR_STRENGTH = 180
MIN_BLUR_STRENGTH = 5
MAX_BLUR_STRENGTH = 300


@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int
    angle: float = 0.0


def expand_box(box: Box, image_w: int, image_h: int, pad: float = 0.28) -> Box:
    dx = int(box.w * pad)
    dy = int(box.h * pad)
    x = max(0, box.x - dx)
    y = max(0, box.y - dy)
    w = min(image_w - x, box.w + 2 * dx)
    h = min(image_h - y, box.h + 2 * dy)
    return Box(x, y, max(1, w), max(1, h), angle=box.angle)


def _odd(value: int) -> int:
    n = max(3, int(value))
    return n if n % 2 else n - 1


def _kernel(strength: int, *, cap: int | None = None, limit: int | None = None) -> int:
    try:
        k = _odd(int(strength) | 1)
    except (TypeError, ValueError):
        k = _odd(DEFAULT_BLUR_STRENGTH)
    if cap is not None:
        k = min(k, _odd(cap))
    if limit is not None:
        k = min(k, _odd(limit))
    return k


def _gaussian(roi: np.ndarray, strength: int, *, cap: int | None = None) -> np.ndarray:
    rh, rw = roi.shape[:2]
    if min(rh, rw) < 3:
        return roi
    k = _kernel(strength, cap=cap, limit=min(rh, rw))
    if k < 3:
        return roi
    try:
        return cv2.GaussianBlur(roi, (k, k), 0)
    except cv2.error:
        try:
            return cv2.GaussianBlur(roi, (3, 3), 0)
        except cv2.error:
            return roi


def _clip(bgr: np.ndarray, box: Box) -> tuple[int, int, int, int]:
    """画像内に収めた (x1, y1, x2, y2)。負の座標でスライスが末尾から数えないようにする。"""
    x1, x2 = sorted((int(box.x), int(box.x) + int(box.w)))
    y1, y2 = sorted((int(box.y), int(box.y) + int(box.h)))
    height, width = bgr.shape[:2]
    return max(0, x1), max(0, y1), min(width, x2), min(height, y2)


def gaussian_region(bgr: np.ndarray, box: Box, strength: int = DEFAULT_BLUR_STRENGTH) -> None:
    x1, y1, x2, y2 = _clip(bgr, box)
    if x2 <= x1 or y2 <= y1:
        return
    roi = bgr[y1:y2, x1:x2]
    bgr[y1:y2, x1:x2] = _gaussian(roi, strength)


def oval_tilt(angle: float) -> float:
    """楕円を枠に合わせて傾ける角度（-45〜45°）。

    枠は顔を囲む縦横の枠。横倒し（目の線が縦）の顔は枠が横長なので、
    目の線の角度そのままで回すと楕円が縦横逆になり、顔の端がぼけない。
    楕円の長い軸が、枠の長い辺の向きから 45° 以内になるようにそろえる。
    """
    try:
        value = float(angle)
    except (TypeError, ValueError):
        return 0.0
    if not np.isfinite(value):
        return 0.0
    if -45.0 <= value <= 45.0:
        return value
    return ((value + 45.0) % 90.0) - 45.0


def gaussian_oval(bgr: np.ndarray, box: Box, strength: int = DEFAULT_BLUR_STRENGTH) -> None:
    """矩形の角は残し、顔の形に近い楕円でぼかす。"""
    x1, y1, x2, y2 = _clip(bgr, box)
    if x2 <= x1 or y2 <= y1:
        return
    roi = bgr[y1:y2, x1:x2]
    rh, rw = roi.shape[:2]
    if rh < 4 or rw < 4:
        gaussian_region(bgr, box, strength)
        return
    blurred = _gaussian(roi, strength)
    mask = np.zeros((rh, rw), dtype=np.float32)
    axes = (max(1, rw // 2 - 1), max(1, rh // 2 - 1))
    cv2.ellipse(mask, (rw // 2, rh // 2), axes, oval_tilt(box.angle), 0, 360, 1.0, -1)
    feather = max(3, (min(rw, rh) // 8) | 1)
    mask = cv2.GaussianBlur(mask, (feather, feather), 0)
    alpha = mask[..., None]
    mixed = blurred.astype(np.float32) * alpha + roi.astype(np.float32) * (1.0 - alpha)
    bgr[y1:y2, x1:x2] = mixed.astype(np.uint8)


def apply_marks(bgr: np.ndarray, marks: list[dict], strength: int = DEFAULT_BLUR_STRENGTH) -> None:
    h, w = bgr.shape[:2]
    for mark in marks:
        try:
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
                width_frac = float(mark.get("width") or 0.04)
                thickness = max(1, int(round(width_frac * w)))
                mask = np.zeros((h, w), dtype=np.uint8)
                radius = max(1, thickness // 2)
                for a, b in zip(pts, pts[1:], strict=False):
                    p1 = (int(float(a[0]) * w), int(float(a[1]) * h))
                    p2 = (int(float(b[0]) * w), int(float(b[1]) * h))
                    cv2.line(mask, p1, p2, 255, thickness, cv2.LINE_8)
                    cv2.circle(mask, p1, radius, 255, -1)
                    cv2.circle(mask, p2, radius, 255, -1)
                ys, xs = np.where(mask > 0)
                if xs.size == 0:
                    continue
                k_local = _kernel(strength, cap=thickness * 2 + 1)
                pad = k_local // 2 + 1
                x0, x1 = max(0, int(xs.min()) - pad), min(w, int(xs.max()) + pad + 1)
                y0, y1 = max(0, int(ys.min()) - pad), min(h, int(ys.max()) + pad + 1)
                roi = bgr[y0:y1, x0:x1]
                if min(roi.shape[:2]) < 3:
                    continue
                blurred = _gaussian(roi, strength, cap=thickness * 2 + 1)
                local = mask[y0:y1, x0:x1] > 0
                roi[local] = blurred[local]
        except (TypeError, ValueError, IndexError, cv2.error):
            continue
