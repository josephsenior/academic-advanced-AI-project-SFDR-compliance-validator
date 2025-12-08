"""
LLM Response Cache
Caches LLM responses to avoid redundant API calls
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class LLMCache:
    """Cache for LLM API responses to reduce costs and improve performance"""
    
    def __init__(self, cache_dir: str = ".cache/llm", ttl_hours: int = 168):
        """
        Initialize LLM cache
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours (default: 7 days)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.stats = {"hits": 0, "misses": 0, "expired": 0}
    
    def _compute_key(self, prompt: str, model: str, **kwargs) -> str:
        """Compute cache key from prompt and parameters"""
        # Include model and relevant parameters in key
        cache_input = {
            "prompt": prompt,
            "model": model,
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": kwargs.get("max_tokens"),
        }
        
        # Create hash
        cache_str = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key"""
        # Use first 2 chars as subdirectory for better filesystem performance
        subdir = self.cache_dir / key[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{key}.json"
    
    def get(self, prompt: str, model: str, **kwargs) -> Optional[Any]:
        """
        Get cached response
        
        Args:
            prompt: The prompt text
            model: Model name
            **kwargs: Additional parameters used in key generation
        
        Returns:
            Cached response or None if not found/expired
        """
        key = self._compute_key(prompt, model, **kwargs)
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self.stats["misses"] += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check expiration
            cached_at = datetime.fromisoformat(cached_data["cached_at"])
            if datetime.utcnow() - cached_at > self.ttl:
                logger.debug(f"Cache expired for key: {key[:8]}")
                self.stats["expired"] += 1
                cache_path.unlink()  # Delete expired cache
                return None
            
            self.stats["hits"] += 1
            logger.debug(f"Cache hit for key: {key[:8]}")
            return cached_data["response"]
            
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            self.stats["misses"] += 1
            return None
    
    def set(self, prompt: str, model: str, response: Any, **kwargs) -> None:
        """
        Cache a response
        
        Args:
            prompt: The prompt text
            model: Model name
            response: The response to cache
            **kwargs: Additional parameters used in key generation
        """
        key = self._compute_key(prompt, model, **kwargs)
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            "cached_at": datetime.utcnow().isoformat(),
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
            "model": model,
            "response": response
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cached response for key: {key[:8]}")
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")
    
    def clear(self) -> int:
        """Clear all cache entries"""
        count = 0
        for cache_file in self.cache_dir.rglob("*.json"):
            cache_file.unlink()
            count += 1
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def clear_expired(self) -> int:
        """Clear expired cache entries"""
        count = 0
        for cache_file in self.cache_dir.rglob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                cached_at = datetime.fromisoformat(cached_data["cached_at"])
                if datetime.utcnow() - cached_at > self.ttl:
                    cache_file.unlink()
                    count += 1
            except Exception:
                pass
        
        logger.info(f"Cleared {count} expired cache entries")
        return count
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Count cache files
        cache_files = list(self.cache_dir.rglob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "expired": self.stats["expired"],
            "hit_rate": f"{hit_rate:.1f}%",
            "total_entries": len(cache_files),
            "total_size_mb": f"{total_size / 1024 / 1024:.2f}"
        }


# Global cache instance
_global_cache = None


def get_llm_cache(cache_dir: str = ".cache/llm", ttl_hours: int = 168) -> LLMCache:
    """Get or create global LLM cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = LLMCache(cache_dir, ttl_hours)
    return _global_cache


if __name__ == "__main__":
    # Test cache
    cache = LLMCache()
    
    # Test caching
    prompt = "What is 2+2?"
    model = "gpt-4"
    
    # First call - miss
    result = cache.get(prompt, model)
    print(f"First call: {result}")
    
    # Cache response
    cache.set(prompt, model, "4")
    
    # Second call - hit
    result = cache.get(prompt, model)
    print(f"Second call: {result}")
    
    # Stats
    print(f"Stats: {cache.get_stats()}")
