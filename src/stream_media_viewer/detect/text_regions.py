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


def _from_binary(mask: np.ndarray, min_ratio: float, max_ratio: float) -> list[Box]:
    h, w = mask.shape[:2]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[Box] = []
    for contour in contours:
        x, y, bw, bh = cv2.boundingRect(contour)
        if bw < 18 or bh < 8:
            continue
        area = bw * bh
        if area < 280 or area > (w * h) * 0.28:
            continue
        ratio = bw / max(1, bh)
        if ratio < min_ratio or ratio > max_ratio:
            continue
        boxes.append(Box(x, y, bw, bh))
    return boxes


def detect_text_boxes(bgr: np.ndarray) -> list[Box]:
    """番号（横長）と名札（縦長〜やや横長）を狙う。看板も拾いうる。"""
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
        thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 13)), iterations=2
    )
    boxes = _from_binary(horiz, 1.8, 8.5)
    boxes += _from_binary(vert, 0.22, 0.75)

    h, w = gray.shape
    mser = cv2.MSER_create()
    regions, _ = mser.detectRegions(gray)
    for region in regions:
        x, y, bw, bh = cv2.boundingRect(region)
        if bw < 20 or bh < 10:
            continue
        ratio = bw / max(1, bh)
        area = bw * bh
        if area < 350 or area > (w * h) * 0.2:
            continue
        # プレート寄り（下半分の横長）または名札寄り（上〜中の小さめ縦）
        plate_like = ratio >= 2.0 and ratio <= 6.5 and y > int(h * 0.28)
        tag_like = 0.25 <= ratio <= 1.4 and area < (w * h) * 0.08
        if plate_like or tag_like:
            boxes.append(Box(x, y, bw, bh))

    return _merge(boxes)
