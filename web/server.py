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
import hashlib
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from utils.logger import get_logger

logger = get_logger(__name__)

# Persistent data directory — defaults to project root, override with DATA_DIR env var.
# In Docker, DATA_DIR=/data (a volume) so favorites/channels survive container upgrades.
DATA_DIR = Path(os.environ.get("DATA_DIR", str(PROJECT_ROOT)))

# ─── In-memory channel cache (avoids repeated disk reads) ────────────────────

class _ChannelCache:
    """Lazy-loading channel cache — reads JSON once, serves from RAM."""
    __slots__ = ('_channels', '_mtime', '_path', '_categories', '_countries')

    def __init__(self):
        self._channels = None
        self._mtime = 0
        self._path = DATA_DIR / "channels.json"
        self._categories = None
        self._countries = None

    def _check_reload(self):
        """Reload only if file changed (stat is cheap, JSON parse is not)."""
        try:
            mt = self._path.stat().st_mtime
        except OSError:
            return
        if mt != self._mtime:
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._channels = data.get("channels", [])
                self._mtime = mt
                self._categories = None
                self._countries = None
            except (json.JSONDecodeError, OSError):
                pass  # File being written — keep stale data

    @property
    def channels(self) -> List[Dict[str, Any]]:
        self._check_reload()
        return self._channels or []

    @property
    def categories(self) -> List[Dict[str, Any]]:
        if self._categories is None:
            cats: Dict[str, int] = {}
            for ch in self.channels:
                if ch.get("status") == "offline":
                    continue
                cat = ch.get("category", "General")
                cats[cat] = cats.get(cat, 0) + 1
            self._categories = [{"name": k, "count": v} for k, v in sorted(cats.items(), key=lambda x: -x[1])]
        return self._categories

    @property
    def countries(self) -> List[Dict[str, Any]]:
        if self._countries is None:
            ctrs: Dict[str, int] = {}
            for ch in self.channels:
                if ch.get("status") == "offline":
                    continue
                country = ch.get("country", "Unknown")
                ctrs[country] = ctrs.get(country, 0) + 1
            self._countries = [{"name": k, "count": v} for k, v in sorted(ctrs.items(), key=lambda x: -x[1])]
        return self._countries

    def invalidate(self):
        """Force reload on next access."""
        self._mtime = 0
        self._categories = None
        self._countries = None


_cache = _ChannelCache()

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
    """Load channels from cache (memory-first, disk-fallback)."""
    return _cache.channels


def _load_favorites() -> set:
    """Load favorite URLs."""
    fav_file = DATA_DIR / "favorites.json"
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
    return {"categories": _cache.categories}


@app.get("/api/countries")
async def get_countries():
    """Get all countries with channel counts."""
    return {"countries": _cache.countries}


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


# ─── Stream Proxy (CORS bypass) ─────────────────────────────────────────────

import aiohttp
import re
from urllib.parse import urljoin, quote

