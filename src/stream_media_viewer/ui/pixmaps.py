from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage, QPixmap


def bgr_to_pixmap(bgr: np.ndarray) -> QPixmap:
    rgb = np.ascontiguousarray(bgr[:, :, ::-1])
    height, width, _ = rgb.shape
    image = QImage(rgb.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(image)
