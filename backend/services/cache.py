from collections import OrderedDict
import time
from typing import Any, Optional

class QueryCache:
    """
    Bounded in-memory LRU cache with TTL for optional query caching.
    """
    def __init__(self, maxsize: int = 100, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp <= self.ttl_seconds:
                self.cache.move_to_end(key)
                return value
            else:
                del self.cache[key]
        return None
        
    def set(self, key: str, value: Any):
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False)
        self.cache[key] = (value, time.time())
        
    def clear(self):
        self.cache.clear()

query_cache = QueryCache(maxsize=200, ttl_seconds=3600)
