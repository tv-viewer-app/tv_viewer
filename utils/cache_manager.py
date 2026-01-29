"""Cache manager - simple stub as file doesn't exist in repo."""

class CacheManager:
    """Simple cache manager stub."""
    def __init__(self, cache_file="channels.json"):
        self.cache_file = cache_file
        self.cache = {}
    
    def load(self):
        """Load cache."""
        import json
        import os
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file) as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
    
    def save(self):
        """Save cache."""
        import json
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except:
            pass
    
    def get(self, key, default=None):
        """Get from cache."""
        return self.cache.get(key, default)
    
    def set(self, key, value):
        """Set in cache."""
        self.cache[key] = value
