import numpy as np

from stream_media_viewer.detect.blur import Box
from stream_media_viewer.detect.faces import crop_ahash, reject_false_faces, remember_false_faces


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
