#!/usr/bin/env python3
"""Crash Monitor — Queries analytics for crashes, creates GitHub issues.

Runs daily via GitHub Actions. Deduplicates by crash signature to avoid
flooding the issue tracker with duplicate reports.
"""
import os
import sys
import json
import subprocess
from datetime import datetime, timedelta, timezone

import requests

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
LOOKBACK_HOURS = 48  # Check last 48h to catch weekend crashes on Monday


def query_crashes():
    """Query app_crash events from the last LOOKBACK_HOURS."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE_URL/SUPABASE_KEY not set")
        sys.exit(1)

    since = (datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    url = f"{SUPABASE_URL}/rest/v1/analytics_events"
    params = {
        'select': 'id,created_at,event_type,event_data,device_id,app_version,platform',
        'event_type': 'eq.app_crash',
        'created_at': f'gte.{since}',
        'order': 'created_at.desc',
        'limit': '50',
    }
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def extract_signature(crash):
    """Extract a deduplication signature from crash event_data."""
    data = crash.get('event_data', {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            data = {}

    error_type = data.get('error_type', data.get('error', 'unknown'))
    # Use first line of stack trace + error type as signature
    stack = data.get('stack_trace', data.get('stackTrace', ''))
    first_frame = ''
    if stack:
        lines = [l.strip() for l in stack.split('\n') if l.strip() and l.strip().startswith('#')]
        first_frame = lines[0] if lines else stack.split('\n')[0][:100]

    return f"{error_type}|{first_frame}"


def get_existing_crash_issues():
    """Get titles of existing open crash issues."""
    result = subprocess.run(
        ['gh', 'issue', 'list', '--label', 'crash', '--state', 'open', '--json', 'title'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return set()
    issues = json.loads(result.stdout or '[]')
    return {i['title'] for i in issues}


def create_issue(crash_group):
    """Create a GitHub issue for a crash group."""
    sample = crash_group[0]
    data = sample.get('event_data', {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            data = {}

    error_type = data.get('error_type', data.get('error', 'unknown'))
    platform = sample.get('platform', 'unknown')
    version = sample.get('app_version', 'unknown')
    count = len(crash_group)
    stack = data.get('stack_trace', data.get('stackTrace', 'No stack trace'))

    title = f"🐛 Crash: [{error_type}] on {platform} v{version}"

    body = f"""## Automated Crash Report

**Error:** `{error_type}`
**Platform:** {platform}
**Version:** {version}
**Occurrences:** {count} in last {LOOKBACK_HOURS}h
**First seen:** {crash_group[-1].get('created_at', 'unknown')}
**Last seen:** {crash_group[0].get('created_at', 'unknown')}
**Devices affected:** {len(set(c.get('device_id', '') for c in crash_group))}

### Stack Trace
```
{stack[:3000]}
```

### Event Data
```json
{json.dumps(data, indent=2, default=str)[:2000]}
```

---
*Auto-created by Crash Monitor workflow. Close when fixed.*
"""

    subprocess.run(
        ['gh', 'issue', 'create',
         '--title', title,
         '--body', body,
         '--label', 'crash,bug,P1-High'],
        check=True
    )
    print(f"  ✅ Created issue: {title}")


def main():
    print(f"🔍 Checking crashes in last {LOOKBACK_HOURS}h...")
    crashes = query_crashes()

    if not crashes:
        print("✅ No crashes found!")
        return

    print(f"  Found {len(crashes)} crash event(s)")

    # Group by signature
    groups = {}
    for crash in crashes:
        sig = extract_signature(crash)
        groups.setdefault(sig, []).append(crash)

    print(f"  {len(groups)} unique crash signature(s)")

    # Check existing issues
    existing = get_existing_crash_issues()

    created = 0
    for sig, group in groups.items():
        sample = group[0]
        data = sample.get('event_data', {})
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                data = {}
        error_type = data.get('error_type', data.get('error', 'unknown'))
        platform = sample.get('platform', 'unknown')
        version = sample.get('app_version', 'unknown')

        # Check if issue already exists
        expected_title = f"🐛 Crash: [{error_type}] on {platform} v{version}"
        if expected_title in existing:
            print(f"  ⏭️  Already reported: {expected_title}")
            continue

        create_issue(group)
        created += 1

    print(f"\n{'✅' if created == 0 else '📝'} Done: {created} new issue(s) created, {len(groups) - created} already tracked")


if __name__ == '__main__':
    main()
