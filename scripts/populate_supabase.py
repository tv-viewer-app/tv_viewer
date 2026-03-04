#!/usr/bin/env python3
"""Populate Supabase channels + channel_status tables.

Fetches from ALL configured M3U repos, consolidates multi-URL channels,
checks stream health, and uploads to Supabase. Both Windows and Android
apps will then read from the same database.

Usage:
    python scripts/populate_supabase.py [--skip-health] [--dry-run]
"""

import asyncio
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import config
from utils.helpers import parse_m3u
from core.channel_manager import consolidate_channels

SUPABASE_URL = config.SUPABASE_URL
SUPABASE_KEY = config.SUPABASE_ANON_KEY

# Unified repo list (same as channels_config.json + custom channels)
def load_repos():
    """Load repos from channels_config.json."""
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'channels_config.json')
    with open(cfg_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    repos = data.get('repositories', [])
    custom = data.get('custom_channels', [])
    return repos, custom


def hash_url(url: str) -> str:
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def headers(upsert=False):
    h = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
    }
    if upsert:
        h['Prefer'] = 'resolution=merge-duplicates'
    return h


async def fetch_m3u(session: aiohttp.ClientSession, url: str) -> List[Dict]:
    """Fetch and parse a single M3U URL."""
    try:
        async with session.get(
            url,
            headers={'User-Agent': 'TV Viewer/2.2.3 ChannelPopulator'},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                print(f"  ✗ {url[:60]}... HTTP {resp.status}")
                return []
            content = await resp.text(errors='replace')
            if len(content) > 50 * 1024 * 1024:
                print(f"  ✗ {url[:60]}... too large ({len(content)} bytes)")
                return []
            channels = parse_m3u(content)
            print(f"  ✓ {url[:60]}... {len(channels)} channels")
            return channels
    except Exception as e:
        print(f"  ✗ {url[:60]}... {type(e).__name__}: {e}")
        return []


async def check_stream(session: aiohttp.ClientSession, url: str) -> Dict:
    """Check if a stream URL is accessible. Returns health info."""
    start = time.monotonic()
    try:
        async with session.head(
            url,
            headers={'User-Agent': 'TV Viewer/2.2.3 HealthCheck'},
            timeout=aiohttp.ClientTimeout(total=8),
            allow_redirects=True,
        ) as resp:
            elapsed = int((time.monotonic() - start) * 1000)
            is_ok = resp.status in (200, 206, 302, 301)
            return {
                'url_hash': hash_url(url),
                'status': 'working' if is_ok else 'failed',
                'last_checked': datetime.now(timezone.utc).isoformat(),
                'response_time_ms': elapsed,
            }
    except Exception:
        elapsed = int((time.monotonic() - start) * 1000)
        return {
            'url_hash': hash_url(url),
            'status': 'failed',
            'last_checked': datetime.now(timezone.utc).isoformat(),
            'response_time_ms': elapsed,
        }


async def upload_channels(session: aiohttp.ClientSession, channels: List[Dict]) -> int:
    """Upload consolidated channels to Supabase channels table."""
    payload = []
    for ch in channels:
        primary_url = ch.get('url', '')
        urls = ch.get('urls', [primary_url])
        if isinstance(urls, str):
            try:
                urls = json.loads(urls)
            except (json.JSONDecodeError, TypeError):
                urls = [urls]
        if not primary_url and urls:
            primary_url = urls[0]
        if not primary_url:
            continue
        if primary_url not in urls:
            urls = [primary_url] + urls

        payload.append({
            'url_hash': hash_url(primary_url),
            'name': (ch.get('name') or '')[:200],
            'urls': urls,
            'category': ch.get('category', 'Other'),
            'country': ch.get('country', 'Unknown'),
            'logo': (ch.get('logo') or '')[:500],
            'media_type': ch.get('media_type'),
            'source': ch.get('source', 'iptv-org'),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    uploaded = 0
    batch_size = 500
    for i in range(0, len(payload), batch_size):
        batch = payload[i:i + batch_size]
        url = f'{SUPABASE_URL}/rest/v1/channels'
        try:
            async with session.post(url, json=batch, headers=headers(upsert=True),
                                    timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status in (200, 201):
                    uploaded += len(batch)
                    print(f"  ✓ Uploaded channels batch {i//batch_size + 1}: {len(batch)} rows")
                else:
                    body = await resp.text()
                    print(f"  ✗ Channel batch failed: {resp.status} - {body[:200]}")
        except Exception as e:
            print(f"  ✗ Channel batch error: {e}")

    return uploaded


async def upload_status(session: aiohttp.ClientSession, statuses: List[Dict]) -> int:
    """Upload health check results to Supabase channel_status table."""
    uploaded = 0
    batch_size = 500
    for i in range(0, len(statuses), batch_size):
        batch = statuses[i:i + batch_size]
        url = f'{SUPABASE_URL}/rest/v1/channel_status'
        try:
            async with session.post(url, json=batch, headers=headers(upsert=True),
                                    timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status in (200, 201):
                    uploaded += len(batch)
                    print(f"  ✓ Uploaded status batch {i//batch_size + 1}: {len(batch)} rows")
                else:
                    body = await resp.text()
                    print(f"  ✗ Status batch failed: {resp.status} - {body[:200]}")
        except Exception as e:
            print(f"  ✗ Status batch error: {e}")

    return uploaded


async def main():
    skip_health = '--skip-health' in sys.argv
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("TV Viewer — Supabase Channel Population Script")
    print("=" * 60)

    # 1. Load repos and custom channels
    repos, custom_channels = load_repos()
    print(f"\n[1/5] Loaded {len(repos)} repositories, {len(custom_channels)} custom channels")

    # 2. Fetch from all repos
    print(f"\n[2/5] Fetching channels from {len(repos)} repositories...")
    all_channels = []
    seen_urls = set()

    async with aiohttp.ClientSession() as session:
        # Fetch repos with concurrency limit
        sem = asyncio.Semaphore(10)

        async def fetch_with_sem(url):
            async with sem:
                return await fetch_m3u(session, url)

        results = await asyncio.gather(*[fetch_with_sem(u) for u in repos], return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            for ch in result:
                url = ch.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_channels.append(ch)

        # Add custom channels
        for ch in custom_channels:
            url = ch.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_channels.append(ch)

    print(f"\n  Total unique channels (pre-consolidation): {len(all_channels)}")

    # 3. Consolidate
    print(f"\n[3/5] Consolidating channels...")
    consolidated = consolidate_channels(all_channels)
    multi_url = sum(1 for ch in consolidated if len(ch.get('urls', [ch.get('url', '')])) > 1)
    print(f"  Consolidated: {len(all_channels)} → {len(consolidated)} channels")
    print(f"  Multi-source channels: {multi_url}")

    # Count by country
    countries = {}
    for ch in consolidated:
        c = ch.get('country', 'Unknown')
        countries[c] = countries.get(c, 0) + 1
    top_countries = sorted(countries.items(), key=lambda x: -x[1])[:10]
    print(f"  Top countries: {', '.join(f'{c}:{n}' for c, n in top_countries)}")

    if dry_run:
        print("\n[DRY RUN] Skipping upload.")
        return

    # 4. Upload channels to Supabase
    print(f"\n[4/5] Uploading {len(consolidated)} channels to Supabase...")
    async with aiohttp.ClientSession() as session:
        uploaded_ch = await upload_channels(session, consolidated)
    print(f"  Uploaded: {uploaded_ch} channels")

    # 5. Health check + upload status
    if skip_health:
        print(f"\n[5/5] Skipping health checks (--skip-health)")
    else:
        # Collect all unique URLs for health checking
        all_urls = set()
        for ch in consolidated:
            urls = ch.get('urls', [ch.get('url', '')])
            for u in urls:
                if u:
                    all_urls.add(u)

        print(f"\n[5/5] Checking health of {len(all_urls)} unique URLs...")
        statuses = []
        sem = asyncio.Semaphore(50)  # 50 concurrent health checks

        async with aiohttp.ClientSession() as session:
            async def check_with_sem(url):
                async with sem:
                    return await check_stream(session, url)

            results = await asyncio.gather(
                *[check_with_sem(u) for u in all_urls],
                return_exceptions=True
            )

            for r in results:
                if isinstance(r, dict):
                    statuses.append(r)

            working = sum(1 for s in statuses if s['status'] == 'working')
            failed = sum(1 for s in statuses if s['status'] == 'failed')
            print(f"  Health results: {working} working, {failed} failed")

            # Upload status
            uploaded_st = await upload_status(session, statuses)
            print(f"  Uploaded: {uploaded_st} status records")

    print("\n" + "=" * 60)
    print("✓ Population complete!")
    print(f"  Channels: {uploaded_ch}")
    if not skip_health:
        print(f"  Health records: {uploaded_st}")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
