import numpy as np

from stream_media_viewer.detect.text_regions import detect_text_boxes


def _plate_image() -> np.ndarray:
    image = np.full((240, 400, 3), 30, dtype=np.uint8)
    image[168:204, 140:300] = 240
    for x in range(148, 292, 22):
        image[174:198, x : x + 10] = 20
    return image


def test_detects_horizontal_plate_like_block() -> None:
    boxes = detect_text_boxes(_plate_image())
    assert boxes
    hit = any(box.w > box.h * 1.5 and box.y > 100 for box in boxes)
    assert hit


def test_plain_window_and_pole_are_not_plates() -> None:
    image = np.full((240, 400, 3), 40, dtype=np.uint8)
    image[20:90, 40:220] = 220
    image[40:200, 300:318] = 210
    boxes = detect_text_boxes(image)
    assert boxes == []


def test_speckle_texture_is_not_a_name_tag() -> None:
    rng = np.random.default_rng(0)
    image = np.full((240, 400, 3), 80, dtype=np.uint8)
    noise = rng.integers(0, 90, size=image.shape, dtype=np.uint8)
    image = cv2_add(image, noise)
    boxes = detect_text_boxes(image)
    assert boxes == []


def cv2_add(image: np.ndarray, noise: np.ndarray) -> np.ndarray:
    return np.clip(image.astype(np.int16) + noise.astype(np.int16), 0, 255).astype(np.uint8)
