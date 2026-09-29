import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from stream_media_viewer.detect import faces
from stream_media_viewer.detect.blur import Box
from stream_media_viewer.detect.faces import (
    FaceDetectorUnavailable,
    FaceHold,
    crop_ahash,
    detect_face_boxes,
    face_box_at,
    face_box_from_eyes,
    hold_face_boxes,
    oval_angle_deg,
    reject_false_faces,
    remember_false_faces,
    unturn_point,
)
from stream_media_viewer.detect.protect import protect_frame_safe
from stream_media_viewer.settings import FACE_PIPELINE_ACCURATE, FACE_PIPELINE_LEGACY


def test_false_face_hash_rejects_same_crop() -> None:
    bgr = np.zeros((64, 64, 3), dtype=np.uint8)
    bgr[8:40, 8:40] = (40, 80, 180)
    box = Box(8, 8, 32, 32)
    hashes = remember_false_faces([], bgr, [box])
    assert hashes
    kept = reject_false_faces(bgr, [box], hashes)
    assert kept == []


def test_false_face_hash_keeps_different_crop() -> None:
    first = np.zeros((64, 64, 3), dtype=np.uint8)
    first[8:40, 8:24] = 20
    first[8:40, 24:40] = 220
    second = np.zeros((64, 64, 3), dtype=np.uint8)
    second[8:40, 8:24] = 220
    second[8:40, 24:40] = 20
    box = Box(8, 8, 32, 32)
    hashes = remember_false_faces([], first, [box])
    kept = reject_false_faces(second, [box], hashes)
    assert len(kept) == 1
    assert crop_ahash(first, box) != crop_ahash(second, box)


def test_hold_face_boxes_keeps_previous_when_current_misses() -> None:
    previous = [Box(10, 10, 20, 20)]
    kept = hold_face_boxes([], previous)
    assert kept == previous
    assert hold_face_boxes([], None) == []
    assert hold_face_boxes([Box(40, 40, 8, 8)], previous) == [
        Box(10, 10, 20, 20),
        Box(40, 40, 8, 8),
    ]


def test_face_hold_lasts_one_missed_frame_then_drops() -> None:
    hold = FaceHold()
    first = [Box(4, 4, 12, 12)]
    assert hold.step(first) == first
    assert hold.step([]) == first
    assert hold.step([]) == []
    hold.reset()
    assert hold.step([]) == []


def test_oval_angle_deg_follows_eye_line() -> None:
    assert oval_angle_deg((0.0, 0.0), (10.0, 0.0)) == 0.0
    assert oval_angle_deg((0.0, 0.0), (0.0, 10.0)) == 90.0


def test_face_box_from_eyes_keeps_tilt() -> None:
    box = face_box_from_eyes(Box(10, 10, 20, 20), (10.0, 10.0), (30.0, 30.0), 80, 80)
    assert box.angle == 45.0
    assert box.x <= 10
    assert box.y <= 10


def test_detect_face_boxes_blank_image_empty_legacy() -> None:
    blank = np.zeros((64, 64, 3), dtype=np.uint8)
    assert detect_face_boxes(blank, pipeline=FACE_PIPELINE_LEGACY) == []


def test_detect_face_boxes_blank_image_empty_accurate() -> None:
    blank = np.zeros((320, 320, 3), dtype=np.uint8)
    assert detect_face_boxes(blank, pipeline=FACE_PIPELINE_ACCURATE) == []


def test_detect_face_boxes_tiny_image_empty_for_both_pipelines() -> None:
    tiny = np.zeros((8, 8, 3), dtype=np.uint8)
    assert detect_face_boxes(tiny, pipeline=FACE_PIPELINE_LEGACY) == []
    assert detect_face_boxes(tiny, pipeline=FACE_PIPELINE_ACCURATE) == []


def test_face_box_at_picks_smallest_hit() -> None:
    inner = Box(10, 10, 10, 10)
    outer = Box(0, 0, 40, 40)
    hit = face_box_at([outer, inner], 0.3, 0.3, 50, 50)
    assert hit == inner
    assert face_box_at([outer], 0.9, 0.9, 50, 50) is None


def test_unturn_point_goes_back_to_the_original_pixel() -> None:
    image = np.zeros((30, 50), dtype=np.uint8)
    image[7, 41] = 255
    for code in (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE):
        turned = cv2.rotate(image, code)
        ys, xs = np.nonzero(turned)
        # 画素の真ん中どうしで比べる
        x, y = unturn_point(float(xs[0]) + 0.5, float(ys[0]) + 0.5, code, 50, 30)
        assert (int(x), int(y)) == (41, 7)


def _patch_detectors(monkeypatch, *, base: list[Box], extra: list[Box]) -> None:
    monkeypatch.setattr(faces, "_yunet_boxes", lambda *_a: list(base) if _a[1] >= 1.0 else [])
    monkeypatch.setattr(faces, "_mediapipe_boxes", lambda *_a, **_k: [])
    monkeypatch.setattr(faces, "_still_extra_boxes", lambda *_a: list(extra))


