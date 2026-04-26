#!/usr/bin/env python3
"""
supabase_analytics_report.py — Query Supabase for usage metrics
================================================================

Runs via GitHub Actions (workflow_dispatch) to generate usage reports.

Queries:
  1. Usage by app_version and platform (filtered to MIN_VERSION+)
  2. Most popular channels (channel_play events)
  3. Failed channel reports (report_count distribution)
  4. Active users (unique device_ids)
  5. Geographic distribution
  6. Crash summary

Requires SUPABASE_URL and SUPABASE_ANON_KEY environment variables.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("ERROR: requests required. Run: pip install requests")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
MIN_VERSION = os.environ.get("MIN_VERSION", "2.6.0")
DAYS_BACK = int(os.environ.get("DAYS_BACK", "30"))
REPORT_PATH = "/tmp/analytics-report.json"


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }


def _version_gte(version: str, min_ver: str) -> bool:
    """Compare version strings (e.g., '2.6.3' >= '2.6.0')."""
    try:
        v = tuple(int(x) for x in version.split(".")[:3])
        m = tuple(int(x) for x in min_ver.split(".")[:3])
        return v >= m
    except (ValueError, AttributeError):
        return False


def query_analytics_events(event_type: str | None = None, limit: int = 1000) -> list[dict]:
    """Query analytics_events table with optional event_type filter."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).isoformat()
    url = f"{SUPABASE_URL}/rest/v1/analytics_events"
    params = {
        "created_at": f"gte.{cutoff}",
        "select": "event_type,event_data,app_version,platform,created_at",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    if event_type:
        params["event_type"] = f"eq.{event_type}"

    all_rows = []
    offset = 0
    while offset < 10000:  # Safety cap
        params["offset"] = str(offset)
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        if resp.status_code != 200:
            log.warning("Query failed: %d - %s", resp.status_code, resp.text[:200])
            break
        rows = resp.json()
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < limit:
            break
        offset += limit

    # Filter by version
    filtered = [r for r in all_rows if _version_gte(r.get("app_version", "0"), MIN_VERSION)]
    log.info("Fetched %d %s events (%d after version filter >= %s)",
             len(all_rows), event_type or "all", len(filtered), MIN_VERSION)
    return filtered


def query_channels_reports() -> list[dict]:
    """Query channels table for report_count distribution."""
    url = f"{SUPABASE_URL}/rest/v1/channels"
    params = {
        "report_count": "gte.1",
        "select": "url_hash,name,report_count,country,category",
        "order": "report_count.desc",
        "limit": "100",
    }
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    if resp.status_code != 200:
        log.warning("Channels query failed: %d", resp.status_code)
        return []
    return resp.json()


def build_report() -> dict:
    """Build comprehensive analytics report."""
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "min_version": MIN_VERSION,
        "days_back": DAYS_BACK,
    }

    # 1. App launches by version + platform
    launches = query_analytics_events("app_launch")
    version_platform = {}
    for ev in launches:
        key = f"{ev.get('app_version', '?')} / {ev.get('platform', '?')}"
        version_platform[key] = version_platform.get(key, 0) + 1
    report["app_launches"] = {
        "total": len(launches),
        "by_version_platform": dict(sorted(version_platform.items(), key=lambda x: -x[1])),
    }

    # 2. Active users (unique device_ids from launches)
    device_ids = set()
    for ev in launches:
        ed = ev.get("event_data", {})
        if isinstance(ed, dict):
            did = ed.get("device_id")
            if did:
                device_ids.add(did)
    report["active_users"] = {
        "unique_devices": len(device_ids),
    }

    # 3. Channel plays — most popular
    plays = query_analytics_events("channel_play")
    channel_counts = {}
    for ev in plays:
        ed = ev.get("event_data", {})
        if isinstance(ed, dict):
            name = ed.get("channel_name") or ed.get("name") or "Unknown"
            channel_counts[name] = channel_counts.get(name, 0) + 1
    top_channels = sorted(channel_counts.items(), key=lambda x: -x[1])[:30]
    report["popular_channels"] = {
        "total_plays": len(plays),
        "unique_channels": len(channel_counts),
        "top_30": [{"name": n, "plays": c} for n, c in top_channels],
    }

    # 4. Channel failures
    fails = query_analytics_events("channel_fail")
    fail_counts = {}
    for ev in fails:
        ed = ev.get("event_data", {})
        if isinstance(ed, dict):
            name = ed.get("channel_name") or ed.get("name") or "Unknown"
            fail_counts[name] = fail_counts.get(name, 0) + 1
    top_fails = sorted(fail_counts.items(), key=lambda x: -x[1])[:20]
    report["channel_failures"] = {
        "total_fails": len(fails),
        "top_20_failing": [{"name": n, "fails": c} for n, c in top_fails],
    }

    # 5. Geographic distribution
    country_counts = {}
    for ev in launches:
        ed = ev.get("event_data", {})
        if isinstance(ed, dict):
            country = ed.get("country") or "Unknown"
            country_counts[country] = country_counts.get(country, 0) + 1
    report["geography"] = dict(sorted(country_counts.items(), key=lambda x: -x[1]))

    # 6. Platform distribution
    platform_counts = {}
    for ev in launches:
        platform_counts[ev.get("platform", "?")] = platform_counts.get(ev.get("platform", "?"), 0) + 1
    report["platforms"] = platform_counts

    # 7. Crash summary
    crashes = query_analytics_events("app_crash")
    crash_summary = {}
    for ev in crashes:
        ed = ev.get("event_data", {})
        if isinstance(ed, dict):
            err = ed.get("error_type") or ed.get("error") or "Unknown"
            crash_summary[err[:80]] = crash_summary.get(err[:80], 0) + 1
    report["crashes"] = {
        "total": len(crashes),
        "by_type": dict(sorted(crash_summary.items(), key=lambda x: -x[1])[:15]),
    }

    # 8. Supabase channel reports distribution
    reported = query_channels_reports()
    report["channel_reports"] = {
        "channels_with_reports": len(reported),
        "top_reported": [
            {"name": ch["name"], "reports": ch["report_count"],
             "country": ch.get("country", ""), "category": ch.get("category", "")}
            for ch in reported[:20]
        ],
    }

    # 9. Session durations (from session_end events)
    sessions = query_analytics_events("session_end")
    durations = []
    for ev in sessions:
        ed = ev.get("event_data", {})
        if isinstance(ed, dict):
            dur = ed.get("duration_seconds") or ed.get("session_duration_seconds")
            if dur and isinstance(dur, (int, float)) and dur > 0:
                durations.append(dur)
    if durations:
        durations.sort()
        report["session_duration"] = {
            "count": len(durations),
            "median_seconds": durations[len(durations) // 2],
            "avg_seconds": round(sum(durations) / len(durations), 1),
            "p90_seconds": durations[int(len(durations) * 0.9)] if len(durations) >= 10 else None,
        }
    else:
        report["session_duration"] = {"count": 0}

    return report


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        sys.exit(1)

    log.info("Generating analytics report (version >= %s, last %d days)", MIN_VERSION, DAYS_BACK)
    report = build_report()

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log.info("Report written to %s", REPORT_PATH)

    # Print summary to stdout
    print("\n" + "=" * 60)
    print(f"📊 TV Viewer Analytics Report (>= {MIN_VERSION}, last {DAYS_BACK} days)")
    print("=" * 60)
    print(f"  App launches:     {report['app_launches']['total']}")
    print(f"  Active devices:   {report['active_users']['unique_devices']}")
    print(f"  Channel plays:    {report['popular_channels']['total_plays']}")
    print(f"  Unique channels:  {report['popular_channels']['unique_channels']}")
    print(f"  Crashes:          {report['crashes']['total']}")
    print(f"  Reported broken:  {report['channel_reports']['channels_with_reports']}")
    if report["popular_channels"]["top_30"]:
        print(f"\n  Top channels:")
        for ch in report["popular_channels"]["top_30"][:10]:
            print(f"    {ch['plays']:4d}  {ch['name']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
