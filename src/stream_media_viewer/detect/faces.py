from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from stream_media_viewer.detect.blur import Box, expand_box

_MODEL = Path(__file__).resolve().parent.parent / "assets" / "blaze_face_short_range.tflite"


@lru_cache(maxsize=1)
def _image_detector() -> mp.tasks.vision.FaceDetector:
    options = mp.tasks.vision.FaceDetectorOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(_MODEL)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        min_detection_confidence=0.4,
    )
    return mp.tasks.vision.FaceDetector.create_from_options(options)


def detect_face_boxes(bgr: np.ndarray) -> list[Box]:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    if not rgb.flags["C_CONTIGUOUS"]:
        rgb = np.ascontiguousarray(rgb)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = _image_detector().detect(image)
    boxes: list[Box] = []
    h, w = bgr.shape[:2]
    if not result.detections:
        return boxes
    for det in result.detections:
        bb = det.bounding_box
        box = expand_box(Box(bb.origin_x, bb.origin_y, bb.width, bb.height), w, h)
        boxes.append(box)
    return boxes
