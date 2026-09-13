import re
import threading
import time
from collections.abc import Callable


def normalize_query(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class TTLCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._data: dict[str, tuple[float, object]] = {}
        self._lock = threading.RLock()

    def get(self, key: str):
        now = time.monotonic()
        with self._lock:
            value = self._data.get(key)
            if value is None:
                return None
            expires_at, payload = value
            if now >= expires_at:
                del self._data[key]
                return None
            return payload

    def set(self, key: str, value: object) -> None:
        with self._lock:
            self._data[key] = (time.monotonic() + self.ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


def cache_result(ttl: int = 300):
    cache = TTLCache(ttl=ttl)

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            key = repr((args, tuple(sorted(kwargs.items()))))
            cached = cache.get(key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper

    return decorator
