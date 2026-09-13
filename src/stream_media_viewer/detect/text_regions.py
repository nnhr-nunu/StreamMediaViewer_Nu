from __future__ import annotations

import cv2
import numpy as np

from stream_media_viewer.detect.blur import Box


def _merge(boxes: list[Box], iou_min: float = 0.25) -> list[Box]:
    kept: list[Box] = []
    for box in sorted(boxes, key=lambda b: b.w * b.h, reverse=True):
        overlap = False
        for other in kept:
            x1 = max(box.x, other.x)
            y1 = max(box.y, other.y)
            x2 = min(box.x + box.w, other.x + other.w)
            y2 = min(box.y + box.h, other.y + other.h)
            inter = max(0, x2 - x1) * max(0, y2 - y1)
            union = box.w * box.h + other.w * other.h - inter
            if union > 0 and inter / union >= iou_min:
                overlap = True
                break
        if not overlap:
            kept.append(box)
    return kept


def _from_binary(
    mask: np.ndarray,
    *,
    min_ratio: float,
    max_ratio: float,
    min_w: int,
    min_h: int,
) -> list[Box]:
    h, w = mask.shape[:2]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[Box] = []
    for contour in contours:
        x, y, bw, bh = cv2.boundingRect(contour)
        if bw < min_w or bh < min_h:
            continue
        area = bw * bh
        if area < 280 or area > (w * h) * 0.12:
            continue
        ratio = bw / max(1, bh)
        if ratio < min_ratio or ratio > max_ratio:
            continue
        boxes.append(Box(x, y, bw, bh))
    return boxes


def _stroke_count(gray: np.ndarray) -> int:
    """ROI 内の『文字らしい縦線』の数。窓やポールは 0〜1 になる。"""
    h, w = gray.shape[:2]
    if h < 8 or w < 16:
        return 0
    if max(h, w) < 40:
        scale = 40 / max(h, 1)
        gray = cv2.resize(
            gray,
            (max(16, int(w * scale)), max(12, int(h * scale))),
            interpolation=cv2.INTER_CUBIC,
        )
        h, w = gray.shape[:2]
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    block = max(7, (min(h, w) // 2) | 1)
    bw = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block,
        4,
    )
    fill = float(bw.mean()) / 255.0
    if fill < 0.06 or fill > 0.62:
        return 0
    _n, _labels, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    heights: list[int] = []
    for i in range(1, stats.shape[0]):
        _x, _y, cw, ch, area = stats[i]
        if area < 10:
            continue
        if ch < h * 0.28 or ch > h * 0.92:
            continue
        if cw > max(h * 0.85, 18):
            continue
        if cw / max(ch, 1) > 1.05:
            continue
        heights.append(int(ch))
    if len(heights) < 2:
        return len(heights)
    if max(heights) > min(heights) * 2.4:
        return 0
    return len(heights)


def _keep(gray: np.ndarray, box: Box, *, plate: bool) -> bool:
    h, w = gray.shape[:2]
    x2 = min(w, box.x + box.w)
    y2 = min(h, box.y + box.h)
    if x2 - box.x < 12 or y2 - box.y < 8:
        return False
    roi = gray[box.y : y2, box.x : x2]
    if roi.size == 0:
        return False
    if float(roi.std()) < 12:
        return False
    need = 3 if plate else 2
    return _stroke_count(roi) >= need


def detect_text_boxes(bgr: np.ndarray) -> list[Box]:
    """番号（横長）と名札。中に文字らしい線がある塊だけ残す。"""
    if bgr.ndim != 3 or bgr.shape[0] < 40 or bgr.shape[1] < 40:
        return []
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    horiz = cv2.morphologyEx(
        thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3)), iterations=2
    )
    vert = cv2.morphologyEx(
        thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 11)), iterations=1
    )
    h, w = gray.shape
    plates = [
        box
        for box in _from_binary(horiz, min_ratio=2.0, max_ratio=6.8, min_w=36, min_h=10)
        if box.y > int(h * 0.22) and _keep(gray, box, plate=True)
    ]
    tags = [
        box
        for box in _from_binary(vert, min_ratio=0.4, max_ratio=1.7, min_w=14, min_h=16)
        if int(h * 0.12) <= box.y <= int(h * 0.72) and _keep(gray, box, plate=False)
    ]
    return _merge(plates + tags)
