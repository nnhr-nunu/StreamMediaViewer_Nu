from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from stream_media_viewer.detect.blur import Box, expand_box

_MODEL = Path(__file__).resolve().parent.parent / "assets" / "blaze_face_short_range.tflite"
_DETECT_MAX_SIDE = 640


def _downscale(bgr: np.ndarray, max_side: int) -> tuple[np.ndarray, float]:
    h, w = bgr.shape[:2]
    long_edge = max(h, w)
    if long_edge <= max_side:
        return bgr, 1.0
    scale = long_edge / max_side
    small = cv2.resize(
        bgr,
        (max(1, int(w / scale)), max(1, int(h / scale))),
        interpolation=cv2.INTER_AREA,
    )
    return small, scale


def _iou(a: Box, b: Box) -> float:
    x1 = max(a.x, b.x)
    y1 = max(a.y, b.y)
    x2 = min(a.x + a.w, b.x + b.w)
    y2 = min(a.y + a.h, b.y + b.h)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = a.w * a.h + b.w * b.h - inter
    if union <= 0:
        return 0.0
    return inter / union


def _merge(boxes: list[Box]) -> list[Box]:
    kept: list[Box] = []
    for box in sorted(boxes, key=lambda item: item.w * item.h, reverse=True):
        if any(_iou(box, other) >= 0.35 for other in kept):
            continue
        kept.append(box)
    return kept


@lru_cache(maxsize=1)
def _image_detector() -> mp.tasks.vision.FaceDetector:
    options = mp.tasks.vision.FaceDetectorOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(_MODEL)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        min_detection_confidence=0.35,
    )
    return mp.tasks.vision.FaceDetector.create_from_options(options)


@lru_cache(maxsize=1)
def _profile_cascade() -> cv2.CascadeClassifier | None:
    try:
        path = cv2.data.haarcascades + "haarcascade_profileface.xml"
    except AttributeError:
        return None
    cascade = cv2.CascadeClassifier(path)
    if cascade.empty():
        return None
    return cascade


def _mediapipe_boxes(small: np.ndarray, scale: float, w: int, h: int) -> list[Box]:
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    if not rgb.flags["C_CONTIGUOUS"]:
        rgb = np.ascontiguousarray(rgb)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = _image_detector().detect(image)
    boxes: list[Box] = []
    if not result.detections:
        return boxes
    for det in result.detections:
        bb = det.bounding_box
        box = expand_box(
            Box(
                int(bb.origin_x * scale),
                int(bb.origin_y * scale),
                int(bb.width * scale),
                int(bb.height * scale),
            ),
            w,
            h,
            pad=0.32,
        )
        boxes.append(box)
    return boxes


def _profile_boxes(small: np.ndarray, scale: float, w: int, h: int) -> list[Box]:
    cascade = _profile_cascade()
    if cascade is None:
        return []
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    found = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(24, 24))
    flipped = cv2.flip(gray, 1)
    found_flip = cascade.detectMultiScale(
        flipped, scaleFactor=1.08, minNeighbors=4, minSize=(24, 24)
    )
    boxes: list[Box] = []
    sw = small.shape[1]
    for x, y, bw, bh in list(found) + [
        (sw - x - bw, y, bw, bh) for x, y, bw, bh in found_flip
    ]:
        boxes.append(
            expand_box(
                Box(int(x * scale), int(y * scale), int(bw * scale), int(bh * scale)),
                w,
                h,
                pad=0.38,
            )
        )
    return boxes


def detect_face_boxes(bgr: np.ndarray) -> list[Box]:
    small, scale = _downscale(bgr, _DETECT_MAX_SIDE)
    h, w = bgr.shape[:2]
    boxes = _mediapipe_boxes(small, scale, w, h)
    boxes.extend(_profile_boxes(small, scale, w, h))
    return _merge(boxes)
