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
import ipaddress
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
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

# Global refresh state (used by /api/status and /api/refresh)
_refresh_in_progress = False

# ─── Country code normalization (merge "AE" with "United Arab Emirates" etc.) ─

_COUNTRY_CODES = {
    "AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan",
    "AL": "Albania", "AM": "Armenia", "AO": "Angola", "AR": "Argentina",
    "AT": "Austria", "AU": "Australia", "AZ": "Azerbaijan", "BA": "Bosnia",
    "BD": "Bangladesh", "BE": "Belgium", "BG": "Bulgaria", "BH": "Bahrain",
    "BO": "Bolivia", "BR": "Brazil", "BY": "Belarus", "CA": "Canada",
    "CH": "Switzerland", "CL": "Chile", "CN": "China", "CO": "Colombia",
    "CR": "Costa Rica", "CU": "Cuba", "CY": "Cyprus", "CZ": "Czech Republic",
    "DE": "Germany", "DK": "Denmark", "DO": "Dominican Republic",
    "DZ": "Algeria", "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt",
    "ES": "Spain", "FI": "Finland", "FR": "France", "GB": "United Kingdom",
    "GE": "Georgia", "GH": "Ghana", "GR": "Greece", "GT": "Guatemala",
    "HK": "Hong Kong", "HN": "Honduras", "HR": "Croatia", "HU": "Hungary",
    "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IN": "India",
    "IQ": "Iraq", "IR": "Iran", "IS": "Iceland", "IT": "Italy",
    "JM": "Jamaica", "JO": "Jordan", "JP": "Japan", "KE": "Kenya",
    "KR": "South Korea", "KW": "Kuwait", "KZ": "Kazakhstan", "LB": "Lebanon",
    "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia", "LY": "Libya",
    "MA": "Morocco", "MD": "Moldova", "ME": "Montenegro", "MK": "North Macedonia",
    "MM": "Myanmar", "MN": "Mongolia", "MX": "Mexico", "MY": "Malaysia",
    "NG": "Nigeria", "NL": "Netherlands", "NO": "Norway", "NZ": "New Zealand",
    "OM": "Oman", "PA": "Panama", "PE": "Peru", "PH": "Philippines",
    "PK": "Pakistan", "PL": "Poland", "PR": "Puerto Rico", "PS": "Palestine",
    "PT": "Portugal", "PY": "Paraguay", "QA": "Qatar", "RO": "Romania",
    "RS": "Serbia", "RU": "Russia", "SA": "Saudi Arabia", "SD": "Sudan",
    "SE": "Sweden", "SG": "Singapore", "SI": "Slovenia", "SK": "Slovakia",
    "SN": "Senegal", "SO": "Somalia", "SY": "Syria", "TH": "Thailand",
    "TN": "Tunisia", "TR": "Turkey", "TT": "Trinidad", "TW": "Taiwan",
    "UA": "Ukraine", "UK": "United Kingdom", "US": "USA", "UY": "Uruguay",
    "UZ": "Uzbekistan", "VE": "Venezuela", "VN": "Vietnam", "ZA": "South Africa",
}


def _normalize_country(raw: str) -> str:
    """Normalize country codes (2-letter) to full names, merge duplicates."""
    if not raw or raw == "Unknown":
        return "Unknown"
    upper = raw.strip().upper()
    if upper in _COUNTRY_CODES:
        return _COUNTRY_CODES[upper]
    return raw.strip()


# Detect local country for "LOCAL" category — env var override or system locale
def _detect_local_country() -> str:
    env = os.environ.get("LOCAL_COUNTRY", "").strip()
    if env:
        upper = env.upper()
        return _COUNTRY_CODES.get(upper, env)
    try:
        import locale
        loc = locale.getlocale()
        if loc and loc[0] and '_' in loc[0]:
            code = loc[0].split('_')[1].upper()
            return _COUNTRY_CODES.get(code, code)
    except Exception:
        pass
    return "Israel"  # Default for this deployment


_LOCAL_COUNTRY = _detect_local_country()


