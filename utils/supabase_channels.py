"""Supabase-backed channel repository for crowdsourced channel sharing.

Clients pull the shared channel list from Supabase first (fast, pre-consolidated),
then supplement with M3U sources. New channels discovered from M3U or custom
playlists are contributed back to Supabase.

If Supabase is unavailable, the app falls back to M3U-only mode seamlessly.

Table: channels
  url_hash (text PK), name, urls (jsonb[]), category, country, logo,
  media_type, source, report_count, created_at, updated_at
"""

import hashlib
import json
import logging
import os
import re
import ssl
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import certifi
except ImportError:
    certifi = None

logger = logging.getLogger(__name__)

# Supabase configuration
try:
    import config as _cfg
    _SUPABASE_URL = _cfg.SUPABASE_URL
    _SUPABASE_KEY = _cfg.SUPABASE_ANON_KEY
except (ImportError, AttributeError):
    _SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    _SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

_TABLE = 'channels'
_ENABLED = bool(_SUPABASE_URL and _SUPABASE_KEY)


# ---------------------------------------------------------------------------
# SSL / TLS hardening (Issue #97)
# ---------------------------------------------------------------------------

def _get_ssl_context() -> ssl.SSLContext:
    """Create SSL context with system CA bundle for Supabase connections."""
    if certifi is not None:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    else:
        ssl_ctx = ssl.create_default_context()
    return ssl_ctx


# ---------------------------------------------------------------------------
# Client-side channel validation (Issue #74)
# ---------------------------------------------------------------------------

VALID_URL_PATTERN = re.compile(r'^https?://.+')
VALID_CATEGORIES = {
    'News', 'Sports', 'Entertainment', 'Music', 'Kids', 'Documentary',
    'Movies', 'Education', 'Religious', 'Shopping', 'Weather', 'General',
    'Other', 'Culture', 'Lifestyle', 'Business', 'Science', 'Travel',
    'Food', 'Comedy', 'Drama', 'Animation', 'Classic', 'Outdoor', 'Auto',
    'XXX', 'Legislative', 'Series',
}


def _validate_channel(ch: Dict[str, Any]) -> bool:
    """Validate channel data before contributing (Issue #74).

    Returns True if the channel has a valid HTTP(S) URL and a
    reasonably-sized name.  Invalid entries are silently dropped.
    """
    url = ch.get('url', '') or (ch.get('urls', [''])[0] if ch.get('urls') else '')
    if not url or not VALID_URL_PATTERN.match(url):
        return False
    name = ch.get('name', '')
    if not name or len(name) > 200:
        return False
    return True


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def _headers() -> Dict[str, str]:
    return {
        'apikey': _SUPABASE_KEY,
        'Authorization': f'Bearer {_SUPABASE_KEY}',
        'Content-Type': 'application/json',
    }


def is_configured() -> bool:
    return (
        _ENABLED
        and aiohttp is not None
        and _SUPABASE_URL != 'YOUR_SUPABASE_PROJECT_URL'
    )


