from __future__ import annotations

import cv2
import numpy as np

from stream_media_viewer.detect.blur import Box


def detect_text_boxes(bgr: np.ndarray) -> list[Box]:
    """番号・名札向けの弱い検出。看板や服の模様も拾いうる。"""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = bgr.shape[:2]
    boxes: list[Box] = []
    for contour in contours:
        x, y, bw, bh = cv2.boundingRect(contour)
        if bw < 24 or bh < 10:
            continue
        area = bw * bh
        if area < 400 or area > (w * h) * 0.35:
            continue
        ratio = bw / max(1, bh)
        if ratio < 1.6 or ratio > 12:
            continue
        boxes.append(Box(x, y, bw, bh))
    return boxes
