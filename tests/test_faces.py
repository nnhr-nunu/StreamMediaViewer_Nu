import numpy as np

from stream_media_viewer.detect.blur import Box
from stream_media_viewer.detect.faces import crop_ahash, face_box_at, reject_false_faces, remember_false_faces


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


def test_face_box_at_picks_smallest_hit() -> None:
    inner = Box(10, 10, 10, 10)
    outer = Box(0, 0, 40, 40)
    hit = face_box_at([outer, inner], 0.3, 0.3, 50, 50)
    assert hit == inner
    assert face_box_at([outer], 0.9, 0.9, 50, 50) is None
