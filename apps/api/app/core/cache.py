from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheItem:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheItem] = {}

    def get(self, key: str) -> tuple[Any | None, bool]:
        item = self._store.get(key)
        if not item:
            return None, False
        if item.expires_at < time.time():
            self._store.pop(key, None)
            return None, False
        return item.value, True

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = CacheItem(value=value, expires_at=time.time() + ttl_seconds)

    def clear(self) -> None:
        self._store.clear()


cache = TTLCache()
