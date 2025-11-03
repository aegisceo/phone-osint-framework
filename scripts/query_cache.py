#!/usr/bin/env python3
"""
Smart Query Caching System
Prevents duplicate API calls and manages quota usage across investigations
"""

import os
import json
import hashlib
import time
from typing import Dict, Optional
from pathlib import Path

class QueryCache:
    """
    Intelligent caching system for search API results
    Prevents duplicate queries and tracks quota usage
    """

    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session_cache = {}  # In-memory cache for current session
        self.quota_tracker = {}  # Track API usage per day
        
    def _get_cache_key(self, query: str, api_type: str) -> str:
        """Generate cache key for query"""
        combined = f"{api_type}:{query}".lower()
        return hashlib.md5(combined.encode()).hexdigest()
        
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get path to cache file"""
        return self.cache_dir / f"{cache_key}.json"
        
    def _is_cache_valid(self, cache_file: Path, ttl_hours: int = 24) -> bool:
        """Check if cache is still valid (default 24 hours)"""
        if not cache_file.exists():
            return False
            
        file_age = time.time() - cache_file.stat().st_mtime
        return file_age < (ttl_hours * 3600)
    
    def get_cached_result(self, query: str, api_type: str) -> Optional[Dict]:
        """Get cached result if available and valid"""
        cache_key = self._get_cache_key(query, api_type)
        
        # Check session cache first (fastest)
        if cache_key in self.session_cache:
            return self.session_cache[cache_key]
            
        # Check persistent cache
        cache_file = self._get_cache_file(cache_key)
        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    
                # Add to session cache
                self.session_cache[cache_key] = cached_data['result']
                return cached_data['result']
                
            except Exception as e:
                # Cache corrupted, remove it
                cache_file.unlink(missing_ok=True)
                
        return None
    
    def cache_result(self, query: str, api_type: str, result: Dict):
        """Cache search result for future use"""
        cache_key = self._get_cache_key(query, api_type)
        
        # Store in session cache
        self.session_cache[cache_key] = result
        
        # Store in persistent cache
        cache_data = {
            'query': query,
            'api_type': api_type,
            'timestamp': time.time(),
            'result': result
        }
        
        cache_file = self._get_cache_file(cache_key)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            pass  # Cache write failure shouldn't break investigation
    
    def track_quota_usage(self, api_type: str):
        """Track API quota usage by day"""
        today = time.strftime('%Y-%m-%d')
        key = f"{api_type}_{today}"
        
        if key not in self.quota_tracker:
            self.quota_tracker[key] = 0
        self.quota_tracker[key] += 1
        
        # Log quota usage for monitoring
        if self.quota_tracker[key] % 10 == 0:  # Every 10 queries
            total = self.quota_tracker[key]
            if api_type == 'google' and total >= 80:
                logging.getLogger(__name__).warning(f"⚠️ Google quota usage: {total}/100 - approaching limit!")
            elif api_type == 'serpapi' and total >= 200:
                logging.getLogger(__name__).warning(f"⚠️ SerpAPI quota usage: {total}/250 - approaching limit!")
    
    def get_quota_status(self) -> Dict:
        """Get current quota usage status"""
        today = time.strftime('%Y-%m-%d')
        return {
            'google_today': self.quota_tracker.get(f"google_{today}", 0),
            'serpapi_today': self.quota_tracker.get(f"serpapi_{today}", 0),
            'session_cache_size': len(self.session_cache),
            'persistent_cache_files': len(list(self.cache_dir.glob('*.json')))
        }
    
    def should_skip_query(self, api_type: str) -> bool:
        """Check if we should skip query due to quota concerns"""
        today = time.strftime('%Y-%m-%d')
        usage = self.quota_tracker.get(f"{api_type}_{today}", 0)
        
        # Conservative thresholds to prevent hitting limits
        limits = {
            'google': 90,     # Save 10 queries for emergencies
            'serpapi': 240    # Save 10 queries for emergencies  
        }
        
        return usage >= limits.get(api_type, 999)
    
    def clear_old_cache(self, days_old: int = 7):
        """Clear cache files older than specified days"""
        cutoff = time.time() - (days_old * 24 * 3600)
        
        for cache_file in self.cache_dir.glob('*.json'):
            if cache_file.stat().st_mtime < cutoff:
                cache_file.unlink(missing_ok=True)

# Global cache instance
_global_cache = None

def get_query_cache() -> QueryCache:
    """Get the global query cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = QueryCache()
    return _global_cache
