import numpy as np

from stream_media_viewer.detect.blur import Box
from stream_media_viewer.detect.faces import (
    FaceHold,
    crop_ahash,
    detect_face_boxes,
    face_box_at,
    face_box_from_eyes,
    hold_face_boxes,
    oval_angle_deg,
    reject_false_faces,
    remember_false_faces,
)
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


def test_detect_face_boxes_blank_image_empty_for_both_pipelines() -> None:
    blank = np.zeros((64, 64, 3), dtype=np.uint8)
    assert detect_face_boxes(blank, pipeline=FACE_PIPELINE_LEGACY) == []
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
