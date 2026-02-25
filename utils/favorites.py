"""Favorites and Recently Watched manager for TV Viewer."""

import json
import os
import time
from utils.logger import get_logger

logger = get_logger(__name__)

FAVORITES_FILE = "favorites.json"
MAX_RECENT = 20


class FavoritesManager:
    """Manages favorite channels and recently watched history."""

    __slots__ = ('_favorites', '_recent', '_filepath')

    def __init__(self, filepath=None):
        self._filepath = filepath or FAVORITES_FILE
        self._favorites = set()  # Set of channel URLs
        self._recent = []  # List of {url, name, timestamp}
        self._load()

    def _load(self):
        """Load favorites from disk."""
        try:
            if os.path.exists(self._filepath):
                with open(self._filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._favorites = set(data.get('favorites', []))
                self._recent = data.get('recent', [])[:MAX_RECENT]
                logger.info(f"Loaded {len(self._favorites)} favorites, {len(self._recent)} recent")
        except Exception as e:
            logger.error(f"Failed to load favorites: {e}")
            self._favorites = set()
            self._recent = []

    def _save(self):
        """Save favorites to disk."""
        try:
            data = {
                'favorites': list(self._favorites),
                'recent': self._recent[:MAX_RECENT]
            }
            with open(self._filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save favorites: {e}")

    def is_favorite(self, url):
        """Check if a channel URL is favorited."""
        return url in self._favorites

    def toggle_favorite(self, url):
        """Toggle favorite status. Returns new state."""
        if url in self._favorites:
            self._favorites.discard(url)
            state = False
        else:
            self._favorites.add(url)
            state = True
        self._save()
        return state

    def add_favorite(self, url):
        """Add a channel to favorites."""
        self._favorites.add(url)
        self._save()

    def remove_favorite(self, url):
        """Remove a channel from favorites."""
        self._favorites.discard(url)
        self._save()

    def get_favorites(self):
        """Return set of favorite channel URLs."""
        return self._favorites.copy()

    def get_favorite_count(self):
        """Return number of favorites."""
        return len(self._favorites)

    def add_to_recent(self, url, name):
        """Record a channel as recently watched."""
        entry = {'url': url, 'name': name, 'timestamp': time.time()}
        # Remove existing entry for same URL
        self._recent = [r for r in self._recent if r.get('url') != url]
        # Add to front
        self._recent.insert(0, entry)
        # Trim
        self._recent = self._recent[:MAX_RECENT]
        self._save()

    def get_recent(self, limit=10):
        """Return recently watched channels."""
        return self._recent[:limit]

    def clear_recent(self):
        """Clear recently watched history."""
        self._recent = []
        self._save()
