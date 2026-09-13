import numpy as np

from stream_media_viewer.detect.text_regions import detect_text_boxes


def test_detects_horizontal_plate_like_block() -> None:
    image = np.full((240, 400, 3), 30, dtype=np.uint8)
    image[160:200, 80:320] = 240
    for x in range(90, 310, 18):
        image[168:192, x : x + 8] = 20
    boxes = detect_text_boxes(image)
    assert boxes
    hit = any(box.w > box.h * 1.5 and box.y > 100 for box in boxes)
    assert hit