def test_still_extra_boxes_only_add_places_the_usual_detector_missed(monkeypatch) -> None:
    bgr = np.zeros((200, 200, 3), dtype=np.uint8)
    usual = Box(20, 20, 60, 60)
    same_place = Box(24, 22, 58, 62)
    far_small = Box(150, 150, 20, 20)
    _patch_detectors(monkeypatch, base=[usual], extra=[same_place, far_small])
    assert detect_face_boxes(bgr) == [usual]
    assert detect_face_boxes(bgr, still=True) == [usual, far_small]


def test_still_extra_boxes_do_not_bring_back_learned_false_faces(monkeypatch) -> None:
    # 学習済みの誤検出を、足した探し方が少し違う枠で出し直さないこと。
    bgr = np.zeros((200, 200, 3), dtype=np.uint8)
    bgr[20:80, 20:50] = 200
    learned = Box(20, 20, 60, 60)
    shifted = Box(26, 18, 60, 64)
    _patch_detectors(monkeypatch, base=[learned], extra=[shifted])
    hashes = remember_false_faces([], bgr, [learned])
    assert detect_face_boxes(bgr, false_face_hashes=hashes, still=True) == []


def _portrait() -> np.ndarray | None:
    try:
        from matplotlib import cbook
    except ImportError:
        return None
    try:
        path = Path(cbook.get_sample_data("grace_hopper.jpg", asfileobj=False))
    except (OSError, ValueError):
        return None
    return cv2.imread(str(path))


# grace_hopper.jpg（パブリックドメイン）の顔の位置
_PORTRAIT_FACE = (183, 120, 170, 212)


def _covered(face: tuple[int, int, int, int], boxes: list[Box], need: float = 0.5) -> bool:
    fx, fy, fw, fh = face
    for box in boxes:
        w = max(0, min(fx + fw, box.x + box.w) - max(fx, box.x))
        h = max(0, min(fy + fh, box.y + box.h) - max(fy, box.y))
        if w * h >= need * fw * fh:
            return True
    return False


def test_photo_finds_a_small_far_face() -> None:
    portrait = _portrait()
    if portrait is None:
        pytest.skip("sample portrait not available")
    rng = np.random.default_rng(3)
    canvas = cv2.resize(
        rng.integers(40, 200, (40, 60, 3), dtype=np.uint8), (1920, 1280),
        interpolation=cv2.INTER_CUBIC,
    )
    scale = 18 / _PORTRAIT_FACE[2]
    small = cv2.resize(portrait, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    canvas[600 : 600 + small.shape[0], 900 : 900 + small.shape[1]] = small
    fx, fy, fw, fh = (int(v * scale) for v in _PORTRAIT_FACE)
    face = (900 + fx, 600 + fy, fw, fh)
    assert _covered(face, detect_face_boxes(canvas, still=True))


def test_photo_finds_a_sideways_face_without_mediapipe(monkeypatch) -> None:
    portrait = _portrait()
    if portrait is None:
        pytest.skip("sample portrait not available")
    # Mac は MediaPipe を使わない。YuNet だけでも横倒しの顔を拾うこと。
    monkeypatch.setattr(faces, "_mediapipe_boxes", lambda *_a, **_k: [])
    turned = cv2.rotate(portrait, cv2.ROTATE_90_CLOCKWISE)
    h = portrait.shape[0]
    fx, fy, fw, fh = _PORTRAIT_FACE
    face = (h - (fy + fh), fx, fh, fw)
    assert _covered(face, detect_face_boxes(turned, still=True))


def _copy_to_japanese_folder(tmp_path: Path, source: Path) -> Path:
    folder = tmp_path / "山田の配信ツール"
    folder.mkdir(exist_ok=True)
    target = folder / source.name
    target.write_bytes(source.read_bytes())
    return target


def test_yunet_loads_from_a_japanese_folder(tmp_path: Path, monkeypatch) -> None:
    # zip を日本語のユーザーフォルダなどに展開しても、顔を探す部品が読めること。
    monkeypatch.setattr(faces, "_YUNET", _copy_to_japanese_folder(tmp_path, faces._YUNET))
    faces._yunet.cache_clear()
    try:
        assert faces._yunet() is not None
    finally:
        faces._yunet.cache_clear()


@pytest.mark.skipif(sys.platform == "darwin", reason="Mac は MediaPipe を使わない")
def test_mediapipe_loads_from_a_japanese_folder(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(faces, "_MODEL", _copy_to_japanese_folder(tmp_path, faces._MODEL))
    faces._image_detector.cache_clear()
    try:
        assert faces._image_detector() is not None
    finally:
        faces._image_detector.cache_clear()


def test_missing_face_detector_fails_closed(monkeypatch) -> None:
    # 部品が使えないときに「顔なし」として素顔を通さない。処理の失敗にする。
    monkeypatch.setattr(faces, "_yunet", lambda: None)
    bgr = np.full((360, 480, 3), 120, dtype=np.uint8)
    with pytest.raises(FaceDetectorUnavailable):
        detect_face_boxes(bgr)
    out, has_face, _ = protect_frame_safe(
        bgr, face_blur=True, text_blur=False, marks=[], strength=31
    )
    assert out is None
    assert not has_face
    # 顔ぼかしがオフなら部品は使わないので送れる
    out, _, _ = protect_frame_safe(bgr, face_blur=False, text_blur=False, marks=[], strength=31)
    assert out is not None
