#!/usr/bin/env python3
"""TV Viewer Analytics Dashboard — Query Supabase analytics_events table.

Usage:
    python scripts/analytics_dashboard.py              # Full dashboard
    python scripts/analytics_dashboard.py --crashes    # Crash details only
    python scripts/analytics_dashboard.py --top        # Top channels only
    python scripts/analytics_dashboard.py --raw        # Raw recent events

Requires SUPABASE_URL and SUPABASE_ANON_KEY environment variables.
Auto-loads from .env file in project root if env vars are not set.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Run: pip install requests")
    sys.exit(1)


def _load_env_file():
    """Auto-load Supabase credentials from .env file if env vars are not set.

    Looks for .env in the project root (parent of scripts/).
    Only sets variables that are not already in the environment.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Strip surrounding quotes
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                # Only set if not already in environment (env vars take precedence)
                if key not in os.environ or not os.environ[key]:
                    os.environ[key] = value
    except Exception:
        pass  # Silently ignore .env parse errors — fall through to env var check


# Auto-load .env before reading credentials
_load_env_file()

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
TABLE = 'analytics_events'


def _headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'count=exact',
    }


def _query(params: str, limit: int = 1000) -> list:
    """Query Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?{params}&limit={limit}"
    resp = requests.get(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def _query_count(params: str) -> int:
    """Get count of matching rows."""
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?{params}&limit=1"
    headers = _headers()
    headers['Prefer'] = 'count=exact'
    headers['Range-Unit'] = 'items'
    headers['Range'] = '0-0'
    resp = requests.get(url, headers=headers, timeout=15)
    count_header = resp.headers.get('content-range', '*/0')
    return int(count_header.split('/')[-1])


def print_header(title: str):
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def print_section(title: str):
    print(f"\n--- {title} ---")


def dashboard_summary():
    """Show overall analytics summary."""
    print_header("TV Viewer Analytics Dashboard")
    print(f"  Supabase: {SUPABASE_URL}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Total events
    total = _query_count("select=id")
    print(f"\n  Total events: {total:,}")

    # Events by type
    print_section("Events by Type")
    events = _query("select=event_type&order=event_type", limit=10000)
    type_counts = {}
    for e in events:
        t = e.get('event_type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        bar = '█' * min(c // max(total // 40, 1), 40) if total > 0 else ''
        print(f"  {t:<20} {c:>6,}  {bar}")

    # Unique devices
    devices = _query("select=device_id", limit=50000)
    unique_devices = len(set(e.get('device_id', '') for e in devices))
    print(f"\n  Unique devices: {unique_devices:,}")

    # Platform breakdown
    print_section("Platform Breakdown")
    platforms = {}
    for e in devices:
        # We only have device_id here, need event_data for platform
        pass
    platform_events = _query("select=platform", limit=50000)
    for e in platform_events:
        p = e.get('platform', 'unknown')
        platforms[p] = platforms.get(p, 0) + 1
    for p, c in sorted(platforms.items(), key=lambda x: -x[1]):
        pct = (c / total * 100) if total > 0 else 0
        print(f"  {p:<15} {c:>6,}  ({pct:.1f}%)")

    # Last 24h activity
    since = (datetime.utcnow() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
    recent_count = _query_count(f"select=id&created_at=gte.{since}")
    print(f"\n  Events (last 24h): {recent_count:,}")

    # App version distribution
    print_section("App Version Distribution")
    versions = _query("select=app_version", limit=50000)
    ver_counts = {}
    for e in versions:
        v = e.get('app_version', 'unknown')
        ver_counts[v] = ver_counts.get(v, 0) + 1
    for v, c in sorted(ver_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  v{v:<12} {c:>6,}")


def show_crashes():
    """Show crash/error details."""
    print_header("Crash & Error Report")

    crashes = _query(
        "select=*&event_type=eq.app_crash&order=created_at.desc",
        limit=50
    )

    if not crashes:
        print("  No crashes recorded. ✅")
        return

    print(f"  Total crash events: {len(crashes)}")

    # Group by error type
    error_types = {}
    for c in crashes:
        data = c.get('event_data', {})
        if isinstance(data, str):
            data = json.loads(data)
        etype = data.get('error_type', 'Unknown')
        error_types.setdefault(etype, []).append(c)

    print_section("Crash Types")
    for etype, events in sorted(error_types.items(), key=lambda x: -len(x[1])):
        print(f"\n  [{etype}] — {len(events)} occurrences")
        for e in events[:3]:
            data = e.get('event_data', {})
            if isinstance(data, str):
                data = json.loads(data)
            ts = e.get('created_at', '?')[:19]
            msg = data.get('error_message', 'N/A')[:80]
            stack = data.get('stack_first_line', '')[:60]
            platform = e.get('platform', '?')
            version = e.get('app_version', '?')
            print(f"    {ts}  [{platform} v{version}]")
            print(f"      {msg}")
            if stack:
                print(f"      @ {stack}")

    # Channel failures
    print_section("Channel Play Failures (last 50)")
    failures = _query(
        "select=*&event_type=eq.channel_fail&order=created_at.desc",
        limit=50
    )
    if failures:
        error_codes = {}
        for f in failures:
            data = f.get('event_data', {})
            if isinstance(data, str):
                data = json.loads(data)
            code = data.get('error_code', 'unknown')
            error_codes[code] = error_codes.get(code, 0) + 1
        for code, count in sorted(error_codes.items(), key=lambda x: -x[1]):
            print(f"  {code:<30} {count:>4}")
    else:
        print("  No channel failures recorded.")


def show_top_channels():
    """Show most played channels."""
    print_header("Top Channels (by play count)")

    plays = _query(
        "select=event_data&event_type=eq.channel_play",
        limit=50000
    )

    if not plays:
        print("  No play events recorded.")
        return

    url_counts = {}
    for p in plays:
        data = p.get('event_data', {})
        if isinstance(data, str):
            data = json.loads(data)
        url_hash = data.get('url_hash', 'unknown')
        url_counts[url_hash] = url_counts.get(url_hash, 0) + 1

    print(f"  Total plays: {len(plays):,}")
    print(f"  Unique channels: {len(url_counts):,}")
    print()
    print(f"  {'Rank':<6} {'URL Hash (SHA256)':<20} {'Plays':>8}")
    print(f"  {'─'*6} {'─'*20} {'─'*8}")
    for i, (h, c) in enumerate(sorted(url_counts.items(), key=lambda x: -x[1])[:20], 1):
        print(f"  {i:<6} {h[:18]+'..':.<20} {c:>8,}")


def show_scan_stats():
    """Show scan statistics."""
    print_header("Scan Statistics")

    scans = _query(
        "select=*&event_type=eq.scan_complete&order=created_at.desc",
        limit=100
    )

    if not scans:
        print("  No scan events recorded.")
        return

    print(f"  Total scans: {len(scans)}")
    total_working = 0
    total_failed = 0
    total_duration = 0
    for s in scans:
        data = s.get('event_data', {})
        if isinstance(data, str):
            data = json.loads(data)
        total_working += data.get('working_count', 0)
        total_failed += data.get('failed_count', 0)
        total_duration += data.get('duration_ms', 0)

    avg_working = total_working / len(scans) if scans else 0
    avg_failed = total_failed / len(scans) if scans else 0
    avg_duration = total_duration / len(scans) / 1000 if scans else 0

    print(f"  Avg working channels: {avg_working:.0f}")
    print(f"  Avg failed channels:  {avg_failed:.0f}")
    print(f"  Avg scan duration:    {avg_duration:.1f}s")

    print_section("Recent Scans")
    for s in scans[:10]:
        data = s.get('event_data', {})
        if isinstance(data, str):
            data = json.loads(data)
        ts = s.get('created_at', '?')[:19]
        w = data.get('working_count', 0)
        f = data.get('failed_count', 0)
        d = data.get('duration_ms', 0) / 1000
        platform = s.get('platform', '?')
        print(f"  {ts}  [{platform}]  ✓{w} ✗{f}  ({d:.1f}s)")


def show_raw_events():
    """Show raw recent events."""
    print_header("Recent Events (last 30)")

    events = _query("select=*&order=created_at.desc", limit=30)

    for e in events:
        ts = e.get('created_at', '?')[:19]
        etype = e.get('event_type', '?')
        platform = e.get('platform', '?')
        version = e.get('app_version', '?')
        device = e.get('device_id', '?')[:8]
        data = e.get('event_data', {})
        if isinstance(data, str):
            data = json.loads(data)
        data_str = json.dumps(data)[:60] if data else ''
        print(f"  {ts}  {etype:<16} [{platform} v{version}] dev:{device}  {data_str}")


def main():
    parser = argparse.ArgumentParser(description='TV Viewer Analytics Dashboard')
    parser.add_argument('--crashes', action='store_true', help='Show crash details')
    parser.add_argument('--top', action='store_true', help='Show top channels')
    parser.add_argument('--scans', action='store_true', help='Show scan statistics')
    parser.add_argument('--raw', action='store_true', help='Show raw recent events')
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
        print()
        print("  Option 1 — Run the setup script (creates .env automatically):")
        print("    python scripts/supabase_setup.py")
        print()
        print("  Option 2 — Set environment variables manually:")
        print("    $env:SUPABASE_URL = 'https://your-project.supabase.co'")
        print("    $env:SUPABASE_ANON_KEY = 'your-anon-key'")
        print()
        print("  Option 3 — Create .env file in project root:")
        print("    SUPABASE_URL=https://your-project.supabase.co")
        print("    SUPABASE_ANON_KEY=your-anon-key")
        sys.exit(1)

    try:
        if args.crashes:
            show_crashes()
        elif args.top:
            show_top_channels()
        elif args.scans:
            show_scan_stats()
        elif args.raw:
            show_raw_events()
        else:
            dashboard_summary()
            show_top_channels()
            show_scan_stats()
            show_crashes()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Supabase. Check SUPABASE_URL.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Supabase API error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
