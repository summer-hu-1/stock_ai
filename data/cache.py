import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta


class DataHubCache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = threading.Lock()
        self._default_ttl = {
            "daily": 3600,
            "realtime": 60,
            "market_state": 300,
            "sector": 300,
            "index": 300,
            "info": 3600,
        }
        self._initialized = True

    def get(self, key: str) -> Optional[Any]:
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._cache[key]
                return None
            entry.hit_count += 1
            entry.last_access = time.time()
            return entry.value

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        with self._cache_lock:
            cache_type = self._get_cache_type(key)
            actual_ttl = ttl or self._default_ttl.get(cache_type, 300)
            self._cache[key] = CacheEntry(value, actual_ttl)

    def delete(self, key: str) -> None:
        with self._cache_lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self, pattern: str = None) -> int:
        with self._cache_lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                return count
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    def invalidate(self, prefix: str) -> int:
        return self.clear(prefix)

    def get_or_load(self, key: str, loader: Callable[[], Any], ttl: int = None) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = loader()
        self.set(key, value, ttl)
        return value

    def _get_cache_type(self, key: str) -> str:
        if "realtime" in key or "_rt_" in key:
            return "realtime"
        if "daily" in key or "_d_" in key:
            return "daily"
        if "state" in key or "memory" in key:
            return "market_state"
        if "sector" in key:
            return "sector"
        if "index" in key:
            return "index"
        return "info"

    def stats(self) -> Dict[str, Any]:
        with self._cache_lock:
            total = len(self._cache)
            expired = sum(1 for e in self._cache.values() if e.is_expired())
            hits = sum(e.hit_count for e in self._cache.values())
            return {
                "total_entries": total,
                "expired_entries": expired,
                "total_hits": hits,
                "cache_types": {k: len([e for e in self._cache.values() if self._get_cache_type(k) == k])
                               for k in self._default_ttl.keys()}
            }


class CacheEntry:
    __slots__ = ['value', 'expire_at', 'created_at', 'hit_count', 'last_access']

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.expire_at = self.created_at + ttl
        self.hit_count = 0
        self.last_access = self.created_at

    def is_expired(self) -> bool:
        return time.time() > self.expire_at

    def remaining_ttl(self) -> int:
        remaining = self.expire_at - time.time()
        return max(0, int(remaining))


_cache_instance: Optional[DataHubCache] = None


def get_cache() -> DataHubCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DataHubCache()
    return _cache_instance