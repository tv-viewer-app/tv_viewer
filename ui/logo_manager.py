"""Logo manager — fetches and caches channel logos asynchronously."""
import os
import threading
import urllib.request
import hashlib
from typing import Optional, Callable, Dict
from io import BytesIO

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import config
from utils.logger import get_logger

logger = get_logger(__name__)

LOGO_CACHE_DIR = os.path.join(
    getattr(config, 'CACHE_DIR', os.path.expanduser('~/.tv_viewer')),
    'logos'
)
try:
    os.makedirs(LOGO_CACHE_DIR, exist_ok=True)
except Exception:
    pass

LOGO_SIZE = (96, 96)  # display size


class LogoManager:
    """Fetches channel logos lazily, caches in memory and on disk."""

    def __init__(self):
        self._cache: Dict[str, 'ImageTk.PhotoImage'] = {}
        self._failed: set = set()
        self._loading: set = set()
        self._lock = threading.Lock()

    def get_logo(self, channel: dict, callback: Callable[[Optional['ImageTk.PhotoImage']], None]):
        """Get logo (cached or fetch). Calls callback on main thread when ready.

        Returns the cached PhotoImage immediately if available, otherwise None
        (and triggers asynchronous fetch which calls back later).
        """
        if not PIL_AVAILABLE:
            return None

        url = channel.get('logo', '') or ''
        if url in ('None', 'null', '', None):
            url = ''
        if not url or not url.startswith(('http://', 'https://')):
            return None

        with self._lock:
            if url in self._cache:
                return self._cache[url]
            if url in self._failed or url in self._loading:
                return None
            self._loading.add(url)

        # Check disk cache
        cache_file = self._cache_path(url)
        if os.path.exists(cache_file):
            try:
                img = self._load_image(cache_file)
                with self._lock:
                    self._cache[url] = img
                    self._loading.discard(url)
                callback(img)
                return img
            except Exception:
                pass

        thread = threading.Thread(
            target=self._fetch, args=(url, cache_file, callback), daemon=True
        )
        thread.start()
        return None

    def _cache_path(self, url: str) -> str:
        h = hashlib.sha1(url.encode('utf-8')).hexdigest()
        return os.path.join(LOGO_CACHE_DIR, f"{h}.png")

    def _fetch(self, url: str, cache_file: str, callback):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TVViewer/1.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
            if len(data) < 64 or len(data) > 2_000_000:
                raise ValueError("Invalid logo size")
            img_pil = Image.open(BytesIO(data)).convert('RGBA')
            img_pil.thumbnail(LOGO_SIZE, Image.LANCZOS)
            img_pil.save(cache_file, 'PNG')
            try:
                from tkinter import _default_root as _root
            except ImportError:
                _root = None
            if _root is not None:
                _root.after(0, lambda: self._on_loaded(url, cache_file, callback))
            else:
                self._on_loaded(url, cache_file, callback)
        except Exception as e:
            logger.debug(f"Logo fetch failed for {url}: {e}")
            with self._lock:
                self._failed.add(url)
                self._loading.discard(url)
            try:
                from tkinter import _default_root as _root
                if _root is not None:
                    _root.after(0, lambda: callback(None))
            except Exception:
                pass

    def _on_loaded(self, url: str, cache_file: str, callback):
        try:
            img = self._load_image(cache_file)
            with self._lock:
                self._cache[url] = img
                self._loading.discard(url)
            callback(img)
        except Exception:
            with self._lock:
                self._failed.add(url)
                self._loading.discard(url)
            callback(None)

    def _load_image(self, path: str) -> 'ImageTk.PhotoImage':
        from PIL import Image, ImageTk
        img_pil = Image.open(path).convert('RGBA')
        img_pil.thumbnail(LOGO_SIZE, Image.LANCZOS)
        return ImageTk.PhotoImage(img_pil)


_logo_mgr: Optional[LogoManager] = None


def get_logo_manager() -> LogoManager:
    global _logo_mgr
    if _logo_mgr is None:
        _logo_mgr = LogoManager()
    return _logo_mgr
