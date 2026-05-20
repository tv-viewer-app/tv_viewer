"""TV Viewer Web Server — FastAPI backend for the web interface.

Can run standalone (Docker / CLI) or embedded within the Windows desktop app.

Usage:
    Standalone:  python -m web.server
    Docker:      docker run -p 8765:8765 tv-viewer-web
"""

import os
import sys
import json
import asyncio
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="TV Viewer Web",
    version=config.APP_VERSION,
    description="Browser-based IPTV streaming interface"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _load_channels() -> List[Dict[str, Any]]:
    """Load channels from the cache file."""
    channels_file = PROJECT_ROOT / config.CHANNELS_FILE
    try:
        with open(channels_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("channels", [])
    except Exception as e:
        logger.warning(f"Failed to load channels: {e}")
        return []


def _load_favorites() -> set:
    """Load favorite URLs."""
    fav_file = PROJECT_ROOT / "favorites.json"
    try:
        with open(fav_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("urls", []))
    except Exception:
        return set()


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main web UI."""
    index_file = STATIC_DIR / "index.html"
    return FileResponse(str(index_file), media_type="text/html")


@app.get("/api/channels")
async def get_channels(
    category: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    favorites_only: bool = Query(False),
):
    """Get channels with optional filtering."""
    channels = _load_channels()
    favorites = _load_favorites() if favorites_only else set()

    if favorites_only:
        channels = [c for c in channels if c.get("url") in favorites]
    if category:
        channels = [c for c in channels if c.get("category", "").lower() == category.lower()]
    if country:
        channels = [c for c in channels if c.get("country", "").lower() == country.lower()]
    if search:
        q = search.lower()
        channels = [c for c in channels if q in c.get("name", "").lower()
                    or q in c.get("category", "").lower()
                    or q in c.get("country", "").lower()]

    # Only return working channels by default, plus unchecked
    channels = [c for c in channels if c.get("status") != "offline"]

    return {
        "channels": channels,
        "total": len(channels),
    }


@app.get("/api/categories")
async def get_categories():
    """Get all categories with channel counts."""
    channels = _load_channels()
    cats: Dict[str, int] = {}
    for ch in channels:
        if ch.get("status") == "offline":
            continue
        cat = ch.get("category", "General")
        cats[cat] = cats.get(cat, 0) + 1
    sorted_cats = sorted(cats.items(), key=lambda x: -x[1])
    return {"categories": [{"name": k, "count": v} for k, v in sorted_cats]}


@app.get("/api/countries")
async def get_countries():
    """Get all countries with channel counts."""
    channels = _load_channels()
    countries: Dict[str, int] = {}
    for ch in channels:
        if ch.get("status") == "offline":
            continue
        country = ch.get("country", "Unknown")
        countries[country] = countries.get(country, 0) + 1
    sorted_countries = sorted(countries.items(), key=lambda x: -x[1])
    return {"countries": [{"name": k, "count": v} for k, v in sorted_countries]}


@app.get("/api/status")
async def get_status():
    """Server status and version info."""
    channels = _load_channels()
    working = sum(1 for c in channels if c.get("status") == "working")
    return {
        "version": config.APP_VERSION,
        "app_name": config.APP_NAME,
        "total_channels": len(channels),
        "working_channels": working,
        "status": "running",
    }


# ─── Embedded server control (used by Windows app) ───────────────────────────

_server_thread: Optional[threading.Thread] = None
_server_instance: Optional[uvicorn.Server] = None

WEB_PORT = int(os.environ.get("TV_VIEWER_WEB_PORT", "8765"))


def start_server(port: int = WEB_PORT) -> bool:
    """Start the web server in a background thread. Returns True if started."""
    global _server_thread, _server_instance

    if _server_thread and _server_thread.is_alive():
        logger.info("Web server already running")
        return True

    config_uvi = uvicorn.Config(
        app, host="0.0.0.0", port=port,
        log_level="warning", access_log=False
    )
    _server_instance = uvicorn.Server(config_uvi)

    def _run():
        asyncio.run(_server_instance.serve())

    _server_thread = threading.Thread(target=_run, daemon=True, name="WebServer")
    _server_thread.start()
    logger.info(f"Web server started on http://0.0.0.0:{port}")
    return True


def stop_server():
    """Stop the embedded web server."""
    global _server_instance, _server_thread
    if _server_instance:
        _server_instance.should_exit = True
        logger.info("Web server stopping...")
        _server_instance = None
        _server_thread = None


def is_running() -> bool:
    """Check if the web server is currently running."""
    return _server_thread is not None and _server_thread.is_alive()


# ─── Standalone entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TV Viewer Web Server")
    parser.add_argument("--port", type=int, default=WEB_PORT, help="Port (default 8765)")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default 0.0.0.0)")
    args = parser.parse_args()

    print(f"\n📺 TV Viewer Web v{config.APP_VERSION}")
    print(f"   Serving on http://{args.host}:{args.port}\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
