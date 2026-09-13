"""誤検出の記録。配信用の窓には出さない。"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

_CATALOG_NAME = "false_face_hashes.json"
_HASH_LIMIT = 300


def catalog_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / _CATALOG_NAME


def _read_hashes(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    items = raw.get("hashes") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    return [str(item) for item in items if str(item).strip()]


@lru_cache(maxsize=1)
def load_shipped_hashes() -> tuple[str, ...]:
    return tuple(_read_hashes(catalog_path()))


def merge_false_face_hashes(*groups: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for item in group:
            key = str(item).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(key)
    return out[-_HASH_LIMIT:]


def effective_false_face_hashes(user: list[str] | None = None) -> list[str]:
    return merge_false_face_hashes(load_shipped_hashes(), user or [])


def save_shipped_hashes(hashes: list[str], path: Path | None = None) -> None:
    target = path or catalog_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"hashes": merge_false_face_hashes(hashes)}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    load_shipped_hashes.cache_clear()


def try_update_shipped_catalog(hashes: list[str]) -> bool:
    """ソース起動のときだけ同梱ファイルを更新する。exe では書き換えない。"""
    if getattr(sys, "frozen", False):
        return False
    try:
        merged = merge_false_face_hashes(load_shipped_hashes(), hashes)
        save_shipped_hashes(merged)
    except OSError:
        return False
    return True
