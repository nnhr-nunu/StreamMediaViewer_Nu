from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage, QPixmap


def bgr_to_pixmap(bgr: np.ndarray) -> QPixmap:
    if bgr.ndim != 3 or bgr.shape[0] < 1 or bgr.shape[1] < 1 or bgr.shape[2] != 3:
        return QPixmap()
    rgb = np.ascontiguousarray(bgr[:, :, ::-1])
    height, width, _ = rgb.shape
    image = QImage(rgb.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(image)
