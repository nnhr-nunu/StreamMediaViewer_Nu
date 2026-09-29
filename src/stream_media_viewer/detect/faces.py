from __future__ import annotations

import math
import sys
import threading
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from stream_media_viewer.detect.blur import Box, expand_box
from stream_media_viewer.errors import log_exception
from stream_media_viewer.settings import FACE_PIPELINE_LEGACY, parse_face_pipeline

_MODEL = Path(__file__).resolve().parent.parent / "assets" / "blaze_face_short_range.tflite"
_YUNET = Path(__file__).resolve().parent.parent / "assets" / "face_detection_yunet_2023mar.onnx"
# 写真の探し方を変えたら上げる。前の探し方で作った写真の下準備を作り直す。
STILL_DETECT_VERSION = 2
_DETECT_SIDES = (640, 960)
# 写真だけ: 確認用の大きさ（長い辺 1920 まで）のままでも探し、遠くの小さい顔を拾う
_STILL_SIDE = 1920
# 写真だけ: 90° 回しても探し、寝転び・横倒しの顔を拾う
_TURNED_SIDE = 640
# 足した探し方の枠が、いつもの探し方の枠とこれだけ重なるなら同じ顔として足さない
_EXTRA_SAME_IOU = 0.35
_FALSE_HASH_LIMIT = 300
_FALSE_HAMMING = 10
_YUNET_SCORE = 0.75
_YUNET_MIN_SIDE = 128
_YUNET_LOCK = threading.Lock()
_MEDIAPIPE_LOCK = threading.Lock()
_mediapipe_logged = False


class FaceDetectorUnavailable(RuntimeError):
    """顔を探す部品が使えない。顔なしとして素顔を通さず、処理の失敗にする。"""


def _model_bytes(path: Path) -> bytes:
    # cv2 と MediaPipe は、Windows でパスに日本語などが入ると部品のファイルを開けない。
    # （zip を「山田」のユーザーフォルダなどに展開したとき）。中身を読んで渡す。
    return path.read_bytes()


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


def hold_face_boxes(current: list[Box], previous: list[Box] | None) -> list[Box]:
    if not previous:
        return list(current)
    if not current:
        return list(previous)
    return _merge(list(current) + list(previous))


class FaceHold:
    """直前コマの検出を 1 回だけ残す。素顔は増やさない。"""

    def __init__(self) -> None:
        self._last: list[Box] = []

    def reset(self) -> None:
        self._last = []

    def step(self, detected: list[Box]) -> list[Box]:
        held = hold_face_boxes(detected, self._last)
        self._last = list(detected)
        return held


def oval_angle_deg(
    right_eye: tuple[float, float], left_eye: tuple[float, float]
) -> float:
    dx = left_eye[0] - right_eye[0]
    dy = left_eye[1] - right_eye[1]
    if dx == 0.0 and dy == 0.0:
        return 0.0
    return math.degrees(math.atan2(dy, dx))


def face_box_from_eyes(
    box: Box,
    right_eye: tuple[float, float],
    left_eye: tuple[float, float],
    image_w: int,
    image_h: int,
    *,
    pad: float = 0.32,
) -> Box:
    tilted = Box(box.x, box.y, box.w, box.h, angle=oval_angle_deg(right_eye, left_eye))
    return expand_box(tilted, image_w, image_h, pad=pad)


