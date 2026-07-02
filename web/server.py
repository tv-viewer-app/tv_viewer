"""TV Viewer Web Server — FastAPI backend for the web interface.

Can run standalone (Docker / CLI) or embedded within the Windows desktop app.

Usage:
    Standalone:  python -m web.server
    Docker:      docker run -p 8765:8765 tv-viewer-web
"""

import copy
import os
import sys
import json
import uuid
import asyncio
import inspect
import hashlib
import ipaddress
import re
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.background import BackgroundTask
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

from utils.normalize import (
    normalize_country as _normalize_country,
    COUNTRY_CODES as _COUNTRY_CODES,
)



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


# ─── Category normalization ───────────────────────────────────────────────────
# Use shared normalization module (single source of truth)
from utils.normalize import normalize_category as _normalize_category_impl, CANONICAL_CATEGORIES


def _normalize_category(cat: str, channel_name: str = None) -> str:
    """Normalize a category string to a clean standard name."""
    return _normalize_category_impl(cat, channel_name)



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
    Pre-sorts channels (IL first, then alphabetical) on load to avoid per-request sorting.
    Also pre-builds category/country indexes so /api/channels filtering is O(1)
    instead of O(n) per request."""
    __slots__ = ('_channels', '_sorted', '_mtime', '_path', '_categories', '_countries',
                 '_favorites', '_fav_mtime',
                 '_by_category', '_by_country', '_by_cat_country', '_local_channels')

    def __init__(self):
        self._channels = None
        self._sorted = None
        self._mtime = 0
        self._path = DATA_DIR / "channels.json"
        self._categories = None
        self._countries = None
        self._favorites = None
        self._fav_mtime = 0
        # O(1) lookup indexes (lowercased keys), built at load time
        self._by_category: Dict[str, List[Dict[str, Any]]] = {}
        self._by_country: Dict[str, List[Dict[str, Any]]] = {}
        self._by_cat_country: Dict[tuple, List[Dict[str, Any]]] = {}
        self._local_channels: List[Dict[str, Any]] = []

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
                # Normalize country codes and categories
                for ch in raw_channels:
                    ch["country"] = _normalize_country(ch.get("country") or "Unknown")
                    ch["category"] = _normalize_category(
                        ch.get("category") or "General",
                        ch.get("name")
                    )
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
                self._build_indexes()
            except (json.JSONDecodeError, OSError):
                pass  # File being written — keep stale data

    def _build_indexes(self):
        """Build O(1) lookup tables. Called once per file change."""
        by_cat: Dict[str, List[Dict[str, Any]]] = {}
        by_country: Dict[str, List[Dict[str, Any]]] = {}
        by_cat_country: Dict[tuple, List[Dict[str, Any]]] = {}
        local: List[Dict[str, Any]] = []
        local_lc = _LOCAL_COUNTRY.lower()
        for ch in (self._sorted or []):
            cat_lc = (ch.get("category") or "").lower()
            country_lc = (ch.get("country") or "").lower()
            if cat_lc:
                by_cat.setdefault(cat_lc, []).append(ch)
            if country_lc:
                by_country.setdefault(country_lc, []).append(ch)
            if cat_lc and country_lc:
                by_cat_country.setdefault((cat_lc, country_lc), []).append(ch)
            if country_lc == local_lc:
                local.append(ch)
        self._by_category = by_cat
        self._by_country = by_country
        self._by_cat_country = by_cat_country
        self._local_channels = local

    @property
    def by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        self._check_reload()
        return self._by_category

    @property
    def by_country(self) -> Dict[str, List[Dict[str, Any]]]:
        self._check_reload()
        return self._by_country

    @property
    def by_cat_country(self) -> Dict[tuple, List[Dict[str, Any]]]:
        self._check_reload()
        return self._by_cat_country

    @property
    def local_channels(self) -> List[Dict[str, Any]]:
        self._check_reload()
        return self._local_channels

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
        self._by_category = {}
        self._by_country = {}
        self._by_cat_country = {}
        self._local_channels = []


_cache = _ChannelCache()


def _parse_version_string(version_str: str) -> tuple[int, int, int]:
    """Parse a version string like 'v2.21.3' into a comparable tuple."""
    parts = str(version_str or "").lstrip("v").split(".")
    parsed: List[int] = []
    for part in parts[:3]:
        try:
            parsed.append(int(part.split("-")[0]))
        except (TypeError, ValueError):
            parsed.append(0)
    while len(parsed) < 3:
        parsed.append(0)
    return tuple(parsed)


def _is_newer_version(latest: str, current: str) -> bool:
    """Return True when the latest version is newer than the current version."""
    return _parse_version_string(latest) > _parse_version_string(current)


def _channel_has_epg(channel_name: str) -> bool:
    """Return True when the channel has at least one loaded EPG entry."""
    if not channel_name:
        return False
    try:
        from utils.epg import epg_service
        if not epg_service.is_loaded:
            return False
        with epg_service._lock:
            epg_id = epg_service._resolve_channel(channel_name, "")
            return bool(epg_id and epg_service._schedules.get(epg_id))
    except Exception:
        return False


def _channel_health_score(channel: Dict[str, Any], has_epg: Optional[bool] = None) -> int:
    """Compute a simple reliability score for verified-first browsing."""
    score = 0
    status = (channel.get("status") or "").lower()
    if status == "working":
        score += 50
    elif status == "unchecked":
        score += 10
    elif status in {"broken", "failed", "offline"}:
        score -= 20

    urls = channel.get("urls") or []
    if len(urls) > 1:
        score += 10
    if channel.get("logo"):
        score += 5
    if has_epg is None:
        has_epg = _channel_has_epg(channel.get("name") or "")
    if has_epg:
        score += 5
    return score


def _channel_health_label(score: int) -> str:
    if score >= 50:
        return "reliable"
    if score >= 20:
        return "unstable"
    return "offline"

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
        try:
            response = await call_next(request)
        except RuntimeError as exc:
            # Starlette BaseHTTPMiddleware raises "No response returned"
            # when a StreamingResponse generator is interrupted by a client
            # disconnect.  The bytes were already delivered to the (now-gone)
            # client; the error is just noise.  Suppress it for proxy
            # streams which see this constantly during HLS playback.
            if (request.url.path.startswith("/api/proxy")
                    and "No response returned" in str(exc)):
                return Response(status_code=499)  # nginx "client closed request"
            raise
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


# ─── CSRF Middleware ─────────────────────────────────────────────────────────
#
# Wildcard CORS lets browsers fire cross-site POSTs at our state-changing
# routes (refresh, favorites toggle, report, analytics).  Block any
# state-changing request whose Origin/Referer doesn't match our own server
# host.  Pure CLI/curl/mobile callers send no Origin/Referer and are still
# allowed (no ambient browser credentials to abuse).

_CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# Endpoints that legitimately receive cross-origin POSTs and don't carry
# state-changing side effects beyond their own rate-limited / validated logic.
_CSRF_EXEMPT_PATH_PREFIXES = ("/api/health/report",)


class CSRFOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in _CSRF_PROTECTED_METHODS and not any(
            request.url.path.startswith(p) for p in _CSRF_EXEMPT_PATH_PREFIXES
        ):
            try:
                _enforce_same_origin(request)
            except HTTPException as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail},
                )
        try:
            return await call_next(request)
        except RuntimeError as exc:
            # Same Starlette streaming-disconnect bug as SecurityHeaders.
            if (request.url.path.startswith("/api/proxy")
                    and "No response returned" in str(exc)):
                return Response(status_code=499)
            raise


app.add_middleware(CSRFOriginMiddleware)


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


# ─── TLS helpers ─────────────────────────────────────────────────────────────
#
# Centralised SSL context construction so every aiohttp call uses certifi's
# CA bundle and verifies hostnames by default.  The proxy upstream gets an
# env-flag escape hatch (TV_VIEWER_PROXY_INSECURE_TLS=1) for legacy IPTV
# servers with broken/self-signed certs — disabled by default.

import ssl as _ssl
try:
    import certifi as _certifi
    _CERTIFI_PATH = _certifi.where()
except ImportError:
    _CERTIFI_PATH = None

_ssl_ctx_strict: Optional[_ssl.SSLContext] = None


def _get_strict_ssl_context() -> _ssl.SSLContext:
    """Return a process-wide SSL context with full hostname + chain verification."""
    global _ssl_ctx_strict
    if _ssl_ctx_strict is None:
        ctx = (_ssl.create_default_context(cafile=_CERTIFI_PATH)
               if _CERTIFI_PATH else _ssl.create_default_context())
        ctx.check_hostname = True
        ctx.verify_mode = _ssl.CERT_REQUIRED
        ctx.minimum_version = _ssl.TLSVersion.TLSv1_2
        _ssl_ctx_strict = ctx
    return _ssl_ctx_strict


_PROXY_TLS_INSECURE = os.environ.get(
    "TV_VIEWER_PROXY_INSECURE_TLS", ""
).strip().lower() in ("1", "true", "yes", "on")
if _PROXY_TLS_INSECURE:
    logger.warning(
        "TV_VIEWER_PROXY_INSECURE_TLS is enabled — /api/proxy will NOT "
        "verify upstream TLS certificates. Use only for legacy IPTV servers."
    )


def _proxy_ssl_param():
    """SSL parameter for the /api/proxy upstream call.

    Returns ``False`` only when the operator opted in via env var; otherwise
    returns the strict SSL context (certifi CA, TLS 1.2+, hostname check).
    """
    return False if _PROXY_TLS_INSECURE else _get_strict_ssl_context()


# ─── /api/proxy circuit breaker ─────────────────────────────────────────────
#
# A dead upstream URL combined with an aggressive HLS.js retry loop produced
# a 403 storm in production docker logs — the same two URLs hammered the
# proxy hundreds of times per second, saturating the event loop and
# starving /api/channels. The client-side fix bounds tryNextSource(); this
# server-side fix bounds *any* misbehaving client (including stale tabs
# from older app versions that we can no longer fix). After N consecutive
# 4xx responses for a URL within a short window, subsequent requests for
# that URL are short-circuited with the cached status until the cooldown
# elapses — no upstream call, no log spam, no event-loop time.
_PROXY_BREAKER_THRESHOLD = 5      # consecutive 4xx before tripping
_PROXY_BREAKER_WINDOW = 30.0      # seconds: 4xx within this window count
_PROXY_BREAKER_COOLDOWN = 60.0    # seconds: short-circuit window after trip
_PROXY_BREAKER_MAX_ENTRIES = 1024  # cap on tracked URLs (LRU-ish prune)
_proxy_breaker_state: dict = {}   # url -> {fails, first_ts, tripped_until, status}


def _breaker_should_short_circuit(url: str) -> Optional[int]:
    """Return the cached 4xx status to serve, or None if the call should proceed."""
    entry = _proxy_breaker_state.get(url)
    if not entry:
        return None
    tripped_until = entry.get("tripped_until", 0.0)
    if tripped_until and time.time() < tripped_until:
        return entry.get("status", 403)
    if tripped_until and time.time() >= tripped_until:
        # Cooldown elapsed — clear the trip but keep counting on next failure.
        entry["tripped_until"] = 0.0
        entry["fails"] = 0
    return None


def _breaker_record_failure(url: str, status: int) -> None:
    """Track a 4xx upstream response; trip the breaker if threshold reached."""
    now = time.time()
    entry = _proxy_breaker_state.get(url)
    if entry is None:
        # Soft prune to keep memory bounded.
        if len(_proxy_breaker_state) >= _PROXY_BREAKER_MAX_ENTRIES:
            try:
                oldest = min(
                    _proxy_breaker_state.items(),
                    key=lambda kv: kv[1].get("first_ts", 0.0),
                )[0]
                _proxy_breaker_state.pop(oldest, None)
            except ValueError:
                pass
        entry = {"fails": 0, "first_ts": now, "tripped_until": 0.0, "status": status}
        _proxy_breaker_state[url] = entry

    # Reset the window if the last failure was too long ago.
    if now - entry.get("first_ts", now) > _PROXY_BREAKER_WINDOW:
        entry["fails"] = 0
        entry["first_ts"] = now

    entry["fails"] += 1
    entry["status"] = status
    if entry["fails"] >= _PROXY_BREAKER_THRESHOLD:
        entry["tripped_until"] = now + _PROXY_BREAKER_COOLDOWN
        logger.warning(
            "Proxy circuit breaker tripped for %s (status=%d, cooldown=%.0fs)",
            url, status, _PROXY_BREAKER_COOLDOWN,
        )


def _breaker_record_success(url: str) -> None:
    """Successful upstream call clears any pending failure tally."""
    _proxy_breaker_state.pop(url, None)


import socket as _socket


def _resolve_once_and_check(hostname: str, port: int) -> List[tuple]:
    """Resolve *hostname* once and return ``getaddrinfo`` records — or raise
    ``HTTPException(403)`` if any resolved IP is in the SSRF blocklist.

    The returned records are what the caller must connect to *directly*
    (with ``Host:`` header set to the original hostname) so the validated
    IP is also the one we actually dial — closing the DNS-rebinding window
    that exists when validate and connect each do their own DNS lookup.
    """
    lower = hostname.lower()
    if lower in ('localhost', '0.0.0.0') or lower.endswith('.local'):
        raise HTTPException(403, "Access to internal network addresses is forbidden")
    try:
        records = _socket.getaddrinfo(hostname, port, _socket.AF_UNSPEC,
                                      _socket.SOCK_STREAM)
    except (_socket.gaierror, OSError) as exc:
        raise HTTPException(502, f"DNS resolution failed: {exc}")
    if not records:
        raise HTTPException(502, "DNS resolution returned no addresses")
    for info in records:
        try:
            resolved_ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            raise HTTPException(403, "Unresolvable address")
        if (resolved_ip.is_private or resolved_ip.is_loopback
                or resolved_ip.is_link_local or resolved_ip.is_reserved
                or any(resolved_ip in net for net in _BLOCKED_IP_RANGES)):
            raise HTTPException(403, "Access to internal network addresses is forbidden")
    return records


# ─── CSRF / Origin guard ─────────────────────────────────────────────────────
#
# CORS is wildcard so the browser will happily fire cross-site POSTs at our
# unauthenticated state-changing routes.  This helper rejects POSTs whose
# Origin/Referer doesn't match our own server (or an explicit allowlist).

_CSRF_ALLOWED_ORIGINS = {
    o.strip().rstrip('/')
    for o in os.environ.get("TV_VIEWER_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
}


def _enforce_same_origin(request: Request) -> None:
    """Reject cross-site state-changing requests.

    Allowed when:
      * the request's Origin/Referer matches our own ``base_url`` host, OR
      * no Origin/Referer was sent (CLI / curl / mobile — no browser CSRF
        risk since there's no ambient credential context), OR
      * the origin is in ``TV_VIEWER_ALLOWED_ORIGINS``.
    """
    origin = request.headers.get("origin") or ""
    referer = request.headers.get("referer") or ""
    if not origin and not referer:
        return
    try:
        own = urlparse(str(request.base_url))
        own_host = f"{own.scheme}://{own.netloc}".rstrip('/')
    except Exception:
        own_host = ""
    candidates = {origin.rstrip('/')}
    if referer:
        try:
            rp = urlparse(referer)
            candidates.add(f"{rp.scheme}://{rp.netloc}".rstrip('/'))
        except Exception:
            pass
    if own_host and own_host in candidates:
        return
    if _CSRF_ALLOWED_ORIGINS & candidates:
        return
    raise HTTPException(403, "Cross-origin request rejected")


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
        except (socket.gaierror, OSError):
            # DNS error — fail closed so we don't accidentally permit a
            # name that resolves later (e.g. after rebinding).
            return True
        except ValueError:
            return True
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

    # Allow any port — SSRF is prevented by private IP blocking above.
    # Streaming servers commonly use non-standard ports (9443, 5000+, etc.)

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
    verified_only: bool = Query(False),
    show_all: bool = Query(False),
    limit: int = Query(200, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    """Get channels with optional filtering. Local (IL) channels shown first."""
    # ── Fast path: O(1) index lookup when category and/or country is specified ──
    cat_lc = category.lower() if category else None
    country_lc = country.lower() if country else None

    if cat_lc == "local":
        # LOCAL = channels from user's detected country (pre-built list)
        channels = _cache.local_channels
    elif cat_lc and country_lc:
        channels = _cache.by_cat_country.get((cat_lc, country_lc), [])
    elif cat_lc:
        channels = _cache.by_category.get(cat_lc, [])
    elif country_lc:
        channels = _cache.by_country.get(country_lc, [])
    else:
        channels = _cache.sorted_channels

    favorites = _cache.favorites if favorites_only else set()
    if favorites_only:
        channels = [c for c in channels if c.get("url") in favorites]
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

    enriched = []
    for ch in channels:
        has_epg = _channel_has_epg(ch.get("name") or "")
        health_score = _channel_health_score(ch, has_epg=has_epg)
        enriched.append({
            **ch,
            "health_score": health_score,
            "health": _channel_health_label(health_score),
        })

    if verified_only:
        enriched = [c for c in enriched if c.get("health") == "reliable"]

    # Stable sort: keep existing local/alphabetical order inside equal scores.
    enriched.sort(key=lambda ch: ch.get("health_score", 0), reverse=True)

    total = len(enriched)
    channels = enriched[offset:offset + limit]

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
            "health_score": ch.get("health_score", 0),
            "health": ch.get("health", "offline"),
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
    countries = set(c.get("country", "Unknown") for c in channels)
    try:
        from utils.supabase_channels import is_configured
        cloud_db = "connected" if is_configured() else "not configured"
    except Exception:
        cloud_db = "unavailable"
    return {
        "version": config.APP_VERSION,
        "app_name": config.APP_NAME,
        "total_channels": len(channels),
        "working_channels": working,
        "countries": len(countries),
        "cloud_db": cloud_db,
        "status": "running",
        "refresh_in_progress": _refresh_in_progress,
    }


_version_cache: Dict[str, Any] = {}
_version_cache_time: float = 0
_VERSION_CACHE_TTL = 6 * 3600  # 6 hours
_LATEST_RELEASE_URL = "https://github.com/tv-viewer-app/tv_viewer/releases/latest"
_LATEST_RELEASE_API = "https://api.github.com/repos/tv-viewer-app/tv_viewer/releases/latest"
_DOCKER_IMAGE = "asummoner/tvviewerapp"


def _format_release_notes(body: str, limit: int = 500) -> str:
    """Strip markdown headers and trim release notes for update banners."""
    lines = []
    for raw_line in str(body or "").splitlines():
        line = raw_line.strip()
        if not line or re.match(r"^#{1,6}\s+", line):
            continue
        lines.append(line)
    return "\n".join(lines)[:limit].strip()


def _extract_release_assets(assets: List[Any], version: str) -> Dict[str, str]:
    """Return per-platform asset URLs from a GitHub release assets array."""
    result = {
        "windows": "",
        "android": "",
        "linux": "",
        "docker": f"docker pull {_DOCKER_IMAGE}:{version}",
    }
    for asset in assets or []:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name", "")).lower()
        url = str(asset.get("browser_download_url", "")).strip()
        if not url:
            continue
        if not result["windows"] and "windows" in name:
            result["windows"] = url
        elif not result["android"] and (name.endswith(".apk") or "android" in name):
            result["android"] = url
        elif not result["linux"] and "linux" in name:
            result["linux"] = url
    return result


async def _refresh_version_cache(force: bool = False) -> Dict[str, Any]:
    """Fetch and cache latest release metadata for client-side update banners."""
    global _version_cache, _version_cache_time

    now = time.time()
    if not force and _version_cache and (now - _version_cache_time) < _VERSION_CACHE_TTL:
        return _version_cache

    current = config.APP_VERSION
    latest = current
    download_url = _LATEST_RELEASE_URL
    release_notes = ""
    assets = _extract_release_assets([], current)

    try:
        connector = aiohttp.TCPConnector(limit=2, ttl_dns_cache=300, ssl=_get_strict_ssl_context())
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(
                _LATEST_RELEASE_API,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"tv-viewer/{current}",
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    latest = str(data.get("tag_name", "") or current).lstrip("v") or current
                    download_url = str(data.get("html_url", "") or _LATEST_RELEASE_URL)
                    release_notes = _format_release_notes(data.get("body", ""))
                    assets = _extract_release_assets(data.get("assets") or [], latest)
    except Exception as exc:
        logger.debug(f"Version check skipped ({exc})")

    result = {
        "current": current,
        "latest": latest,
        "update_available": _is_newer_version(latest, current),
        "download_url": download_url,
        "release_notes": release_notes,
        "assets": assets,
    }
    _version_cache = result
    _version_cache_time = now
    return result


@app.get("/api/version")
async def get_version():
    """Return the running version and latest available GitHub release metadata."""
    return await _refresh_version_cache()


# ─── Stream Proxy (CORS bypass) ─────────────────────────────────────────────

import aiohttp
from urllib.parse import urljoin, quote

# Proxy timeout for upstream connections
_proxy_timeout = aiohttp.ClientTimeout(total=60, sock_read=30)
# Shared connector pool — avoids creating per-request connectors (fixes session leak)
_proxy_connector: Optional[aiohttp.TCPConnector] = None
_PROXY_QUERY_URL_LIMIT = 4096
_PROXY_TOKEN_TTL = 1800
_proxy_token_store: Dict[str, Dict[str, Any]] = {}


def classify_failure(error_msg: str) -> str:
    """Classify stream failure for analytics and user messaging."""
    msg = str(error_msg or "").lower()
    if "geo_blocked" in msg or "geo blocked" in msg:
        return "geo_blocked"
    if "403" in msg or "forbidden" in msg:
        return "geo_blocked"
    if "not_found" in msg or "not found" in msg:
        return "not_found"
    if "404" in msg or "not found" in msg:
        return "not_found"
    if "timeout" in msg or "timed out" in msg:
        return "timeout"
    if "tls_error" in msg or "tls error" in msg:
        return "tls_error"
    if "ssl" in msg or "tls" in msg or "certificate" in msg:
        return "tls_error"
    if "dns_error" in msg or "dns error" in msg:
        return "dns_error"
    if "dns" in msg or "resolve" in msg or "getaddrinfo" in msg:
        return "dns_error"
    if "server_error" in msg or "server error" in msg:
        return "server_error"
    if re.search(r"\b5\d{2}\b", msg) or "server error" in msg:
        return "server_error"
    if "unsupported_format" in msg or "unsupported format" in msg:
        return "unsupported_format"
    if "codec" in msg or "format" in msg or "unsupported" in msg:
        return "unsupported_format"
    if "connection_error" in msg or "connection error" in msg:
        return "connection_error"
    if "connection" in msg or "refused" in msg or "reset" in msg:
        return "connection_error"
    return "unknown"


def _stream_failure_headers(
    failure_type: str,
    *,
    upstream_status: Optional[int] = None,
    breaker: bool = False,
) -> Dict[str, str]:
    """Headers that distinguish upstream failures from proxy failures."""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "X-Proxy-Upstream": "true",
        "X-Stream-Status": "failed",
        "X-Stream-Failure-Type": failure_type,
        "X-Stream-Status-Reason": failure_type,
    }
    if upstream_status is not None:
        headers["X-Upstream-Status"] = str(upstream_status)
    if breaker:
        headers["X-Proxy-Circuit-Breaker"] = "tripped"
    return headers


def _get_proxy_connector() -> aiohttp.TCPConnector:
    global _proxy_connector
    if _proxy_connector is None or _proxy_connector.closed:
        _proxy_connector = aiohttp.TCPConnector(limit=50, ttl_dns_cache=300)
    return _proxy_connector


def _prune_proxy_tokens(now: Optional[float] = None) -> None:
    current = now or time.time()
    expired = [
        token for token, data in _proxy_token_store.items()
        if float(data.get("expires_at", 0)) <= current
    ]
    for token in expired:
        _proxy_token_store.pop(token, None)


def _register_proxy_token(url: str) -> str:
    _prune_proxy_tokens()
    token = uuid.uuid4().hex
    _proxy_token_store[token] = {
        "url": url,
        "expires_at": time.time() + _PROXY_TOKEN_TTL,
    }
    return token


def _build_proxy_url(base_url: str, target_url: str) -> str:
    if len(target_url) <= _PROXY_QUERY_URL_LIMIT:
        return f"{base_url}api/proxy?url={quote(target_url, safe='')}"
    token = _register_proxy_token(target_url)
    return f"{base_url}api/proxy/{token}"


def _resolve_proxy_token(token: str) -> Optional[str]:
    _prune_proxy_tokens()
    record = _proxy_token_store.get(token)
    if not record:
        return None
    return str(record.get("url") or "")


async def _close_proxy_resources(
    response: Optional[aiohttp.ClientResponse],
    session: Optional[aiohttp.ClientSession],
) -> None:
    if response is not None:
        try:
            release_result = response.release()
            if inspect.isawaitable(release_result):
                await release_result
        except Exception:
            pass
    if session is not None and not session.closed:
        try:
            await session.close()
        except Exception:
            pass


async def _proxy_stream_impl(request: Request, url: str):
    """Proxy an HLS stream to bypass CORS restrictions.
    Rewrites .m3u8 manifests so segment URLs also go through the proxy."""
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # SSRF protection
    _validate_proxy_url(url)

    # Circuit breaker: if this URL has been failing repeatedly, return the
    # cached 4xx without touching upstream. Stops 403 storms from
    # misbehaving clients (e.g. HLS.js retry loops in old tabs) from
    # saturating the event loop and starving /api/channels.
    short_circuit_status = _breaker_should_short_circuit(url)
    if short_circuit_status is not None:
        detail = f"Upstream {short_circuit_status} (breaker)"
        failure_type = classify_failure(detail)
        return JSONResponse(
            status_code=short_circuit_status,
            content={
                "detail": detail,
                "failure_type": failure_type,
            },
            headers=_stream_failure_headers(
                failure_type,
                upstream_status=short_circuit_status,
                breaker=True,
            ),
        )

    # Extract origin from URL for CDN compatibility
    from urllib.parse import urlparse as _parse_url
    _parsed = _parse_url(url)
    _origin = f"{_parsed.scheme}://{_parsed.netloc}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": _origin + "/",
        "Origin": _origin,
    }
    session = None
    resp = None
    try:
        session = aiohttp.ClientSession(
            timeout=_proxy_timeout,
            connector=_get_proxy_connector(),
            connector_owner=False  # Don't close shared connector when session closes
        )
        resp = await session.get(url, headers=headers, ssl=_proxy_ssl_param())

        if resp.status != 200:
            status = resp.status
            await _close_proxy_resources(resp, session)
            detail = f"Upstream returned {status}"
            failure_type = classify_failure(detail)
            # Track 4xx for the circuit breaker. 5xx alone shouldn't trip it
            # — those may be transient — but 4xx (esp 403/404) means the
            # URL itself is wrong/dead, so retries will only make it worse.
            if 400 <= status < 500:
                _breaker_record_failure(url, status)
            return JSONResponse(
                status_code=status,
                content={"detail": detail, "failure_type": failure_type},
                headers=_stream_failure_headers(
                    failure_type,
                    upstream_status=status,
                ),
            )

        # For m3u8 manifests, rewrite URLs to go through proxy
        if ".m3u8" in url or "mpegurl" in (resp.headers.get("content-type", "").lower()):
            body = await resp.text()
            await _close_proxy_resources(resp, session)
            _breaker_record_success(url)
            rewritten = _rewrite_manifest(body, url, str(request.base_url))
            return StreamingResponse(
                iter([rewritten.encode()]),
                media_type="application/vnd.apple.mpegurl",
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"}
            )

        # For segments (.ts, .mp4, etc.) — stream through
        media_type = resp.headers.get("content-type", "video/mp2t")
        _breaker_record_success(url)

        async def stream_generator():
            try:
                async for chunk in resp.content.iter_chunked(65536):
                    yield chunk
            except (
                asyncio.TimeoutError,
                aiohttp.ClientError,
                ConnectionResetError,
                OSError,
            ) as exc:
                logger.debug(
                    "Proxy stream ended quietly for %s: %s",
                    _parsed.netloc or _parsed.path or "upstream",
                    type(exc).__name__,
                )
                return

        return StreamingResponse(
            stream_generator(),
            media_type=media_type,
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"},
            background=BackgroundTask(_close_proxy_resources, resp, session),
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, asyncio.CancelledError, OSError) as e:
        await _close_proxy_resources(resp, session)
        detail = f"Upstream connection failed: {type(e).__name__}"
        failure_type = classify_failure(f"{detail} {e}")
        return JSONResponse(
            status_code=502,
            content={
                "detail": detail,
                "failure_type": failure_type
            },
            headers=_stream_failure_headers(failure_type)
        )
    except Exception as e:
        await _close_proxy_resources(resp, session)
        logger.error(f"Proxy unexpected error: {e}")
        failure_type = classify_failure(str(e))
        return JSONResponse(
            status_code=502,
            content={
                "detail": "Proxy error",
                "failure_type": failure_type
            },
            headers=_stream_failure_headers(failure_type)
        )


@app.get("/api/proxy")
async def proxy_stream(request: Request, url: str = Query(..., description="Stream URL to proxy")):
    if len(url) > _PROXY_QUERY_URL_LIMIT:
        raise HTTPException(status_code=414, detail="URL too long for proxy")
    return await _proxy_stream_impl(request, url)


@app.get("/api/proxy/{token}")
async def proxy_stream_token(request: Request, token: str):
    url = _resolve_proxy_token(token)
    if not url:
        raise HTTPException(status_code=404, detail="Proxy token expired or not found")
    return await _proxy_stream_impl(request, url)


@app.post("/api/proxy")
async def proxy_stream_post(request: Request):
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request body")

    url = str(body.get("url", "") or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")

    return {
        "proxy_url": _build_proxy_url(str(request.base_url), url),
        "tokenized": len(url) > _PROXY_QUERY_URL_LIMIT,
    }


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
            result.append(_build_proxy_url(base_url, abs_url))
        elif stripped.startswith('#EXT-X-MAP:URI="') or 'URI="' in stripped:
            # Rewrite URI= attributes in tags
            def rewrite_uri(m):
                uri = m.group(1)
                if not uri.startswith(('http://', 'https://')):
                    uri = urljoin(manifest_url, uri)
                return f'URI="{_build_proxy_url(base_url, uri)}"'
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


@app.get("/api/epg-status")
async def get_epg_status():
    """Return EPG loader diagnostics — channel count, last fetch, sources."""
    try:
        from utils.epg import epg_service
        return {
            "initialized": bool(epg_service._initialized),
            "channel_count": epg_service.channel_count,
            "last_fetch": epg_service._last_fetch,
            "sources": epg_service.get_epg_sources(),
        }
    except Exception as e:
        return {"initialized": False, "error": str(e)}


@app.post("/api/epg/refresh")
async def refresh_epg():
    """Force a fresh EPG re-fetch (bypassing cache). Useful in Docker when
    the initial startup fetch failed and left an empty cache."""
    try:
        from utils.epg import epg_service
        epg_service._last_fetch = 0
        epg_service._initialized = False
        await epg_service.initialize()
        return {
            "status": "ok",
            "channel_count": epg_service.channel_count,
        }
    except Exception as e:
        logger.warning(f"EPG refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"EPG refresh failed: {e}")


# ─── Community Statistics ────────────────────────────────────────────────────

_stats_cache: Dict[str, Any] = {}
_stats_cache_time: float = 0
_STATS_CACHE_TTL = 1800  # 30 minutes


async def _refresh_statistics_cache(force: bool = False) -> Dict[str, Any]:
    """Build and cache aggregated community statistics."""
    global _stats_cache, _stats_cache_time

    now = time.time()
    if not force and _stats_cache and (now - _stats_cache_time) < _STATS_CACHE_TTL:
        return _stats_cache

    # Always build channel database stats (available regardless of Supabase)
    channels = _load_channels()
    ch_countries: Dict[str, int] = {}
    ch_categories: Dict[str, int] = {}
    recently_added: List[Dict] = []
    working_count = 0

    for ch in channels:
        c = ch.get('country', 'Unknown')
        if c and c != 'Unknown':
            ch_countries[c] = ch_countries.get(c, 0) + 1
        cat = ch.get('category', 'General')
        ch_categories[cat] = ch_categories.get(cat, 0) + 1
        if ch.get('status') == 'working':
            working_count += 1

    # Get recently added channels (last 10 sorted by name for stability)
    recently_added = sorted(
        [{"name": ch.get("name", ""), "country": ch.get("country", ""), "category": ch.get("category", "")}
         for ch in channels if ch.get("name")],
        key=lambda x: x["name"]
    )[-10:]

    top_ch_countries = sorted(ch_countries.items(), key=lambda x: -x[1])[:15]
    top_categories = sorted(ch_categories.items(), key=lambda x: -x[1])[:10]

    # Try to get live analytics from Supabase
    analytics_data = {}
    try:
        from utils.supabase_channels import is_configured
        if is_configured():
            import aiohttp
            from datetime import datetime, timedelta, timezone
            supabase_url = os.environ.get('SUPABASE_URL', '') or config.SUPABASE_URL
            # Prefer the publishable key now that anon can read the aggregated
            # analytics views and the raw table via RLS. Fall back to the
            # service role only when anon is not configured in the environment.
            supabase_key = (
                os.environ.get('SUPABASE_ANON_KEY', '').strip()
                or config.SUPABASE_ANON_KEY
                or os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '').strip()
            )

            since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            params = {
                'select': 'event_type,country,platform,event_data,device_id,created_at',
                'created_at': f'gte.{since}',
                'order': 'created_at.desc',
                'limit': '5000',
            }
            headers_req = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
            }
            async with aiohttp.ClientSession() as session:
                # Try pre-aggregated materialized views first (works with
                # publishable key and avoids scanning raw analytics rows).
                try:
                    async with session.get(
                        f'{supabase_url}/rest/v1/mv_top_channels?order=play_count.desc&limit=15',
                        headers=headers_req,
                        timeout=aiohttp.ClientTimeout(total=10),
                        ssl=_get_strict_ssl_context(),
                    ) as mv_resp:
                        if mv_resp.status == 200:
                            mv_channels = await mv_resp.json()
                            if mv_channels:
                                top_played = []
                                for channel in mv_channels[:15]:
                                    country = str(channel.get("channel_country", "") or "").strip()
                                    category = str(channel.get("channel_category", "") or "").strip()
                                    label = " ".join(part for part in (country, category) if part).strip()
                                    if not label:
                                        label = str(channel.get("channel_hash", "Unknown channel") or "Unknown channel")
                                    top_played.append((label, int(channel.get("play_count", 0) or 0)))

                                analytics_data["top_played"] = top_played
                                analytics_data["unique_channels_played"] = len(top_played)
                                analytics_data["total_plays"] = sum(plays for _, plays in top_played)

                    async with session.get(
                        f'{supabase_url}/rest/v1/mv_daily_active_users?order=day.desc&limit=30',
                        headers=headers_req,
                        timeout=aiohttp.ClientTimeout(total=10),
                        ssl=_get_strict_ssl_context(),
                    ) as dau_resp:
                        if dau_resp.status == 200:
                            dau_data = await dau_resp.json()
                            if dau_data:
                                total_devices = len(
                                    set(
                                        f'{d.get("day", "")}{d.get("platform", "")}'
                                        for d in dau_data
                                    )
                                )
                                analytics_data["unique_users"] = total_devices
                                analytics_data["total_events"] = sum(
                                    int(d.get("total_events", 0) or 0) for d in dau_data
                                )
                                platforms_mv: Dict[str, int] = {}
                                for d in dau_data:
                                    platform = str(d.get("platform", "unknown") or "unknown")
                                    platforms_mv[platform] = platforms_mv.get(platform, 0) + int(
                                        d.get("total_events", 0) or 0
                                    )
                                analytics_data["platforms"] = dict(
                                    sorted(platforms_mv.items(), key=lambda x: -x[1])
                                )
                except Exception as mv_err:
                    logger.debug(f"Materialized views not available: {mv_err}")

                async with session.get(
                    f'{supabase_url}/rest/v1/analytics_events',
                    params=params,
                    headers=headers_req,
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=_get_strict_ssl_context(),
                ) as resp:
                    if resp.status == 200:
                        events = await resp.json()
                        if events:
                            devices = set()
                            user_countries: Dict[str, int] = {}
                            platforms: Dict[str, int] = {}
                            played_channels: Dict[str, int] = {}
                            country_last_access: Dict[str, str] = {}
                            country_channels: Dict[str, Counter] = {}
                            live_sessions = 0
                            today_plays = 0
                            today_devices = set()
                            live_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
                            today_start = datetime.now(timezone.utc).replace(
                                hour=0, minute=0, second=0, microsecond=0
                            )

                            for ev in events:
                                devices.add(ev.get('device_id', ''))
                                p = ev.get('platform', 'unknown')
                                platforms[p] = platforms.get(p, 0) + 1
                                uc = ev.get('country', 'XX')
                                if uc and uc != 'XX':
                                    user_countries[uc] = user_countries.get(uc, 0) + 1
                                    created_at = ev.get('created_at', '')
                                    if created_at > country_last_access.get(uc, ''):
                                        country_last_access[uc] = created_at
                                # Channel name from event_data
                                ed = ev.get('event_data') or {}
                                cn = ''
                                if isinstance(ed, dict):
                                    cn = ed.get('name', '') or ed.get('channel_name', '')
                                created_at_raw = str(ev.get('created_at', '') or '')
                                created_at_dt = None
                                if created_at_raw:
                                    try:
                                        created_at_dt = datetime.fromisoformat(
                                            created_at_raw.replace('Z', '+00:00')
                                        )
                                    except ValueError:
                                        created_at_dt = None
                                if created_at_dt is not None:
                                    if created_at_dt >= live_cutoff:
                                        live_sessions += 1
                                    if created_at_dt >= today_start:
                                        device_id = ev.get('device_id', '')
                                        if device_id:
                                            today_devices.add(device_id)
                                        if ev.get('event_type') == 'channel_play':
                                            today_plays += 1
                                if cn and ev.get('event_type') == 'channel_play':
                                    played_channels[cn] = played_channels.get(cn, 0) + 1
                                    if uc and uc != 'XX':
                                        if uc not in country_channels:
                                            country_channels[uc] = Counter()
                                        country_channels[uc][cn] += 1

                            analytics_data.update({
                                "unique_users": len(devices),
                                "total_events": len(events),
                                "user_countries": sorted(user_countries.items(), key=lambda x: -x[1])[:15],
                                "platforms": dict(sorted(platforms.items(), key=lambda x: -x[1])),
                                "top_played": sorted(played_channels.items(), key=lambda x: -x[1])[:15],
                                "unique_channels_played": len(played_channels),
                                "country_last_access": [
                                    {"name": k, "last_seen": v[:10]}
                                    for k, v in sorted(country_last_access.items(), key=lambda x: x[1], reverse=True)[:15]
                                ],
                                "country_top_channels": {
                                    k: [{"name": n, "plays": c} for n, c in v.most_common(3)]
                                    for k, v in country_channels.items()
                                    if user_countries.get(k, 0) > 5 and sum(v.values()) >= 3
                                },
                                "live_sessions": live_sessions,
                                "today_plays": today_plays,
                                "today_active": len(today_devices),
                                "total_plays": sum(1 for e in events if e.get('event_type') == 'channel_play'),
                            })
    except Exception as analytics_err:
        logger.debug(f"Statistics: analytics query skipped ({analytics_err})")

    # Build comprehensive result
    has_analytics = bool(analytics_data.get("total_events") or analytics_data.get("top_played"))
    result = {
        "total_channels": len(channels),
        "working_channels": working_count,
        "channel_countries": [{"name": c[0], "channels": c[1]} for c in top_ch_countries],
        "categories": [{"name": c[0], "channels": c[1]} for c in top_categories],
        "recently_added": recently_added,
        # Analytics (live user data)
        "has_analytics": has_analytics,
        "unique_users": analytics_data.get("unique_users", 0),
        "live_sessions": analytics_data.get("live_sessions", 0),
        "today_plays": analytics_data.get("today_plays", 0),
        "today_active": analytics_data.get("today_active", 0),
        "total_plays": analytics_data.get("total_plays", 0),
        "total_events": analytics_data.get("total_events", 0),
        "unique_channels_played": analytics_data.get("unique_channels_played", 0),
        "platforms": analytics_data.get("platforms", {}),
        "user_countries": [{"name": c[0], "events": c[1]} for c in analytics_data.get("user_countries", [])],
        "top_channels": [{"name": c[0], "plays": c[1]} for c in analytics_data.get("top_played", [])],
        "country_last_access": analytics_data.get("country_last_access", []),
        "country_top_channels": analytics_data.get("country_top_channels", {}),
    }

    _stats_cache = result
    _stats_cache_time = now
    return result

@app.get("/api/statistics")
async def get_statistics(request: Request):
    """Aggregated community usage statistics from Supabase analytics (anonymous).
    Cached for 30 minutes. Rate-limited to 10 req/min/IP."""

    # Rate limit: 10 requests per minute per IP
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_limit_check(client_ip, "stats", max_n=10, window=60):
        raise HTTPException(status_code=429, detail="Too many requests")

    try:
        return await _refresh_statistics_cache()
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Statistics error: {e}")
        return {
            "error": "temporary_failure",
            "total_channels": 0,
            "has_analytics": False,
            "live_sessions": 0,
            "today_plays": 0,
            "today_active": 0,
            "total_events": 0,
        }


@app.on_event("startup")
async def _warm_statistics_cache_on_startup():
    """Pre-warm statistics cache shortly after startup."""

    async def _warm_cache():
        await asyncio.sleep(30)
        try:
            await _refresh_statistics_cache(force=True)
        except Exception as exc:
            logger.debug(f"Statistics pre-warm skipped ({exc})")

    asyncio.create_task(_warm_cache())


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

# Disallowed characters in user-supplied identifiers (channel names) before
# we forward them to PostgREST. These have filter-syntax meaning in PostgREST
# (https://postgrest.org/en/stable/api.html#horizontal-filtering-rows) and
# allowing them lets a client break out of `name=eq.{val}` into arbitrary
# row matching. We refuse rather than try to escape — channel names with these
# chars do not exist in our shared DB.
_POSTGREST_FORBIDDEN_CHARS = set(",()*:")
_MAX_CHANNEL_NAME_LEN = 200


def _is_safe_channel_name(name: str) -> bool:
    if not name or not isinstance(name, str):
        return False
    if len(name) > _MAX_CHANNEL_NAME_LEN:
        return False
    # Reject any character that is a PostgREST filter delimiter
    if any(c in _POSTGREST_FORBIDDEN_CHARS for c in name):
        return False
    # Reject control chars / newlines
    if any(ord(c) < 32 for c in name):
        return False
    return True


# Simple in-memory token bucket: cap promote-write traffic to the shared DB.
# Two independent buckets per client IP:
#   - global:  N requests per W seconds (all /api/health/report)
#   - promote: N promote=true requests per W seconds (writes to Supabase)
# In-memory only — fine for single-instance Docker. If you ever scale out
# horizontally, move to Redis/Supabase. The bucket auto-prunes on the read
# path to bound memory.
_HEALTH_RATE_GLOBAL = (600, 60.0)  # 600 reports per 60s per IP — generous;
                                   # plain reports are local-only and cheap.
_HEALTH_RATE_PROMOTE = (10, 60.0)  # 10 promotes per 60s per IP — these hit Supabase
                                   # and can be used to manipulate channel ordering.
_health_buckets: Dict[str, Dict[str, List[float]]] = {}
_health_buckets_lock = threading.Lock()


def _client_ip(request: Request) -> str:
    # Honor X-Forwarded-For when behind a trusted proxy (Docker reverse proxy);
    # fall back to direct peer. We hash for the abuse log; we keep raw here
    # because the bucket key only lives in memory.
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        # First entry is the original client
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit_check(ip: str, bucket: str, max_n: int, window: float) -> bool:
    """Return True if request is allowed; False if rate-limited.

    Token bucket via sliding window over a list of timestamps.
    """
    now = time.monotonic()
    with _health_buckets_lock:
        per_ip = _health_buckets.setdefault(ip, {})
        timestamps = per_ip.setdefault(bucket, [])
        # Prune stale
        cutoff = now - window
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
        if len(timestamps) >= max_n:
            return False
        timestamps.append(now)
        # Coarse memory bound: drop very-stale IPs entirely on each pass
        if len(_health_buckets) > 10_000:
            for stale_ip in [
                k for k, v in _health_buckets.items()
                if not any(v.values()) or all(
                    (not ts) or ts[-1] < cutoff for ts in v.values()
                )
            ]:
                _health_buckets.pop(stale_ip, None)
        return True


@app.post("/api/health/report")
async def health_report(request: Request):
    """Report channel playback health from client. Accepts {url, status, promote?, name?}.

    Rate-limiting strategy:
      * Plain reports (no promote) are cheap and local-only — generous cap.
      * Promote reports hit Supabase and can be used to manipulate channel
        ordering for all users — tight cap, downgraded to a plain report when
        exceeded (not 429'd, so the client doesn't see noise).
    """
    ip = _client_ip(request)
    # Global rate limit on the endpoint — only as a coarse abuse guard.
    # Return 200 with status=throttled instead of 429 so the frontend's
    # fire-and-forget POST stays quiet and doesn't pollute the console.
    if not _rate_limit_check(ip, "global",
                             _HEALTH_RATE_GLOBAL[0], _HEALTH_RATE_GLOBAL[1]):
        return {"status": "throttled"}

    try:
        body = await request.json()
        url = body.get("url", "")
        status = body.get("status", "")
        promote = bool(body.get("promote", False))
        ch_name = body.get("name", "") or ""
        reason = str(body.get("reason", "") or "")[:200]
        failure_type = classify_failure(reason) if reason else "unknown"
        should_record_broken = not (
            status == "broken" and failure_type == "geo_blocked"
        )
        if not url or status not in ("working", "broken"):
            return {"status": "ignored"}

        # Drop unsafe channel names early (defence in depth — PostgREST injection,
        # log injection, memory bloat from huge strings). Reporting still works,
        # but we silently disable promotion.
        if promote and not _is_safe_channel_name(ch_name):
            logger.debug(
                "health_report: rejecting promote (unsafe name) from %s len=%d",
                ip[:16], len(ch_name) if isinstance(ch_name, str) else -1,
            )
            promote = False
            ch_name = ""

        # Per-IP cap on promote writes (these hit Supabase). Downgrade silently
        # instead of rejecting — the report itself is still useful.
        if promote and not _rate_limit_check(
            ip, "promote", _HEALTH_RATE_PROMOTE[0], _HEALTH_RATE_PROMOTE[1]
        ):
            promote = False

        if status == "working":
            _mark_local_working(url)
            # Promote this URL to primary position in the channel's urls array
            if promote and ch_name:
                _promote_source(ch_name, url)
        elif should_record_broken:
            _mark_local_broken(url)
            logger.debug(
                "health_report: broken stream classified as %s for %s",
                failure_type,
                ch_name[:80] if isinstance(ch_name, str) else "",
            )
        else:
            logger.debug(
                "health_report: skipping geo-blocked broken report for %s",
                ch_name[:80] if isinstance(ch_name, str) else url[:80],
            )

        # Best-effort Supabase push
        try:
            from utils import supabase_channels
            if supabase_channels.is_configured():
                url_hash = hashlib.sha256(url.encode()).hexdigest()
                if status == "broken" and should_record_broken:
                    await supabase_channels.report_channel(url_hash)
                elif status == "working":
                    await supabase_channels.report_channel_working(url_hash)
                    # Promote in Supabase too
                    if promote and ch_name:
                        await _promote_source_supabase(ch_name, url)
        except Exception:
            pass

        return {
            "status": "recorded",
            "channel_status": status,
            "failure_type": failure_type,
            "counted": status != "broken" or should_record_broken,
        }
    except Exception as e:
        logger.debug(f"Health report error: {e}")
        return {"status": "error"}


def _mark_local_working(url: str):
    """Mark a channel as working — update memory cache, write-through to disk."""
    for ch in _cache.channels:
        if ch.get("url") == url or url in (ch.get("urls") or []):
            ch["status"] = "working"
            break


def _promote_source(name: str, working_url: str):
    """Promote a working URL to primary position in a channel's urls array."""
    for ch in _cache.channels:
        if (ch.get("name") or "").lower() == name.lower():
            urls = ch.get("urls") or []
            if working_url in urls and urls[0] != working_url:
                urls.remove(working_url)
                urls.insert(0, working_url)
                ch["urls"] = urls
                ch["url"] = working_url
            elif not urls and ch.get("url") != working_url:
                ch["url"] = working_url
            break


async def _promote_source_supabase(name: str, working_url: str):
    """Promote *working_url* to the primary slot for *name* via atomic RPC.

    Delegates to the ``promote_channel_source`` SECURITY DEFINER function.
    No race conditions, no PostgREST filter-escaping, no name-injection
    surface — the lookup happens server-side with ``lower(name)`` equality.
    """
    if not _is_safe_channel_name(name):
        return
    try:
        url_hash = hashlib.sha256(working_url.encode()).hexdigest()
        headers = {
            "apikey": config.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {config.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
        }
        import aiohttp
        import ssl
        try:
            import certifi
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ssl_ctx = ssl.create_default_context()
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        rpc_url = f'{config.SUPABASE_URL}/rest/v1/rpc/promote_channel_source'
        payload = {
            "p_channel_name": name,
            "p_working_url": working_url,
            "p_working_hash": url_hash,
        }
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                rpc_url, json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status in (200, 204):
                    logger.debug("Promoted source for %s in Supabase", name)
                else:
                    body = await resp.text()
                    logger.debug("promote_channel_source RPC %s: %s",
                                 resp.status, body[:200])
    except Exception as e:
        logger.debug(f"promote_source_supabase error: {e}")


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
            "country": str(body.get("country", "XX"))[:5],
        }
        if payload["event_type"] == "channel_fail":
            event_data = payload["event_data"]
            raw_reason = (
                event_data.get("failure_type")
                or event_data.get("reason")
                or event_data.get("error_code")
                or event_data.get("error_message")
                or ""
            )
            failure_type = classify_failure(raw_reason)
            event_data["failure_type"] = failure_type
            if not event_data.get("error_code"):
                event_data["error_code"] = failure_type
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
                    async with session.post(_ANALYTICS_URL, json=payload, headers=_ANALYTICS_HEADERS, ssl=_get_strict_ssl_context()) as resp:
                        if resp.status not in (200, 201):
                            logger.debug(f"Analytics forward: {resp.status}")
            except Exception as e:
                logger.debug(f"Analytics forward failed: {e}")

        return {"status": "ok"}
    except Exception:
        return {"status": "error"}


# ─── Server-side error reporter (forwards 500s to Supabase) ─────────────────

async def _report_server_error(
    error: BaseException,
    *,
    context: str,
    severity: str = "error",
) -> None:
    """Best-effort: post a `server_error` event to Supabase analytics_events.

    Uses the anon key already plumbed for /api/analytics. Never raises.
    Server has no device_id, so we use a stable per-instance UUID derived
    from the host so all errors from the same Docker container group
    together.
    """
    if not (_ANALYTICS_URL and _ANALYTICS_HEADERS):
        return
    try:
        import traceback as _tb
        frames = _tb.extract_tb(error.__traceback__) if error.__traceback__ else []
        stack_top = ""
        stack_summary = []
        if frames:
            last = frames[-1]
            fname = last.filename.replace("\\", "/").rsplit("/", 1)[-1]
            stack_top = f"{fname}:{last.lineno} in {last.name}"
            for fr in frames[-3:]:
                fn = fr.filename.replace("\\", "/").rsplit("/", 1)[-1]
                stack_summary.append(f"{fn}:{fr.lineno}:{fr.name}")
        msg = str(error)
        if len(msg) > 200:
            msg = msg[:200]
        payload = {
            "event_type": "server_error",
            "device_id": _SERVER_INSTANCE_ID,
            "platform": "web-server",
            "app_version": config.APP_VERSION,
            "event_data": {
                "error_type": type(error).__name__,
                "error_message": msg,
                "stack_top": stack_top,
                "stack_summary": stack_summary,
                "severity": severity if severity in ("warning", "error", "fatal") else "error",
                "is_handled": False,
                "context": context[:64],
            },
        }
        connector = aiohttp.TCPConnector(limit=2, ttl_dns_cache=300)
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.post(_ANALYTICS_URL, json=payload, headers=_ANALYTICS_HEADERS, ssl=_get_strict_ssl_context()) as resp:
                if resp.status not in (200, 201):
                    logger.debug(f"server_error report HTTP {resp.status}")
    except Exception as e:
        logger.debug(f"server_error report failed: {e}")


# Stable per-process instance ID so all errors from one container/process
# share a device_id (useful for dedup / scoping in the analytics dashboard).
_SERVER_INSTANCE_ID = str(uuid.uuid4())


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all that turns server crashes into 500s AND telemeters them.

    HTTPExceptions raised by handlers are NOT routed here — FastAPI handles
    them via its built-in HTTPException handler. This only fires for truly
    unexpected failures.
    """
    try:
        path = request.url.path if request and request.url else "?"
    except Exception:
        path = "?"
    try:
        logger.error("Unhandled exception in %s: %s", path, exc, exc_info=True)
    except Exception:
        pass
    # Fire-and-forget telemetry; never let the reporter mask the original 500.
    try:
        asyncio.create_task(_report_server_error(exc, context=f"http:{path[:48]}"))
    except Exception:
        pass
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


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
            cached_channels = _load_channels()
            if cached_channels:
                mgr.channels = copy.deepcopy(cached_channels)
                mgr._organize_channels()
            else:
                mgr.load_cached_channels()

            # Run async fetch in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(mgr._fetch_and_update())
                if mgr.channels:
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

    # Auto-detect and update channels on startup
    # Logic: always refresh from cloud DB if available and data is stale/incomplete
    channels_path = DATA_DIR / "channels.json"
    try:
        with open(channels_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing_count = len(data.get("channels", []))
        # Check file age — refresh if older than 24 hours
        import time as _time
        file_age_hours = (_time.time() - channels_path.stat().st_mtime) / 3600
    except Exception:
        existing_count = 0
        file_age_hours = 999  # Force fetch

    # Check if cloud channels DB is available
    try:
        from utils.supabase_channels import is_configured as _sb_configured
        cloud_db_available = _sb_configured()
    except Exception:
        cloud_db_available = False

    # Determine if fetch is needed:
    # 1. No channels at all → always fetch
    # 2. Cloud DB available + channel count below expected (stale M3U data) → fetch
    # 3. Cloud DB available + data older than 24h → refresh for updated streams
    # 4. No cloud DB + no channels → fall back to M3U repos
    if existing_count == 0:
        need_fetch = True
        fetch_reason = "no channels in cache"
    elif cloud_db_available and existing_count < 5000:
        need_fetch = True
        fetch_reason = f"cache has only {existing_count} channels (cloud DB has 15k+)"
    elif cloud_db_available and file_age_hours > 24:
        need_fetch = True
        fetch_reason = f"cache is {file_age_hours:.0f}h old (refreshing from cloud DB)"
    else:
        need_fetch = False
        fetch_reason = "cache is fresh"

    print(f"   📊 Channel cache: {existing_count} channels ({file_age_hours:.1f}h old) | Cloud DB: {'connected' if cloud_db_available else 'not configured'}")
    print(f"   {'🔄' if need_fetch else '✅'} {'Fetch needed: ' + fetch_reason if need_fetch else 'Using cached channels'}")

    def _preload_epg():
        """Pre-load EPG data in background so it's ready when users browse."""
        import asyncio as _aio
        try:
            from utils.epg import epg_service
            print("   📺 Loading EPG program guide...")
            import time as _t
            _t0 = _t.time()
            _aio.run(epg_service.initialize())
            _elapsed = _t.time() - _t0
            if epg_service.is_loaded:
                print(f"   ✅ EPG loaded: {epg_service.channel_count} channels in {_elapsed:.1f}s")
            else:
                print(f"   ⚠️  EPG: no program data available ({_elapsed:.1f}s)")
        except Exception as e:
            print(f"   ⚠️  EPG load failed: {e}")

    if need_fetch:
        # Start fetch in background thread so server starts immediately
        def _startup_fetch():
            global _refresh_in_progress
            _refresh_in_progress = True
            import asyncio as _aio
            print("   ⏳ Fetching channels in background...")

            try:
                # Strategy 1: Try cloud channels database first (fast, ~5s)
                try:
                    from utils.supabase_channels import fetch_channels, is_configured
                    if is_configured():
                        print("   📡 Connecting to cloud channels database...")
                        import time as _t
                        _t0 = _t.time()
                        channels = _aio.run(fetch_channels())
                        _elapsed = _t.time() - _t0
                        if channels:
                            with open(channels_path, "w", encoding="utf-8") as f:
                                json.dump({"channels": channels}, f, ensure_ascii=False)
                            print(f"   ✅ Loaded {len(channels)} channels from cloud DB in {_elapsed:.1f}s")
                            _cache.invalidate()
                            # Pre-load EPG data in background
                            _preload_epg()
                            return
                        else:
                            print(f"   ⚠️  Cloud DB returned 0 channels ({_elapsed:.1f}s)")
                    else:
                        print("   ℹ️  Cloud channels DB not configured (set SUPABASE_URL/KEY env vars)")
                except Exception as e:
                    print(f"   ⚠️  Cloud DB fetch failed: {e}")

                # Strategy 2: Fall back to M3U repositories (slow, ~60-120s)
                try:
                    print("   📡 Falling back to M3U repositories...")
                    from core.repository import RepositoryHandler
                    handler = RepositoryHandler()
                    channels = _aio.run(handler.fetch_all_repositories())
                    if channels:
                        with open(channels_path, "w", encoding="utf-8") as f:
                            json.dump({"channels": channels}, f, ensure_ascii=False)
                        print(f"   ✅ Loaded {len(channels)} channels from repositories")
                        _cache.invalidate()
                    else:
                        print("   ⚠️  No channels fetched — use /api/refresh later")
                except Exception as e:
                    print(f"   ⚠️  Repository fetch failed: {e}")
            finally:
                _refresh_in_progress = False

        import threading
        t = threading.Thread(target=_startup_fetch, daemon=True)
        t.start()
        print("   🚀 Server starting (channels loading in background)...\n")
    else:
        # Channels cached — just pre-load EPG in background
        import threading
        t = threading.Thread(target=_preload_epg, daemon=True)
        t.start()

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
