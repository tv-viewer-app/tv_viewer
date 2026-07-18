#!/usr/bin/env python3
"""Device retention report for TV Viewer analytics.

Equivalent SQL:
    SELECT device_id,
           min(created_at::date) AS first_seen,
           max(created_at::date) AS last_seen
    FROM analytics_events
    GROUP BY device_id;
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests required. Run: pip install requests")
    sys.exit(1)


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        with env_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if not os.environ.get(key):
                    os.environ[key] = value
    except OSError:
        pass


_load_env_file()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


def _headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_device_rows(limit: int = 1000) -> list[dict]:
    """Fetch device activity with pagination to avoid sampling bias."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

    url = f"{SUPABASE_URL}/rest/v1/analytics_events"
    params = {
        "select": "device_id,created_at",
        "order": "created_at.asc",
        "limit": str(limit),
    }

    rows: list[dict] = []
    offset = 0
    while offset < 100000:
        params["offset"] = str(offset)
        response = requests.get(url, headers=_headers(), params=params, timeout=30)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < limit:
            break
        offset += limit

    return rows


def build_retention_rows() -> list[dict]:
    devices: dict[str, dict[str, str]] = {}
    for row in fetch_device_rows():
        device_id = row.get("device_id")
        created_at = _parse_date(row.get("created_at", ""))
        if not device_id or not created_at:
            continue

        day = created_at.date().isoformat()
        current = devices.setdefault(device_id, {"device_id": device_id, "first_seen": day, "last_seen": day})
        if day < current["first_seen"]:
            current["first_seen"] = day
        if day > current["last_seen"]:
            current["last_seen"] = day

    return sorted(devices.values(), key=lambda item: (item["first_seen"], item["device_id"]))


def main() -> None:
    rows = build_retention_rows()
    print(json.dumps(rows, indent=2))
    print(f"\nDevices: {len(rows)}")


if __name__ == "__main__":
    main()