async def fetch_channels(max_channels: int = 50_000) -> List[Dict[str, Any]]:
    """Fetch all channels from Supabase.

    Returns list of channel dicts with keys: name, urls, url, category,
    country, logo, media_type, source. Returns [] if unavailable.

    Args:
        max_channels: Safety cap to prevent unbounded memory growth.
                      Default 50,000 (~50MB of channel dicts in memory).
    """
    if not is_configured():
        return []

    try:
        url = f'{_SUPABASE_URL}/rest/v1/{_TABLE}?select=*&order=name.asc'
        headers = _headers()
        del headers['Content-Type']  # GET doesn't need it

        channels = []
        offset = 0
        page_size = 1000

        ssl_ctx = _get_ssl_context()
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as session:
            while len(channels) < max_channels:
                page_url = f'{url}&limit={page_size}&offset={offset}'
                async with session.get(
                    page_url, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.warning(f'Supabase channels fetch failed: {resp.status} - {body[:200]}')
                        break

                    data = await resp.json()
                    if not data:
                        break

                    for row in data:
                        urls = row.get('urls', [])
                        if isinstance(urls, str):
                            urls = json.loads(urls)
                        if not urls:
                            continue
                        channels.append({
                            'name': row.get('name', ''),
                            'urls': urls,
                            'url': urls[0] if urls else '',
                            'category': row.get('category', 'Other'),
                            'country': row.get('country', 'Unknown'),
                            'logo': row.get('logo', ''),
                            'media_type': row.get('media_type'),
                            'source': row.get('source', 'supabase'),
                            'working_url_index': 0,
                        })

                    offset += page_size
                    if len(data) < page_size:
                        break

        if len(channels) >= max_channels:
            logger.warning(
                f'Supabase channel fetch capped at {max_channels} '
                f'(more may exist). Increase max_channels if needed.'
            )
        logger.info(f'Fetched {len(channels)} channels from Supabase')
        return channels

    except Exception as e:
        logger.warning(f'Supabase channels fetch error: {e}')
        return []


async def contribute_channels(
    channels: List[Dict[str, Any]],
    source: str = 'iptv-org',
) -> int:
    """Upload new/updated channels to Supabase.

    Performs upsert (insert or update on conflict by url_hash).
    Returns count of channels contributed, or 0 on failure.
    """
    if not is_configured() or not channels:
        return 0

    # Client-side validation and rate limiting (Issue #74)
    channels = [ch for ch in channels if _validate_channel(ch)]
    channels = channels[:100]  # Rate limit: max 100 channels per contribute call

    if not channels:
        return 0

    payload = []
    for ch in channels:
        primary_url = ch.get('url', '')
        if not primary_url:
            urls = ch.get('urls', [])
            primary_url = urls[0] if urls else ''
        if not primary_url:
            continue

        urls = ch.get('urls', [primary_url])
        if isinstance(urls, list) and primary_url not in urls:
            urls = [primary_url] + urls

        # urls must be a list (not pre-serialized string) for jsonb column
        if isinstance(urls, str):
            try:
                urls = json.loads(urls)
            except (json.JSONDecodeError, TypeError):
                urls = [urls]

        payload.append({
            'url_hash': _hash_url(primary_url),
            'name': (ch.get('name') or '')[:200],
            'urls': urls,  # Native list — aiohttp json= serializes correctly for jsonb
            'category': ch.get('category', 'Other'),
            'country': ch.get('country', 'Unknown'),
            'logo': (ch.get('logo') or '')[:500],
            'media_type': ch.get('media_type'),
            'source': source,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    if not payload:
        return 0

    # Upload in batches of 500
    contributed = 0
    batch_size = 500
    try:
        ssl_ctx = _get_ssl_context()
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as session:
            for i in range(0, len(payload), batch_size):
                batch = payload[i:i + batch_size]
                url = f'{_SUPABASE_URL}/rest/v1/{_TABLE}'
                hdrs = _headers()
                hdrs['Prefer'] = 'resolution=merge-duplicates'

                async with session.post(
                    url, json=batch, headers=hdrs,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status in (200, 201):
                        contributed += len(batch)
                    else:
                        body = await resp.text()
                        logger.warning(
                            f'Supabase channel contribute batch failed: '
                            f'{resp.status} - {body[:200]}'
                        )

        if contributed:
            logger.info(f'Contributed {contributed} channels to Supabase')
        return contributed

    except Exception as e:
        logger.warning(f'Supabase channel contribute error: {e}')
        return contributed


async def report_channel(url_hash: str) -> bool:
    """Report a channel as broken. Increments report_count via Supabase REST.

    Since Supabase REST doesn't support atomic increments natively, we fetch
    the current report_count and PATCH with count + 1.

    Args:
        url_hash: SHA-256 hash of the channel's primary URL.

    Returns:
        True if the report was recorded, False on any failure.
    """
    if not is_configured():
        logger.warning('report_channel: Supabase not configured')
        return False

    if not url_hash:
        return False

    try:
        ssl_ctx = _get_ssl_context()
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Step 1: GET current report_count
            get_url = (
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}'
                f'?url_hash=eq.{url_hash}&select=report_count'
            )
            get_headers = _headers()
            get_headers.pop('Content-Type', None)

            async with session.get(
                get_url, headers=get_headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(
                        f'report_channel: GET failed {resp.status} - {body[:200]}'
                    )
                    return False

                rows = await resp.json()
                if not rows:
                    logger.warning(f'report_channel: no channel found for hash {url_hash[:16]}…')
                    return False

                current_count = rows[0].get('report_count', 0) or 0

            # Step 2: PATCH with incremented count
            patch_url = f'{_SUPABASE_URL}/rest/v1/{_TABLE}?url_hash=eq.{url_hash}'
            patch_headers = _headers()
            patch_headers['Prefer'] = 'return=minimal'

            async with session.patch(
                patch_url,
                json={'report_count': current_count + 1},
                headers=patch_headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status in (200, 204):
                    logger.info(
                        f'Reported channel {url_hash[:16]}… '
                        f'(count {current_count} → {current_count + 1})'
                    )
                    return True
                else:
                    body = await resp.text()
                    logger.warning(
                        f'report_channel: PATCH failed {resp.status} - {body[:200]}'
                    )
                    return False

    except Exception as e:
        logger.warning(f'report_channel error: {e}')
        return False


def diff_channels(
    supabase_channels: List[Dict[str, Any]],
    m3u_channels: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Find channels in m3u_channels that are NOT in supabase_channels.

    Comparison is by primary URL hash.
    """
    known_hashes = set()
    for ch in supabase_channels:
        url = ch.get('url', '')
        if url:
            known_hashes.add(_hash_url(url))
        for u in ch.get('urls', []):
            if u:
                known_hashes.add(_hash_url(u))

    new_channels = []
    for ch in m3u_channels:
        url = ch.get('url', '')
        if url and _hash_url(url) not in known_hashes:
            new_channels.append(ch)

    return new_channels