@app.get("/api/proxy")
async def proxy_stream(request: Request, url: str = Query(..., description="Stream URL to proxy")):
    """Proxy an HLS stream to bypass CORS restrictions.
    Rewrites .m3u8 manifests so segment URLs also go through the proxy."""
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    timeout = aiohttp.ClientTimeout(total=60, sock_read=30)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Referer": url,
    }
    try:
        session = aiohttp.ClientSession(timeout=timeout)
        resp = await session.get(url, headers=headers, ssl=False)

        if resp.status != 200:
            status = resp.status
            await resp.release()
            await session.close()
            return JSONResponse(
                status_code=status,
                content={"detail": f"Upstream returned {status}"},
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # For m3u8 manifests, rewrite URLs to go through proxy
        if ".m3u8" in url or "mpegurl" in (resp.headers.get("content-type", "").lower()):
            body = await resp.text()
            await resp.release()
            await session.close()
            rewritten = _rewrite_manifest(body, url, str(request.base_url))
            return StreamingResponse(
                iter([rewritten.encode()]),
                media_type="application/vnd.apple.mpegurl",
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"}
            )

        # For segments (.ts, .mp4, etc.) — stream and close when done
        media_type = resp.headers.get("content-type", "video/mp2t")

        async def stream_generator():
            try:
                async for chunk in resp.content.iter_chunked(65536):
                    yield chunk
            finally:
                await resp.release()
                await session.close()

        return StreamingResponse(
            stream_generator(),
            media_type=media_type,
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"}
        )
    except aiohttp.ClientError as e:
        return JSONResponse(
            status_code=502,
            content={"detail": f"Upstream connection failed: {str(e)}"},
            headers={"Access-Control-Allow-Origin": "*"}
        )


def _rewrite_manifest(manifest: str, manifest_url: str, base_url: str) -> str:
    """Rewrite URLs in HLS manifest to route through our proxy."""
    lines = manifest.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            # This is a URL line — make it absolute then wrap in proxy
            if stripped.startswith(('http://', 'https://')):
                abs_url = stripped
            else:
                abs_url = urljoin(manifest_url, stripped)
            result.append(f"{base_url}api/proxy?url={quote(abs_url, safe='')}")
        elif stripped.startswith('#EXT-X-MAP:URI="') or 'URI="' in stripped:
            # Rewrite URI= attributes in tags
            def rewrite_uri(m):
                uri = m.group(1)
                if not uri.startswith(('http://', 'https://')):
                    uri = urljoin(manifest_url, uri)
                return f'URI="{base_url}api/proxy?url={quote(uri, safe="")}"'
            result.append(re.sub(r'URI="([^"]+)"', rewrite_uri, stripped))
        else:
            result.append(line)
    return '\n'.join(result)


# ─── EPG endpoints ──────────────────────────────────────────────────────────

@app.get("/api/sources/{channel_name}")
async def get_sources(channel_name: str):
    """Get all alternative stream URLs for a channel by name."""
    channels = _load_channels()
    sources = []
    for ch in channels:
        if ch.get("name", "").lower() == channel_name.lower() and ch.get("status") != "offline":
            sources.append({"url": ch["url"], "status": ch.get("status", "unchecked")})
    return {"channel": channel_name, "sources": sources}


@app.get("/api/epg/{channel_name}")
async def get_epg(channel_name: str, hours: int = Query(6, ge=1, le=24)):
    """Get EPG schedule for a channel."""
    try:
        from utils.epg import epg_service
        # Try to initialize if not already done
        if not epg_service._initialized:
            try:
                await epg_service.initialize()
            except Exception:
                pass

        now_prog, next_prog = epg_service.get_now_next(channel_name=channel_name)
        schedule = epg_service.get_schedule(channel_name=channel_name, hours=hours)

        return {
            "channel": channel_name,
            "now": now_prog.to_dict() if now_prog else None,
            "next": next_prog.to_dict() if next_prog else None,
            "schedule": [p.to_dict() for p in schedule],
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="EPG service unavailable")
    except Exception as e:
        logger.warning(f"EPG error for {channel_name}: {e}")
        return {"channel": channel_name, "now": None, "next": None, "schedule": []}


# ─── Report broken channel ──────────────────────────────────────────────────

class ReportRequest(BaseModel):
    url: str
    name: Optional[str] = None
    reason: Optional[str] = None


@app.post("/api/report")
async def report_broken(report: ReportRequest):
    """Report a channel as broken — increments report_count in Supabase."""
    url_hash = hashlib.sha256(report.url.encode()).hexdigest()
    try:
        from utils import supabase_channels
        if not supabase_channels.is_configured():
            # Fall back to local marking
            _mark_local_broken(report.url)
            return {"status": "recorded_locally", "url_hash": url_hash}

        success = await supabase_channels.report_channel(url_hash)
        if success:
            return {"status": "reported", "url_hash": url_hash}
        else:
            _mark_local_broken(report.url)
            return {"status": "recorded_locally", "url_hash": url_hash}
    except ImportError:
        _mark_local_broken(report.url)
        return {"status": "recorded_locally", "url_hash": url_hash}
    except Exception as e:
        logger.warning(f"Report error: {e}")
        _mark_local_broken(report.url)
        return {"status": "recorded_locally", "url_hash": url_hash}


def _mark_local_broken(url: str):
    """Mark a channel as broken — update memory cache, write-through to disk."""
    for ch in _cache.channels:
        if ch.get("url") == url:
            ch["status"] = "offline"
            _cache._categories = None
            _cache._countries = None
            break
    _persist_channels()


# ─── Health reporting (client-side playback results) ────────────────────────

@app.post("/api/health/report")
async def health_report(request: Request):
    """Report channel playback health from client. Accepts {url, status}."""
    try:
        body = await request.json()
        url = body.get("url", "")
        status = body.get("status", "")
        if not url or status not in ("working", "broken"):
            return {"status": "ignored"}

        if status == "working":
            _mark_local_working(url)
        else:
            _mark_local_broken(url)

        # Best-effort Supabase push
        try:
            from utils import supabase_channels
            if supabase_channels.is_configured():
                url_hash = hashlib.sha256(url.encode()).hexdigest()
                if status == "broken":
                    await supabase_channels.report_channel(url_hash)
        except Exception:
            pass

        return {"status": "recorded", "channel_status": status}
    except Exception as e:
        logger.debug(f"Health report error: {e}")
        return {"status": "error"}


def _mark_local_working(url: str):
    """Mark a channel as working — update memory cache, write-through to disk."""
    for ch in _cache.channels:
        if ch.get("url") == url:
            ch["status"] = "working"
            break
    # Don't persist every working report — too many disk writes on NAS
    # Disk will be written on next broken report or refresh


def _persist_channels():
    """Write current channel state to disk (debounced by callers)."""
    if not _cache.channels:
        return  # Never overwrite with empty data
    try:
        channels_file = DATA_DIR / "channels.json"
        with open(channels_file, "w", encoding="utf-8") as f:
            json.dump({"channels": _cache.channels}, f, ensure_ascii=False)
        _cache._mtime = channels_file.stat().st_mtime
    except Exception as e:
        logger.warning(f"Failed to persist channels: {e}")


# ─── Refresh / pull channels ────────────────────────────────────────────────

_refresh_lock = threading.Lock()
_refresh_in_progress = False


@app.post("/api/refresh")
async def refresh_channels():
    """Trigger a background channel refresh from repositories."""
    global _refresh_in_progress
    if _refresh_in_progress:
        return {"status": "already_in_progress"}

    def _do_refresh():
        global _refresh_in_progress
        _refresh_in_progress = True
        try:
            from core.channel_manager import ChannelManager
            mgr = ChannelManager()
            mgr.load_cached_channels()

            # Run async fetch in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from core.repository import RepositoryHandler
                handler = RepositoryHandler()
                channels = loop.run_until_complete(handler.fetch_all_repositories())
                if channels:
                    mgr.merge_channels(channels)
                    # Save to DATA_DIR so Docker volume persists it
                    channels_file = DATA_DIR / "channels.json"
                    with open(channels_file, "w", encoding="utf-8") as f:
                        json.dump({"channels": mgr.channels}, f, ensure_ascii=False)
                    _cache._channels = None  # Force reload
                    _cache._mtime = 0
                    logger.info(f"Refresh complete: {len(mgr.channels)} channels")
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
        finally:
            _refresh_in_progress = False

    with _refresh_lock:
        t = threading.Thread(target=_do_refresh, daemon=True)
        t.start()

    return {"status": "started"}


@app.get("/api/refresh/status")
async def refresh_status():
    """Check if a refresh is in progress."""
    return {"in_progress": _refresh_in_progress}


# ─── Favorites management ───────────────────────────────────────────────────

def _save_favorites(urls: set):
    """Save favorites to disk."""
    fav_file = DATA_DIR / "favorites.json"
    try:
        with open(fav_file, "w", encoding="utf-8") as f:
            json.dump({"urls": list(urls)}, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Failed to save favorites: {e}")


@app.get("/api/favorites")
async def get_favorites():
    """Get all favorite channel URLs."""
    favs = _load_favorites()
    return {"urls": list(favs)}


class FavoriteRequest(BaseModel):
    url: str


@app.post("/api/favorites/toggle")
async def toggle_favorite(req: FavoriteRequest):
    """Toggle a channel as favorite. Returns new state."""
    favs = _load_favorites()
    if req.url in favs:
        favs.discard(req.url)
        is_fav = False
    else:
        favs.add(req.url)
        is_fav = True
    _save_favorites(favs)
    return {"url": req.url, "is_favorite": is_fav}


# ─── Map data ───────────────────────────────────────────────────────────────

# Country coordinates for map visualization
COUNTRY_COORDS = {
    "Israel": [31.77, 35.22], "United States": [39.83, -98.58], "United Kingdom": [55.38, -3.44],
    "Germany": [51.17, 10.45], "France": [46.23, 2.21], "Spain": [40.46, -3.75],
    "Italy": [41.87, 12.57], "Brazil": [-14.24, -51.93], "Russia": [61.52, 105.32],
    "India": [20.59, 78.96], "Canada": [56.13, -106.35], "Australia": [-25.27, 133.78],
    "Japan": [36.20, 138.25], "China": [35.86, 104.20], "Turkey": [38.96, 35.24],
    "Saudi Arabia": [23.89, 45.08], "UAE": [23.42, 53.85], "Egypt": [26.82, 30.80],
    "South Korea": [35.91, 127.77], "Mexico": [23.63, -102.55], "Argentina": [-38.42, -63.62],
    "Netherlands": [52.13, 5.29], "Poland": [51.92, 19.15], "Portugal": [39.40, -8.22],
    "Sweden": [60.13, 18.64], "Norway": [60.47, 8.47], "Greece": [39.07, 21.82],
    "Romania": [45.94, 24.97], "Iran": [32.43, 53.69], "Iraq": [33.22, 43.68],
    "Pakistan": [30.38, 69.35], "Thailand": [15.87, 100.99], "Indonesia": [-0.79, 113.92],
    "Philippines": [12.88, 121.77], "Vietnam": [14.06, 108.28], "Colombia": [4.57, -74.30],
    "Chile": [-35.68, -71.54], "Morocco": [31.79, -7.09], "Algeria": [28.03, 1.66],
    "Nigeria": [9.08, 8.68], "South Africa": [-30.56, 22.94], "Kenya": [-0.02, 37.91],
    "Ukraine": [48.38, 31.17], "Czech Republic": [49.82, 15.47], "Hungary": [47.16, 19.50],
    "Belgium": [50.50, 4.47], "Switzerland": [46.82, 8.23], "Austria": [47.52, 14.55],
    "Denmark": [56.26, 9.50], "Finland": [61.92, 25.75], "Ireland": [53.14, -7.69],
}


@app.get("/api/map")
async def get_map_data():
    """Get channel counts by country with coordinates for map display."""
    channels = _load_channels()
    country_data: Dict[str, Dict[str, Any]] = {}

    for ch in channels:
        if ch.get("status") == "offline":
            continue
        country = ch.get("country", "Unknown")
        if country == "Unknown":
            continue
        if country not in country_data:
            coords = COUNTRY_COORDS.get(country)
            country_data[country] = {
                "name": country,
                "count": 0,
                "coords": coords,
                "categories": {},
            }
        country_data[country]["count"] += 1
        cat = ch.get("category", "General")
        country_data[country]["categories"][cat] = country_data[country]["categories"].get(cat, 0) + 1

    return {"countries": list(country_data.values())}


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

    # Auto-fetch channels on first run if DATA_DIR has empty channels.json
    channels_path = DATA_DIR / "channels.json"
    try:
        with open(channels_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        need_fetch = len(data.get("channels", [])) == 0
    except Exception:
        need_fetch = True

    if need_fetch:
        print("   ⏳ No channels found — fetching from repositories...")
        try:
            from core.repository import RepositoryHandler
            import asyncio as _aio
            handler = RepositoryHandler()
            channels = _aio.run(handler.fetch_all_repositories())
            if channels:
                with open(channels_path, "w", encoding="utf-8") as f:
                    json.dump({"channels": channels}, f, ensure_ascii=False)
                print(f"   ✅ Loaded {len(channels)} channels\n")
            else:
                print("   ⚠️  No channels fetched — will retry via /api/refresh\n")
        except Exception as e:
            print(f"   ⚠️  Fetch failed: {e} — will retry via /api/refresh\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
