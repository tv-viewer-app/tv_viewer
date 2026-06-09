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
ISSUE_LABELS = ('crash', 'bug', 'P1-High')


def log(message):
    """Print status messages safely on UTF-8 and legacy Windows consoles."""
    encoding = sys.stdout.encoding or 'utf-8'
    safe_message = str(message).encode(encoding, errors='replace').decode(encoding, errors='replace')
    print(safe_message)


def query_crashes():
    """Query app_crash events from the last LOOKBACK_HOURS."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        log("ERROR: SUPABASE_URL/SUPABASE_KEY not set")
        sys.exit(1)

    since = (datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    url = f"{SUPABASE_URL}/rest/v1/analytics_events"
    params = {
        'select': 'id,device_id,event_type,event_data,app_version,platform,country,created_at',
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


def parse_event_data(crash):
    """Return crash event_data as a dict regardless of storage shape."""
    data = crash.get('event_data', {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            data = {}
    return data if isinstance(data, dict) else {}


def crash_field(crash, *keys, default='unknown'):
    """Read a field from event_data first, then top-level crash columns."""
    data = parse_event_data(crash)
    for key in keys:
        value = data.get(key)
        if value not in (None, ''):
            return value
    for key in keys:
        value = crash.get(key)
        if value not in (None, ''):
            return value
    return default


def crash_stack(crash):
    """Return the most useful stack trace string available."""
    data = parse_event_data(crash)
    return (
        data.get('stack_trace')
        or data.get('stackTrace')
        or data.get('stack_first_line')
        or data.get('stack')
        or 'No stack trace'
    )


def extract_signature(crash):
    """Extract a deduplication signature from crash event_data."""
    error_type = crash_field(crash, 'error_type', 'error')
    stack = crash_stack(crash)
    error_message = crash_field(crash, 'error_message', 'message', default='')
    first_frame = ''
    if stack and stack != 'No stack trace':
        lines = [l.strip() for l in stack.split('\n') if l.strip() and l.strip().startswith('#')]
        first_frame = lines[0] if lines else stack.split('\n')[0][:100]
    if not first_frame and error_message:
        first_frame = str(error_message).strip()[:100]

    return f"{error_type}|{first_frame}"


def get_existing_crash_issues():
    """Get titles of existing open crash issues."""
    result = subprocess.run(
        ['gh', 'issue', 'list', '--state', 'open', '--search', 'in:title "🐛 Crash:"', '--json', 'title'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return set()
    issues = json.loads(result.stdout or '[]')
    return {i['title'] for i in issues}


def get_issue_labels():
    """Return the subset of desired labels that exist in this repository."""
    result = subprocess.run(
        ['gh', 'label', 'list', '--limit', '200', '--json', 'name'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log('WARNING: Unable to query repository labels; creating issue without labels')
        return []

    available = {
        label['name'].casefold(): label['name']
        for label in json.loads(result.stdout or '[]')
        if label.get('name')
    }
    labels = [available[name.casefold()] for name in ISSUE_LABELS if name.casefold() in available]
    missing = [name for name in ISSUE_LABELS if name.casefold() not in available]
    if missing:
        log(f"WARNING: Missing labels: {', '.join(missing)}")
    return labels


def create_issue(crash_group, issue_labels):
    """Create a GitHub issue for a crash group."""
    sample = crash_group[0]
    data = parse_event_data(sample)
    error_type = crash_field(sample, 'error_type', 'error')
    error_message = crash_field(sample, 'error_message', 'message', default='Unknown error')
    platform = crash_field(sample, 'platform')
    version = crash_field(sample, 'app_version')
    count = len(crash_group)
    stack = crash_stack(sample)
    countries = sorted({c.get('country', 'unknown') for c in crash_group if c.get('country')})

    title = f"🐛 Crash: [{error_type}] on {platform} v{version}"

    body = f"""## Automated Crash Report

**Error:** `{error_type}`
**Message:** {error_message}
**Platform:** {platform}
**Version:** {version}
**Occurrences:** {count} in last {LOOKBACK_HOURS}h
**First seen:** {crash_group[-1].get('created_at', 'unknown')}
**Last seen:** {crash_group[0].get('created_at', 'unknown')}
**Devices affected:** {len(set(c.get('device_id', '') for c in crash_group))}
**Countries:** {', '.join(countries) if countries else 'unknown'}

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

    command = ['gh', 'issue', 'create', '--title', title, '--body', body]
    for label in issue_labels:
        command.extend(['--label', label])
    subprocess.run(command, check=True)
    log(f"  Created issue: {title}")


def main():
    log(f"Checking crashes in last {LOOKBACK_HOURS}h...")
    crashes = query_crashes()

    if not crashes:
        log("No crashes found.")
        return

    log(f"  Found {len(crashes)} crash event(s)")

    # Group by signature
    groups = {}
    for crash in crashes:
        sig = extract_signature(crash)
        groups.setdefault(sig, []).append(crash)

    log(f"  {len(groups)} unique crash signature(s)")

    # Check existing issues
    existing = get_existing_crash_issues()
    issue_labels = get_issue_labels()

    created = 0
    for sig, group in groups.items():
        sample = group[0]
        error_type = crash_field(sample, 'error_type', 'error')
        platform = crash_field(sample, 'platform')
        version = crash_field(sample, 'app_version')

        # Check if issue already exists
        expected_title = f"🐛 Crash: [{error_type}] on {platform} v{version}"
        if expected_title in existing:
            log(f"  Already reported: {expected_title}")
            continue

        create_issue(group, issue_labels)
        created += 1

    log(f"\nDone: {created} new issue(s) created, {len(groups) - created} already tracked")


if __name__ == '__main__':
    main()