@lru_cache(maxsize=1)
def _image_detector() -> object:
    import mediapipe as mp

    options = mp.tasks.vision.FaceDetectorOptions(
        base_options=mp.tasks.BaseOptions(model_asset_buffer=_model_bytes(_MODEL)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        min_detection_confidence=0.42,
    )
    return mp.tasks.vision.FaceDetector.create_from_options(options)


@lru_cache(maxsize=1)
def _yunet() -> cv2.FaceDetectorYN | None:
    try:
        model = np.frombuffer(_model_bytes(_YUNET), dtype=np.uint8)
    except OSError:
        return None
    config = np.empty(0, dtype=np.uint8)
    backend = int(getattr(cv2.dnn, "DNN_BACKEND_OPENCV", 3))
    target = int(getattr(cv2.dnn, "DNN_TARGET_CPU", 0))
    attempts = (
        ("onnx", model, config, (320, 320), float(_YUNET_SCORE), 0.3, 5000, backend, target),
        ("onnx", model, config, (320, 320), float(_YUNET_SCORE), 0.3, 5000),
        # 中身を渡す作り方が無い古い cv2 向け（パスが ASCII のときだけ開ける）
        (str(_YUNET), "", (320, 320), float(_YUNET_SCORE), 0.3, 5000),
    )
    for args in attempts:
        try:
            return cv2.FaceDetectorYN.create(*args)
        except (cv2.error, TypeError, ValueError):
            continue
    return None


@lru_cache(maxsize=1)
def _profile_cascade() -> cv2.CascadeClassifier | None:
    try:
        path = Path(cv2.data.haarcascades) / "haarcascade_profileface.xml"
    except AttributeError:
        return None
    if not path.is_file():
        # OpenCV 5 の配布物には入っていない
        return None
    cascade = cv2.CascadeClassifier()
    try:
        # パスに日本語などが入っても読めるよう、中身から読む
        storage = cv2.FileStorage(
            path.read_text(encoding="utf-8"),
            cv2.FILE_STORAGE_READ | cv2.FILE_STORAGE_MEMORY,
        )
        cascade.read(storage.getFirstTopLevelNode())
    except (OSError, UnicodeDecodeError, cv2.error):
        cascade = cv2.CascadeClassifier(str(path))
    if cascade.empty():
        return None
    return cascade


def _scaled_eye(
    x: float, y: float, small: np.ndarray, scale: float
) -> tuple[float, float]:
    sh, sw = small.shape[:2]
    if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and sw > 1 and sh > 1:
        x *= sw
        y *= sh
    return (x * scale, y * scale)


def _mediapipe_eyes(
    det: object, small: np.ndarray, scale: float
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    kps = getattr(det, "keypoints", None) or []
    if len(kps) < 2:
        return None
    right = _scaled_eye(float(kps[0].x), float(kps[0].y), small, scale)
    left = _scaled_eye(float(kps[1].x), float(kps[1].y), small, scale)
    return right, left


def _mediapipe_boxes(
    small: np.ndarray, scale: float, w: int, h: int, *, strict: bool = False
) -> list[Box]:
    """strict=True（MediaPipe だけで探す以前の検出）は、使えないとき処理の失敗にする。"""
    global _mediapipe_logged
    if sys.platform == "darwin":
        return []
    try:
        import mediapipe as mp

        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        if not rgb.flags["C_CONTIGUOUS"]:
            rgb = np.ascontiguousarray(rgb)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        with _MEDIAPIPE_LOCK:
            result = _image_detector().detect(image)
    except Exception as exc:
        if strict:
            raise FaceDetectorUnavailable("MediaPipe") from exc
        # 既定の検出では足しの部品。YuNet だけで続ける（Mac と同じ）が、記録は残す。
        if not _mediapipe_logged:
            _mediapipe_logged = True
            log_exception(exc)
        return []
    boxes: list[Box] = []
    if not result.detections:
        return boxes
    for det in result.detections:
        bb = det.bounding_box
        raw = Box(
            int(bb.origin_x * scale),
            int(bb.origin_y * scale),
            int(bb.width * scale),
            int(bb.height * scale),
        )
        eyes = _mediapipe_eyes(det, small, scale)
        if eyes is None:
            boxes.append(expand_box(raw, w, h, pad=0.32))
        else:
            boxes.append(face_box_from_eyes(raw, eyes[0], eyes[1], w, h, pad=0.32))
    return boxes


def _yunet_rows(small: np.ndarray) -> np.ndarray | None:
    """YuNet の結果の行。小さすぎる絵は探さない（None）。部品が使えないときは例外。"""
    ih, iw = small.shape[:2]
    if min(ih, iw) < _YUNET_MIN_SIDE:
        return None
    if not small.flags["C_CONTIGUOUS"]:
        small = np.ascontiguousarray(small)
    detector = _yunet()
    if detector is None:
        raise FaceDetectorUnavailable("YuNet")
    try:
        with _YUNET_LOCK:
            detector.setInputSize((iw, ih))
            _ok, faces = detector.detect(small)
            if faces is not None:
                faces = faces.copy()
    except cv2.error as exc:
        raise FaceDetectorUnavailable("YuNet") from exc
    return faces


def _yunet_boxes(small: np.ndarray, scale: float, w: int, h: int) -> list[Box]:
    faces = _yunet_rows(small)
    if faces is None:
        return []
    boxes: list[Box] = []
    for row in faces:
        raw = Box(
            int(row[0] * scale),
            int(row[1] * scale),
            int(row[2] * scale),
            int(row[3] * scale),
        )
        right = (float(row[4]) * scale, float(row[5]) * scale)
        left = (float(row[6]) * scale, float(row[7]) * scale)
        boxes.append(face_box_from_eyes(raw, right, left, w, h, pad=0.32))
    return boxes


def unturn_point(
    x: float, y: float, code: int, width: int, height: int
) -> tuple[float, float]:
    """90° 回した絵の点を、回す前の絵（幅 width・高さ height）の点へ戻す。"""
    if code == cv2.ROTATE_90_CLOCKWISE:
        return y, height - x
    return width - y, x


def _turned_yunet_boxes(small: np.ndarray, scale: float, w: int, h: int) -> list[Box]:
    sh, sw = small.shape[:2]
    boxes: list[Box] = []
    for code in (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE):
        faces = _yunet_rows(cv2.rotate(small, code))
        if faces is None:
            continue
        for row in faces:
            corners = [
                unturn_point(float(row[0]), float(row[1]), code, sw, sh),
                unturn_point(float(row[0] + row[2]), float(row[1] + row[3]), code, sw, sh),
            ]
            xs = [point[0] for point in corners]
            ys = [point[1] for point in corners]
            raw = Box(
                int(min(xs) * scale),
                int(min(ys) * scale),
                int((max(xs) - min(xs)) * scale),
                int((max(ys) - min(ys)) * scale),
            )
            right = unturn_point(float(row[4]), float(row[5]), code, sw, sh)
            left = unturn_point(float(row[6]), float(row[7]), code, sw, sh)
            boxes.append(
                face_box_from_eyes(
                    raw,
                    (right[0] * scale, right[1] * scale),
                    (left[0] * scale, left[1] * scale),
                    w,
                    h,
                    pad=0.32,
                )
            )
    return boxes


def _profile_boxes(small: np.ndarray, scale: float, w: int, h: int) -> list[Box]:
    cascade = _profile_cascade()
    if cascade is None:
        return []
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    found = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(32, 32))
    flipped = cv2.flip(gray, 1)
    found_flip = cascade.detectMultiScale(
        flipped, scaleFactor=1.1, minNeighbors=6, minSize=(32, 32)
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


def crop_ahash(bgr: np.ndarray, box: Box) -> str | None:
    x2 = min(bgr.shape[1], box.x + box.w)
    y2 = min(bgr.shape[0], box.y + box.h)
    x1 = max(0, box.x)
    y1 = max(0, box.y)
    crop = bgr[y1:y2, x1:x2]
    if crop.size == 0 or min(crop.shape[:2]) < 8:
        return None
    small = cv2.resize(crop, (8, 8), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    bits = (gray > gray.mean()).flatten()
    value = 0
    for index, on in enumerate(bits):
        if on:
            value |= 1 << int(index)
    return f"{value:016x}"


def face_box_at(boxes: list[Box], nx: float, ny: float, width: int, height: int) -> Box | None:
    if width < 1 or height < 1:
        return None
    px = nx * width
    py = ny * height
    hits = [
        box
        for box in boxes
        if box.x <= px < box.x + box.w and box.y <= py < box.y + box.h
    ]
    if not hits:
        return None
    return min(hits, key=lambda box: box.w * box.h)


def remember_false_faces(hashes: list[str], bgr: np.ndarray, boxes: list[Box]) -> list[str]:
    out = [item for item in hashes if item]
    for box in boxes:
        digest = crop_ahash(bgr, box)
        if digest and digest not in out:
            out.append(digest)
    return out[-_FALSE_HASH_LIMIT:]


def reject_false_faces(bgr: np.ndarray, boxes: list[Box], hashes: list[str]) -> list[Box]:
    known: list[int] = []
    for raw in hashes:
        try:
            known.append(int(raw, 16))
        except ValueError:
            continue
    if not known:
        return boxes
    kept: list[Box] = []
    for box in boxes:
        digest = crop_ahash(bgr, box)
        if digest is None:
            kept.append(box)
            continue
        value = int(digest, 16)
        if any((value ^ other).bit_count() <= _FALSE_HAMMING for other in known):
            continue
        kept.append(box)
    return kept


def _still_extra_boxes(bgr: np.ndarray, w: int, h: int) -> list[Box]:
    """写真だけの追加の探し方。遠くの小さい顔と、横倒しの顔。"""
    boxes: list[Box] = []
    full, full_scale = _downscale(bgr, _STILL_SIDE)
    if max(full.shape[:2]) > max(_DETECT_SIDES):
        boxes.extend(_yunet_boxes(full, full_scale, w, h))
    turned, turned_scale = _downscale(bgr, _TURNED_SIDE)
    boxes.extend(_turned_yunet_boxes(turned, turned_scale, w, h))
    return boxes


def detect_face_boxes(
    bgr: np.ndarray,
    *,
    false_face_hashes: list[str] | None = None,
    pipeline: str | None = None,
    still: bool = False,
) -> list[Box]:
    """顔の枠。still=True（写真）は時間をかけて小さい顔・横倒しの顔も探す。"""
    h, w = bgr.shape[:2]
    if h < 16 or w < 16:
        return []
    boxes: list[Box] = []
    legacy = parse_face_pipeline(pipeline) == FACE_PIPELINE_LEGACY
    if legacy:
        for max_side in _DETECT_SIDES:
            small, scale = _downscale(bgr, max_side)
            boxes.extend(_mediapipe_boxes(small, scale, w, h, strict=True))
        profile_small, profile_scale = _downscale(bgr, 640)
        boxes.extend(_profile_boxes(profile_small, profile_scale, w, h))
    else:
        for max_side in _DETECT_SIDES:
            small, scale = _downscale(bgr, max_side)
            boxes.extend(_yunet_boxes(small, scale, w, h))
        close, close_scale = _downscale(bgr, 640)
        boxes.extend(_mediapipe_boxes(close, close_scale, w, h))
    base = _merge(boxes)
    kept = reject_false_faces(bgr, base, false_face_hashes) if false_face_hashes else base
    if not still or legacy:
        return kept
    # 足した探し方は、いつもの探し方が見ていない所だけ足す。
    # いつもの枠（誤検出として学習済みで消した枠も含む）と重なるものは、これまでの判定のままにする。
    extra = [
        box
        for box in _still_extra_boxes(bgr, w, h)
        if all(_iou(box, other) < _EXTRA_SAME_IOU for other in base)
    ]
    if false_face_hashes:
        extra = reject_false_faces(bgr, extra, false_face_hashes)
    return kept + _merge(extra)
