from pathlib import Path

from stream_media_viewer.library.auto_prep import (
    CHECKS_PER_TICK,
    MAX_REST_MS,
    MIN_REST_MS,
    AutoPrepQueue,
    nearest_rows,
    rest_ms,
)
from stream_media_viewer.library.item import MediaItem


def _photo(name: str, *, kind: str = "image", readable: bool = True) -> MediaItem:
    item = MediaItem(path=Path(name), kind=kind, captured_at=None, has_gps=False)
    item.readable = readable
    return item


def test_nearest_rows_go_outward_from_the_current_row() -> None:
    assert nearest_rows(6, 2) == [3, 1, 4, 0, 5]
    assert nearest_rows(1, 0) == []


def test_rest_grows_with_the_work_and_more_while_live() -> None:
    assert rest_ms(0.0, live=False) == MIN_REST_MS
    assert rest_ms(0.5, live=False) == 1000
    assert rest_ms(0.5, live=True) == 2500
    assert rest_ms(60.0, live=True) == MAX_REST_MS


def test_queue_starts_near_the_current_photo_and_skips_videos() -> None:
    items = [_photo("a.jpg"), _photo("b.mp4", kind="video"), _photo("c.jpg"), _photo("d.jpg")]
    hidden_away = _photo("z.jpg")
    broken = _photo("x.jpg", readable=False)
    queue = AutoPrepQueue()
    queue.rebuild(items, 2, others=[hidden_away, broken])
    order = []
    while (item := queue.take_next(lambda _it: False)) is not None:
        order.append(item.path.name)
        queue.mark_done(item)
    assert order == ["c.jpg", "d.jpg", "a.jpg", "z.jpg"]


def test_ready_photos_are_skipped_and_counted_as_done() -> None:
    items = [_photo(f"{n}.jpg") for n in range(5)]
    queue = AutoPrepQueue()
    queue.rebuild(items, 0)
    ready = {"0.jpg", "1.jpg"}
    first = queue.take_next(lambda it: it.path.name in ready)
    assert first is not None and first.path.name == "2.jpg"
    queue.inflight = True
    assert queue.progress() == (2, 5)
    queue.inflight = False
    queue.mark_done(first)
    # 並べ直しても、済んだものは数え直さない
    queue.rebuild(items, 4)
    assert queue.progress() == (3, 5)


def test_one_tick_checks_only_a_limited_number() -> None:
    items = [_photo(f"{n}.jpg") for n in range(CHECKS_PER_TICK + 5)]
    queue = AutoPrepQueue()
    queue.rebuild(items, 0)
    assert queue.take_next(lambda _it: True) is None
    assert queue.pending
    assert queue.take_next(lambda _it: True) is None
    assert not queue.pending
    done, total = queue.progress()
    assert done == total == len(items)


def test_forget_starts_over() -> None:
    items = [_photo("a.jpg")]
    queue = AutoPrepQueue()
    queue.rebuild(items, 0)
    queue.mark_done(queue.take_next(lambda _it: False))
    queue.forget()
    queue.rebuild(items, 0)
    assert queue.progress() == (0, 1)
