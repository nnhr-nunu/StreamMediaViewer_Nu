"""一覧の絞り込み。UI から独立して試せる。"""

from __future__ import annotations

from datetime import date, datetime


PLACE_NONE = "__none__"


def passes_filters(
    *,
    readable: bool = True,
    kind: str = "image",
    favorite: bool = False,
    has_face: bool = False,
    has_gps: bool = False,
    place_name: str = "",
    captured_at: datetime | None = None,
    star_only: bool = False,
    photos: bool = False,
    videos: bool = False,
    faces: bool = False,
    gps_yes: bool = False,
    gps_no: bool = False,
    place: str = "",
    folder: str = "",
    relative_folder: str = "",
    dates: bool = False,
    date_from: date | None = None,
    date_to: date | None = None,
    hidden: bool = False,
    show_hidden: bool = False,
) -> bool:
    if not readable:
        return False
    if show_hidden:
        if not hidden:
            return False
    elif hidden:
        return False
    if star_only and not favorite:
        return False
    if photos and kind != "image":
        return False
    if videos and kind != "video":
        return False
    if faces and not has_face:
        return False
    if gps_yes and not has_gps:
        return False
    if gps_no and has_gps:
        return False
    wanted = place.strip()
    if wanted == PLACE_NONE:
        if has_gps:
            return False
    elif wanted and place_name != wanted:
        return False
    wanted_folder = folder.strip()
    if wanted_folder and relative_folder != wanted_folder:
        return False
    if dates:
        if captured_at is None or date_from is None or date_to is None:
            return False
        day = captured_at.date()
        if day < date_from or day > date_to:
            return False
    return True
