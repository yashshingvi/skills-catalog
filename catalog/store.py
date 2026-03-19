"""
In-memory catalog store.

All items are held in a dict keyed by relative file path.
A RLock protects reads and writes so watchdog threads are safe.
"""
from __future__ import annotations

import threading
from typing import Iterator

from .models import CatalogItem

_lock = threading.RLock()
_items: dict[str, CatalogItem] = {}   # file_path -> CatalogItem


# ── writes ────────────────────────────────────────────────────────────────────

def upsert(item: CatalogItem) -> None:
    with _lock:
        _items[item.file_path] = item


def remove(file_path: str) -> None:
    with _lock:
        _items.pop(file_path, None)


def clear() -> None:
    with _lock:
        _items.clear()


# ── reads ─────────────────────────────────────────────────────────────────────

def all_items() -> list[CatalogItem]:
    with _lock:
        return list(_items.values())


def get_by_path(file_path: str) -> CatalogItem | None:
    with _lock:
        return _items.get(file_path)


def get_by_name(name: str) -> list[CatalogItem]:
    """All items whose name matches (may be multiple versions)."""
    with _lock:
        return [i for i in _items.values() if i.name == name]


def count() -> int:
    with _lock:
        return len(_items)