def _deduplicate_channels(channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge channels with the same normalized name into single entries with multiple URLs.

    E.g., 3 separate "Fox Weather" entries become 1 entry with urls=[url1, url2, url3].
    Prefers 'working' status over 'unchecked' over 'offline'.
    """
    import re
    merged: Dict[str, Dict[str, Any]] = {}
    STATUS_PRIORITY = {'working': 0, 'unchecked': 1, 'offline': 2}

    for ch in channels:
        name = (ch.get("name") or "").strip()
        if not name:
            continue
        # Normalize key: lowercase, strip quality tags like (1080p), [Geo-blocked]
        key = re.sub(r'\s*[\(\[][^\)\]]*[\)\]]', '', name).strip().lower()
        url = ch.get("url", "")
        urls = ch.get("urls") or ([url] if url else [])

        if key in merged:
            existing = merged[key]
            # Add new URLs that aren't already present
            for u in urls:
                if u and u not in existing["urls"]:
                    existing["urls"].append(u)
            # Prefer better status
            new_priority = STATUS_PRIORITY.get(ch.get("status", "unchecked"), 1)
            old_priority = STATUS_PRIORITY.get(existing.get("status", "unchecked"), 1)
            if new_priority < old_priority:
                existing["status"] = ch.get("status", "unchecked")
            # Prefer entry with logo/category if current doesn't have one
            if not existing.get("logo") and ch.get("logo"):
                existing["logo"] = ch["logo"]
            if existing.get("category") in (None, "Other", "General") and ch.get("category") not in (None, "Other", "General"):
                existing["category"] = ch["category"]
        else:
            merged[key] = {
                "name": name,
                "url": urls[0] if urls else url,
                "urls": list(urls),
                "category": ch.get("category", "General"),
                "country": ch.get("country", "Unknown"),
                "logo": ch.get("logo", ""),
                "media_type": ch.get("media_type"),
                "status": ch.get("status", "unchecked"),
                "source": ch.get("source", ""),
                "working_url_index": 0,
            }

    return list(merged.values())


# ─── In-memory channel cache (avoids repeated disk reads) ────────────────────

class _ChannelCache:
    """Lazy-loading channel cache — reads JSON once, serves from RAM.
    Pre-sorts channels (IL first, then alphabetical) on load to avoid per-request sorting."""
    __slots__ = ('_channels', '_sorted', '_mtime', '_path', '_categories', '_countries',
                 '_favorites', '_fav_mtime')

    def __init__(self):
        self._channels = None
        self._sorted = None
        self._mtime = 0
        self._path = DATA_DIR / "channels.json"
        self._categories = None
        self._countries = None
        self._favorites = None
        self._fav_mtime = 0

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
                raw_channels = data.get("channels", [])
                # Normalize country codes to full names
                for ch in raw_channels:
                    ch["country"] = _normalize_country(ch.get("country") or "Unknown")
                # Deduplicate: merge channels with same normalized name
                self._channels = _deduplicate_channels(raw_channels)
                # Pre-sort once on load: Israeli first, then alphabetical
                self._sorted = sorted(self._channels,
                    key=lambda ch: (
                        0 if (ch.get("country") or "").lower() == "israel" else 1,
                        (ch.get("name") or "").lower()
                    ))
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
    def sorted_channels(self) -> List[Dict[str, Any]]:
        """Pre-sorted channels (IL first, then A-Z). No per-request sort needed."""
        self._check_reload()
        return self._sorted or []

    @property
    def categories(self) -> List[Dict[str, Any]]:
        if self._categories is None:
            cats: Dict[str, int] = {}
            # Country names that shouldn't appear as categories — use actual country set
            country_names = set(v.lower() for v in _COUNTRY_CODES.values())
            country_names.update(k.lower() for k in _COUNTRY_CODES.keys())
            # Also collect actual country values from loaded channels
            actual_countries = set()
            local_count = 0
            for ch in self.channels:
                c = ch.get("country")
                if c:
                    actual_countries.add(c.lower())
                # Count LOCAL channels (same country as server)
                if ch.get("status") != "offline" and (c or "").lower() == _LOCAL_COUNTRY.lower():
                    local_count += 1
            country_names.update(actual_countries)

            for ch in self.channels:
                if ch.get("status") == "offline":
                    continue
                cat = ch.get("category") or "General"
                # Skip dirty data: country names mistakenly in category field
                if cat.lower() in country_names or (len(cat) == 2 and cat.upper() == cat):
                    cat = "General"
                cats[cat] = cats.get(cat, 0) + 1

            # Build final list with LOCAL pinned first
            result = []
            if local_count > 0:
                result.append({"name": "LOCAL", "count": local_count})
            result.extend({"name": k, "count": v} for k, v in sorted(cats.items(), key=lambda x: -x[1]))
            self._categories = result
        return self._categories

    @property
    def countries(self) -> List[Dict[str, Any]]:
        if self._countries is None:
            ctrs: Dict[str, int] = {}
            for ch in self.channels:
                if ch.get("status") == "offline":
                    continue
                country = _normalize_country(ch.get("country") or "Unknown")
                ctrs[country] = ctrs.get(country, 0) + 1
            self._countries = [{"name": k, "count": v} for k, v in sorted(ctrs.items(), key=lambda x: -x[1])]
        return self._countries

    @property
    def favorites(self) -> set:
        """Cached favorites — reloads from disk only when file changes."""
        fav_file = DATA_DIR / "favorites.json"
        try:
            mt = fav_file.stat().st_mtime
        except OSError:
            return self._favorites or set()
        if mt != self._fav_mtime or self._favorites is None:
            try:
                with open(fav_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._favorites = set(data.get("urls", []))
                self._fav_mtime = mt
            except Exception:
                self._favorites = self._favorites or set()
        return self._favorites

    def invalidate(self):
        """Force reload on next access."""
        self._mtime = 0
        self._sorted = None
        self._categories = None
        self._countries = None


_cache = _ChannelCache()

app = FastAPI(
    title="TV Viewer Web",
    version=config.APP_VERSION,
    description="Browser-based IPTV streaming interface"
)

# GZip responses > 500 bytes — critical for constrained networks (saves 70-80% bandwidth)
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Security Headers Middleware ──────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Skip security headers for proxied streams (breaks video playback)
        if not request.url.path.startswith("/api/proxy"):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), payment=()"
            )
        return response

app.add_middleware(SecurityHeadersMiddleware)


# ─── SSRF Protection ─────────────────────────────────────────────────────────

_BLOCKED_IP_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
]

def _is_private_ip(hostname: str) -> bool:
    """Check if a hostname resolves to a private/loopback IP (with DNS resolution)."""
    import socket
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return True
        return any(ip in net for net in _BLOCKED_IP_RANGES)
    except ValueError:
        # Hostname — resolve DNS and check all resolved IPs
        lower = hostname.lower()
        if lower in ('localhost', '0.0.0.0') or lower.endswith('.local'):
            return True
        try:
            for info in socket.getaddrinfo(hostname, None, socket.AF_UNSPEC):
                resolved_ip = ipaddress.ip_address(info[4][0])
                if resolved_ip.is_private or resolved_ip.is_loopback or resolved_ip.is_link_local:
                    return True
                if any(resolved_ip in net for net in _BLOCKED_IP_RANGES):
                    return True
        except (socket.gaierror, ValueError, OSError):
            pass
        return False


def _validate_proxy_url(url: str) -> None:
    """Validate proxy URL against SSRF and abuse. Raises HTTPException."""
    parsed = urlparse(url)

    # Must be http/https
    if parsed.scheme not in ('http', 'https'):
        raise HTTPException(400, "Only HTTP/HTTPS URLs are allowed")

    # Block private IPs
    if parsed.hostname and _is_private_ip(parsed.hostname):
        raise HTTPException(403, "Access to internal network addresses is forbidden")

    # Block non-standard ports (allow common streaming ports)
    if parsed.port and parsed.port not in (80, 443, 8080, 8443, 1935, 554):
        raise HTTPException(403, "Non-standard port not allowed for proxy")

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _load_channels() -> List[Dict[str, Any]]:
    """Load channels from cache (memory-first, disk-fallback)."""
    return _cache.channels


def _load_favorites() -> set:
    """Load favorite URLs from cache (memory, reloads when file changes)."""
    return _cache.favorites


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main web UI."""
    index_file = STATIC_DIR / "index.html"
    return FileResponse(str(index_file), media_type="text/html")


@app.get("/api/channels")
async def get_channels(
    category: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    media_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    favorites_only: bool = Query(False),
    show_all: bool = Query(False),
    limit: int = Query(200, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    """Get channels with optional filtering. Local (IL) channels shown first."""
    # Use pre-sorted list (IL first, A-Z) — no per-request sort needed
    channels = _cache.sorted_channels
    favorites = _load_favorites() if favorites_only else set()

    if favorites_only:
        channels = [c for c in channels if c.get("url") in favorites]
    if category:
        if category.upper() == "LOCAL":
            # LOCAL = channels from user's detected country
            channels = [c for c in channels if (c.get("country") or "").lower() == _LOCAL_COUNTRY.lower()]
        else:
            channels = [c for c in channels if (c.get("category") or "").lower() == category.lower()]
    if country:
        channels = [c for c in channels if (c.get("country") or "").lower() == country.lower()]
    if media_type:
        if media_type == "Radio":
            channels = [c for c in channels if (c.get("media_type") or "") == "Radio"
                        or "radio" in (c.get("category") or "").lower()]
        else:
            channels = [c for c in channels if (c.get("media_type") or "TV") == media_type
                        and "radio" not in (c.get("category") or "").lower()]
    if search:
        q = search.lower()
        channels = [c for c in channels if q in (c.get("name") or "").lower()
                    or q in (c.get("category") or "").lower()
                    or q in (c.get("country") or "").lower()]

    # Hide offline (failed) channels by default; show_all=true includes them
    if not show_all:
        channels = [c for c in channels if c.get("status") != "offline"]

    total = len(channels)
    channels = channels[offset:offset + limit]

    # Strip heavy fields to reduce payload (logo URLs alone can add 30% to response size)
    slim = []
    for ch in channels:
        slim.append({
            "name": ch.get("name"),
            "url": ch.get("url"),
            "urls": ch.get("urls"),
            "category": ch.get("category"),
            "country": ch.get("country"),
            "logo": ch.get("logo"),
            "status": ch.get("status"),
            "media_type": ch.get("media_type"),
        })

    return {
        "channels": slim,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total,
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
        "refresh_in_progress": _refresh_in_progress,
    }


# ─── Stream Proxy (CORS bypass) ─────────────────────────────────────────────

import aiohttp
import re
from urllib.parse import urljoin, quote

# Proxy timeout for upstream connections
_proxy_timeout = aiohttp.ClientTimeout(total=60, sock_read=30)
# Shared connector pool — avoids creating per-request connectors (fixes session leak)
_proxy_connector: Optional[aiohttp.TCPConnector] = None


def _get_proxy_connector() -> aiohttp.TCPConnector:
    global _proxy_connector
    if _proxy_connector is None or _proxy_connector.closed:
        _proxy_connector = aiohttp.TCPConnector(limit=50, ttl_dns_cache=300)
    return _proxy_connector


@app.get("/api/proxy")
async def proxy_stream(request: Request, url: str = Query(..., description="Stream URL to proxy")):
    """Proxy an HLS stream to bypass CORS restrictions.
    Rewrites .m3u8 manifests so segment URLs also go through the proxy."""
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # SSRF protection
    _validate_proxy_url(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Referer": url,
    }
    session = None
    try:
        session = aiohttp.ClientSession(
            timeout=_proxy_timeout,
            connector=_get_proxy_connector(),
            connector_owner=False  # Don't close shared connector when session closes
        )
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

        # For segments (.ts, .mp4, etc.) — stream through
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
    except (aiohttp.ClientError, asyncio.TimeoutError, asyncio.CancelledError, OSError) as e:
        if session and not session.closed:
            await session.close()
        return JSONResponse(
            status_code=502,
            content={"detail": f"Upstream connection failed: {type(e).__name__}"},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        if session and not session.closed:
            await session.close()
        logger.error(f"Proxy unexpected error: {e}")
        return JSONResponse(
            status_code=502,
            content={"detail": "Proxy error"},
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
    seen_urls = set()
    for ch in channels:
        if (ch.get("name") or "").lower() == channel_name.lower() and ch.get("status") != "offline":
            # Check urls array (multi-source channels from Supabase)
            urls = ch.get("urls") or []
            if urls:
                for u in urls:
                    if u and u not in seen_urls:
                        seen_urls.add(u)
                        sources.append({"url": u, "status": ch.get("status", "unchecked")})
            # Also add the primary url if not already included
            primary = ch.get("url")
            if primary and primary not in seen_urls:
                seen_urls.add(primary)
                sources.append({"url": primary, "status": ch.get("status", "unchecked")})
    return {"channel": channel_name, "sources": sources}


@app.get("/api/epg/{channel_name}")
async def get_epg(channel_name: str, hours: int = Query(6, ge=1, le=24)):
    """Get EPG schedule for a channel."""
    try:
        from utils.epg import epg_service
        # Initialize once (concurrent requests just wait for the first)
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


# ─── Analytics (anonymous usage telemetry to Supabase) ──────────────────────

_ANALYTICS_URL = f"{config.SUPABASE_URL}/rest/v1/analytics_events" if config.SUPABASE_URL else ""
_ANALYTICS_HEADERS = {
    "apikey": config.SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {config.SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
} if config.SUPABASE_ANON_KEY else {}


@app.post("/api/analytics")
async def track_analytics(request: Request):
    """Accept analytics events from web clients and forward to Supabase.

    Expected body: {event_type, device_id, event_data?, platform?, app_version?}
    Fire-and-forget — never blocks client, always returns 200.
    """
    try:
        body = await request.json()
        event_type = body.get("event_type", "")
        device_id = body.get("device_id", "")
        if not event_type or not device_id or len(event_type) > 100:
            return {"status": "ignored"}

        # Sanitize — only allow expected fields, cap sizes
        payload = {
            "event_type": event_type[:100],
            "device_id": device_id[:64],
            "event_data": body.get("event_data", {}) if isinstance(body.get("event_data"), dict) else {},
            "app_version": str(body.get("app_version", config.APP_VERSION))[:20],
            "platform": str(body.get("platform", "web"))[:30],
        }
        # Cap event_data size
        import json as _json
        if len(_json.dumps(payload["event_data"])) > 5000:
            payload["event_data"] = {"error": "payload_too_large"}

        # Forward to Supabase (fire-and-forget)
        if _ANALYTICS_URL and _ANALYTICS_HEADERS:
            try:
                connector = aiohttp.TCPConnector(limit=5, ttl_dns_cache=300)
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    async with session.post(_ANALYTICS_URL, json=payload, headers=_ANALYTICS_HEADERS, ssl=False) as resp:
                        if resp.status not in (200, 201):
                            logger.debug(f"Analytics forward: {resp.status}")
            except Exception as e:
                logger.debug(f"Analytics forward failed: {e}")

        return {"status": "ok"}
    except Exception:
        return {"status": "error"}


# ─── Refresh / pull channels ────────────────────────────────────────────────

_refresh_lock = threading.Lock()


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
        # Start fetch in background thread so server starts immediately
        def _startup_fetch():
            global _refresh_in_progress
            _refresh_in_progress = True
            import asyncio as _aio
            print("   ⏳ Fetching channels in background...")

            try:
                # Strategy 1: Try Supabase first (fast, ~5s)
                try:
                    from utils.supabase_channels import fetch_channels, is_configured
                    if is_configured():
                        print("   📡 Trying Supabase (fast)...")
                        channels = _aio.run(fetch_channels())
                        if channels:
                            with open(channels_path, "w", encoding="utf-8") as f:
                                json.dump({"channels": channels}, f, ensure_ascii=False)
                            print(f"   ✅ Loaded {len(channels)} channels from Supabase\n")
                            return
                except Exception as e:
                    print(f"   ⚠️  Supabase failed: {e}")

                # Strategy 2: Fall back to M3U repositories (slow, ~60-120s)
                try:
                    print("   📡 Falling back to M3U repositories...")
                    from core.repository import RepositoryHandler
                    handler = RepositoryHandler()
                    channels = _aio.run(handler.fetch_all_repositories())
                    if channels:
                        with open(channels_path, "w", encoding="utf-8") as f:
                            json.dump({"channels": channels}, f, ensure_ascii=False)
                        print(f"   ✅ Loaded {len(channels)} channels from repositories\n")
                    else:
                        print("   ⚠️  No channels fetched — use /api/refresh later\n")
                except Exception as e:
                    print(f"   ⚠️  Repository fetch failed: {e}\n")
            finally:
                _refresh_in_progress = False

        import threading
        t = threading.Thread(target=_startup_fetch, daemon=True)
        t.start()
        print("   🚀 Server starting (channels loading in background)...\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
