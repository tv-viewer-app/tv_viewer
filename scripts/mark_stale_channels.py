#!/usr/bin/env python3
"""Call the Supabase mark_stale_channels RPC and print a short summary."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    or os.environ.get("SUPABASE_ANON_KEY", "").strip()
)


def main() -> int:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required", file=sys.stderr)
        return 1

    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/rpc/mark_stale_channels",
        data=b"{}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"RPC failed: HTTP {exc.code} - {body[:300]}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"RPC failed: {exc}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(body) if body.strip() else {}
    except json.JSONDecodeError:
        print(f"RPC returned non-JSON response: {body[:300]}", file=sys.stderr)
        return 1

    if isinstance(payload, list):
        payload = payload[0] if payload else {}

    marked = int(payload.get("marked_stale", 0) or 0)
    cleared = int(payload.get("cleared_stale", 0) or 0)
    total = int(payload.get("total_stale", 0) or 0)

    print(f"Marked stale: {marked}")
    print(f"Cleared stale: {cleared}")
    print(f"Total stale: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
