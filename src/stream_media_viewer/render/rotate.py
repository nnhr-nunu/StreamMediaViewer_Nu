from __future__ import annotations

from typing import Any

import numpy as np

_ALLOWED = {0, 90, 180, 270}


def clamp_rotation(value: object) -> int:
    try:
        degrees = int(value) % 360
    except (TypeError, ValueError):
        return 0
    if degrees < 0:
        degrees += 360
    if degrees in _ALLOWED:
        return degrees
    return 0


def rotate_bgr(bgr: np.ndarray, degrees: int) -> np.ndarray:
    deg = clamp_rotation(degrees)
    if deg == 0:
        return bgr
    import cv2

    if deg == 90:
        return cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
    if deg == 180:
        return cv2.rotate(bgr, cv2.ROTATE_180)
    return cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)


def _map_point(x: float, y: float, degrees: int) -> tuple[float, float]:
    deg = clamp_rotation(degrees)
    if deg == 90:
        return 1.0 - y, x
    if deg == 180:
        return 1.0 - x, 1.0 - y
    if deg == 270:
        return y, 1.0 - x
    return x, y


def rotate_marks(marks: list[dict[str, Any]], degrees: int) -> list[dict[str, Any]]:
    deg = clamp_rotation(degrees)
    if deg == 0:
        return [dict(mark) for mark in marks]
    out: list[dict[str, Any]] = []
    for mark in marks:
        item = dict(mark)
        kind = item.get("kind")
        if kind == "rect":
            x = float(item.get("x") or 0)
            y = float(item.get("y") or 0)
            width = float(item.get("w") or 0)
            height = float(item.get("h") or 0)
            corners = [
                (x, y),
                (x + width, y),
                (x, y + height),
                (x + width, y + height),
            ]
            mapped = [_map_point(px, py, deg) for px, py in corners]
            xs = [point[0] for point in mapped]
            ys = [point[1] for point in mapped]
            item["x"] = min(xs)
            item["y"] = min(ys)
            item["w"] = max(xs) - min(xs)
            item["h"] = max(ys) - min(ys)
        elif kind == "stroke":
            points = item.get("points") or []
            moved: list[list[float]] = []
            for point in points:
                if not isinstance(point, (list, tuple)) or len(point) < 2:
                    continue
                nx, ny = _map_point(float(point[0]), float(point[1]), deg)
                moved.append([nx, ny])
            item["points"] = moved
        out.append(item)
    return out
