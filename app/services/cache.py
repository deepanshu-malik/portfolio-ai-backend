"""Simple in-memory cache with TTL for response caching."""

import hashlib
import logging
import time
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL (Time To Live).

    Features:
    - TTL-based expiration
    - LRU-style eviction (keeps last 100 entries)
    - Cache hit/miss tracking
    - Message+intent based key generation
    """

    def __init__(self, ttl: int = 1800, max_size: int = 100):
        """
        Initialize the cache.

        Args:
            ttl: Time to live in seconds (default 30 minutes)
            max_size: Maximum number of cached entries (default 100)
        """
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _generate_key(self, message: str, intent: str = "") -> str:
        """
        Generate cache key from message and intent.

        Args:
            message: User's message
            intent: Detected intent (optional)

        Returns:
            MD5 hash of message+intent
        """
        key_string = f"{message.lower().strip()}:{intent}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, message: str, intent: str = "") -> Optional[Any]:
        """
        Get cached response if available and not expired.

        Args:
            message: User's message
            intent: Detected intent

        Returns:
            Cached value or None if not found/expired
        """
        key = self._generate_key(message, intent)

        if key in self.cache:
            value, timestamp = self.cache[key]

            # Check if expired
            if time.time() - timestamp < self.ttl:
                self.hits += 1
                logger.debug(f"Cache HIT for key: {key[:8]}...")
                return value
            else:
                # Expired, remove from cache
                del self.cache[key]
                logger.debug(f"Cache EXPIRED for key: {key[:8]}...")

        self.misses += 1
        logger.debug(f"Cache MISS for key: {key[:8]}...")
        return None

    def set(self, message: str, value: Any, intent: str = "") -> None:
        """
        Cache a response.

        Args:
            message: User's message
            value: Response to cache
            intent: Detected intent
        """
        key = self._generate_key(message, intent)

        # Add to cache with current timestamp
        self.cache[key] = (value, time.time())

        # Evict oldest entries if cache is too large
        if len(self.cache) > self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
            del self.cache[oldest_key]
            logger.debug(f"Cache EVICTED key: {oldest_key[:8]}... (size: {len(self.cache)})")

        logger.debug(f"Cache SET for key: {key[:8]}... (size: {len(self.cache)})")

    def clear(self) -> None:
        """Clear all cached entries."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache CLEARED: {count} entries removed")

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired = [
            key
            for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.ttl
        ]

        for key in expired:
            del self.cache[key]

        if expired:
            logger.info(f"Cache CLEANUP: {len(expired)} expired entries removed")

        return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.ttl,
        }


# Global cache instance (30 minute TTL, 100 entry limit)
response_cache = SimpleCache(ttl=1800, max_size=100)
