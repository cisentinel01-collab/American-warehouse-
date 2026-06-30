import cachetools
from typing import Any, Optional

class CacheManager:
    _instance = None
    # In-memory cache for items, suppliers, etc.
    # In professional ERP, this could be Redis.
    _cache = cachetools.TTLCache(maxsize=1000, ttl=300)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance

    def set(self, key: str, value: Any):
        self._cache[key] = value

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def clear(self):
        self._cache.clear()

cache = CacheManager()
