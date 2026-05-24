#!/usr/bin/env python3
"""Supabase monitoring helper — runs read-only telemetry queries.

Designed to be invoked from a GitHub Actions workflow (or locally) using a
*service-role* key that lives in repo secrets. Never echoes the key.

Env:
  SUPABASE_URL                — project REST URL
  SUPABASE_SERVICE_ROLE_KEY   — sb_secret_… key (read + bypass-RLS)

CLI:
  python scripts/supabase_monitor.py <query> [--hours N] [--limit N] [--version V]

Supported queries:
  health         — schema version + table row counts + cleanup age
  events         — recent events grouped by (event_type, app_version, platform)
  errors         — recent client_error / server_error rows with full payload
  version        — adoption: events grouped by app_version (last N hours)
  devices        — unique device counts by platform / app_version
  v_recent       — raw recent events for a specific app version (--version 2.16.2)
  app_launches   — app_launch events with platform/version
  channel_plays  — channel_play events ordered by most-played channel

All queries default to last 24 hours unless --hours is given.
"""

from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error
from typing import Any

# Force UTF-8 stdout on Windows consoles so the box-drawing chars render.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get(
    "SUPABASE_KEY", ""
)
UA = "tv-viewer-monitor/1.0"


def _die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


if not URL or not KEY:
    _die("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in the environment.")


def _get(path: str) -> Any:
    req = urllib.request.Request(
        f"{URL}{path}",
        headers={
            "apikey": KEY,
            "Authorization": f"Bearer {KEY}",
            "Accept": "application/json",
            "User-Agent": UA,
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        _die(f"HTTP {e.code} on {path}: {body[:300]}")
    try:
        return json.loads(body)
    except Exception:
        _die(f"Non-JSON response on {path}: {body[:200]}")


def _post_rpc(name: str, payload: dict | None = None) -> Any:
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        f"{URL}/rest/v1/rpc/{name}",
        data=data,
        headers={
            "apikey": KEY,
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": UA,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode("utf-8", errors="replace")[:300]}
    try:
        return json.loads(body) if body.strip() else None
    except Exception:
        return body


def _since(hours: int) -> str:
    return (
        _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=hours)
    ).isoformat()


def _events(hours: int, extra_filter: str = "", limit: int = 1000) -> list[dict]:
    qs = {
        "select": "created_at,event_type,app_version,platform,device_id,event_data",
        "created_at": f"gte.{_since(hours)}",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    base = f"/rest/v1/analytics_events?{urllib.parse.urlencode(qs)}"
    if extra_filter:
        base += f"&{extra_filter}"
    rows = _get(base)
    return rows if isinstance(rows, list) else []


def q_health() -> None:
    schema = _post_rpc("tv_viewer_schema_version")
    if isinstance(schema, list) and schema:
        schema = schema[0]
    print("── Schema ──")
    print(f"  version: {schema}")

    # Row counts via PostgREST count header
    def _count(path: str) -> str:
        req = urllib.request.Request(
            f"{URL}{path}",
            headers={
                "apikey": KEY,
                "Authorization": f"Bearer {KEY}",
                "Prefer": "count=exact",
                "Range-Unit": "items",
                "Range": "0-0",
                "User-Agent": UA,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                cr = resp.headers.get("content-range", "*/?")
        except urllib.error.HTTPError as e:
            cr = e.headers.get("content-range", "?") if e.headers else "?"
        return cr.split("/")[-1]

    print("\n── Row counts ──")
    print(f"  analytics_events : {_count('/rest/v1/analytics_events?select=id')}")
    print(f"  channel_status   : {_count('/rest/v1/channel_status?select=url_hash')}")
    print(f"  channel_votes    : {_count('/rest/v1/channel_votes?select=url_hash')}")

    print("\n── Activity (24h) ──")
    rows = _events(24, limit=10000)
    devs = {r["device_id"] for r in rows if r.get("device_id")}
    print(f"  events       : {len(rows)}")
    print(f"  unique devs  : {len(devs)}")


def q_events(hours: int) -> None:
    rows = _events(hours, limit=5000)
    c = collections.Counter(
        (r.get("event_type", "?"), r.get("app_version", "?"), r.get("platform", "?"))
        for r in rows
    )
    print(f"── Events grouped (last {hours}h, {len(rows)} total) ──")
    print(f"  {'count':>5}  {'event_type':<22}  {'version':<10}  platform")
    for (et, ver, plat), n in c.most_common(40):
        print(f"  {n:>5}  {et:<22}  {ver:<10}  {plat}")


def q_errors(hours: int, limit: int) -> None:
    qs = {
        "select": "created_at,platform,app_version,device_id,event_type,event_data",
        "event_type": "in.(client_error,server_error)",
        "created_at": f"gte.{_since(hours)}",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    rows = _get(f"/rest/v1/analytics_events?{urllib.parse.urlencode(qs)}")
    print(f"── Errors (last {hours}h) — {len(rows)} rows ──")
    if not rows:
        print("  none ✓")
        return
    # Group by error_type + context
    groups: dict[tuple, list[dict]] = collections.defaultdict(list)
    for r in rows:
        d = r.get("event_data") or {}
        groups[(d.get("error_type", "?"), d.get("context", "?"))].append(r)
    print(f"\n  {'count':>5}  {'error_type':<28}  context")
    for (et, ctx), grp in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(grp):>5}  {et:<28}  {ctx}")
    print("\n── Most recent 5 ──")
    for r in rows[:5]:
        d = r.get("event_data") or {}
        print(
            f"  {r['created_at']}  {r.get('platform'):<8}  "
            f"v{r.get('app_version','?'):<8}  "
            f"{d.get('severity','?'):<8}  "
            f"{d.get('error_type','?')}: "
            f"{(d.get('error_message') or '')[:90]}"
        )
        if d.get("stack_top"):
            print(f"      └ {d['stack_top']}")


def q_version(hours: int) -> None:
    rows = _events(hours, limit=10000)
    by_ver = collections.Counter(
        (r.get("app_version", "?"), r.get("platform", "?")) for r in rows
    )
    devs_by_ver: dict[tuple, set] = collections.defaultdict(set)
    for r in rows:
        if r.get("device_id"):
            devs_by_ver[(r.get("app_version", "?"), r.get("platform", "?"))].add(
                r["device_id"]
            )
    print(f"── Version adoption (last {hours}h) ──")
    print(f"  {'events':>6}  {'devices':>7}  {'version':<10}  platform")
    for (ver, plat), n in by_ver.most_common(30):
        d = len(devs_by_ver.get((ver, plat), ()))
        print(f"  {n:>6}  {d:>7}  {ver:<10}  {plat}")


def q_devices(hours: int) -> None:
    rows = _events(hours, limit=10000)
    by_plat: dict[str, set] = collections.defaultdict(set)
    for r in rows:
        if r.get("device_id"):
            by_plat[r.get("platform", "?")].add(r["device_id"])
    print(f"── Unique devices (last {hours}h) ──")
    for plat, ids in sorted(by_plat.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(ids):>5}  {plat}")
    print(f"  {sum(len(v) for v in by_plat.values()):>5}  TOTAL")


def q_v_recent(hours: int, version: str, limit: int) -> None:
    if not version:
        _die("--version is required for v_recent")
    qs = {
        "select": "created_at,event_type,platform,device_id,event_data",
        "app_version": f"like.{version}*",
        "created_at": f"gte.{_since(hours)}",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    rows = _get(f"/rest/v1/analytics_events?{urllib.parse.urlencode(qs)}")
    print(f"── v{version}* recent ({len(rows)} rows, last {hours}h) ──")
    for r in rows:
        d = r.get("event_data") or {}
        snippet = (
            d.get("feature")
            or d.get("category")
            or d.get("error_type")
            or d.get("country")
            or ""
        )
        dev = (r.get("device_id") or "?")[:8]
        print(
            f"  {r['created_at']}  {r.get('platform'):<8}  "
            f"{dev}  {r.get('event_type'):<20}  {snippet}"
        )


def q_app_launches(hours: int) -> None:
    qs = {
        "select": "created_at,platform,app_version,device_id",
        "event_type": "eq.app_launch",
        "created_at": f"gte.{_since(hours)}",
        "order": "created_at.desc",
        "limit": "500",
    }
    rows = _get(f"/rest/v1/analytics_events?{urllib.parse.urlencode(qs)}")
    print(f"── app_launch events (last {hours}h) — {len(rows)} ──")
    devs = collections.Counter(
        (r.get("platform", "?"), r.get("app_version", "?"))
        for r in rows
    )
    for (plat, ver), n in devs.most_common(20):
        print(f"  {n:>4}  {plat:<10}  v{ver}")


def q_channel_plays(hours: int) -> None:
    qs = {
        "select": "event_data,platform,app_version",
        "event_type": "eq.channel_play",
        "created_at": f"gte.{_since(hours)}",
        "limit": "5000",
    }
    rows = _get(f"/rest/v1/analytics_events?{urllib.parse.urlencode(qs)}")
    by_cat = collections.Counter()
    by_country = collections.Counter()
    for r in rows:
        d = r.get("event_data") or {}
        by_cat[d.get("category", "?")] += 1
        by_country[d.get("country", "?")] += 1
    print(f"── channel_play (last {hours}h) — {len(rows)} plays ──")
    print("\n  Top categories:")
    for cat, n in by_cat.most_common(10):
        print(f"    {n:>4}  {cat}")
    print("\n  Top countries:")
    for co, n in by_country.most_common(10):
        print(f"    {n:>4}  {co}")


def _error_signature(event_data: dict) -> str:
    """Stable signature for grouping/dedup. Combines error_type + cleaned message.

    The message can contain noisy bits (URLs, timestamps, IDs); we keep a
    short, normalized prefix. Same signature across releases = same bug.
    """
    et = (event_data.get("error_type") or "UnknownError").strip()
    msg = (event_data.get("error_message") or "").strip()
    # Strip URLs, hex IDs, timestamps to keep signature stable.
    import re
    msg = re.sub(r"https?://\S+", "<url>", msg)
    msg = re.sub(r"\b[0-9a-f]{8,}\b", "<hex>", msg, flags=re.I)
    msg = re.sub(r"\b\d{4}-\d{2}-\d{2}T?\S*\b", "<ts>", msg)
    msg = re.sub(r"\s+", " ", msg)[:120]
    return f"{et}::{msg}"


def q_weekly_pulse(hours: int) -> None:
    """L4 — Weekly Pulse. Multi-section markdown-friendly report for humans.

    Designed to be captured as workflow step output and committed to
    docs/pulse/YYYY-WW.md by the weekly-pulse.yml workflow.
    """
    print(f"# Weekly Pulse — last {hours}h")
    print()

    rows = _events(hours, limit=50000)
    devs = {r["device_id"] for r in rows if r.get("device_id")}
    print(f"- **Events:** {len(rows):,}")
    print(f"- **Unique devices:** {len(devs):,}")
    print()

    # Health: error rate
    errs = [r for r in rows if r.get("event_type") in ("client_error", "server_error")]
    play_count = sum(1 for r in rows if r.get("event_type") == "channel_play")
    err_rate = (len(errs) / max(len(rows), 1)) * 100
    print(f"- **Errors:** {len(errs)} ({err_rate:.2f}% of events)")
    print(f"- **Channel plays:** {play_count:,}")
    print()

    # Version adoption
    print("## Version adoption (by unique device)")
    devs_by_ver: dict[tuple, set] = collections.defaultdict(set)
    for r in rows:
        if r.get("device_id"):
            devs_by_ver[(r.get("platform", "?"), r.get("app_version", "?"))].add(
                r["device_id"]
            )
    print()
    print("| Platform | Version | Devices |")
    print("|---|---|---|")
    for (plat, ver), ids in sorted(devs_by_ver.items(), key=lambda kv: -len(kv[1]))[:20]:
        print(f"| {plat} | v{ver} | {len(ids)} |")
    print()

    # Top errors grouped by signature
    print("## Top error signatures")
    sigs: dict[str, list[dict]] = collections.defaultdict(list)
    for r in errs:
        sigs[_error_signature(r.get("event_data") or {})].append(r)
    print()
    if not sigs:
        print("_No errors in window._ ✓")
    else:
        print("| Count | Platforms | Versions | Signature |")
        print("|---|---|---|---|")
        for sig, grp in sorted(sigs.items(), key=lambda kv: -len(kv[1]))[:15]:
            plats = ",".join(sorted({(r.get("platform") or "?") for r in grp}))
            vers = ",".join(sorted({(r.get("app_version") or "?") for r in grp}))
            # Escape pipes in signature for markdown table
            safe_sig = sig.replace("|", "\\|")[:120]
            print(f"| {len(grp)} | {plats} | {vers} | `{safe_sig}` |")
    print()

    # Top channels played
    print("## Top channels played")
    plays = [r for r in rows if r.get("event_type") == "channel_play"]
    by_channel: collections.Counter = collections.Counter()
    by_cat: collections.Counter = collections.Counter()
    by_country: collections.Counter = collections.Counter()
    for r in plays:
        d = r.get("event_data") or {}
        if d.get("channel_name"):
            by_channel[d["channel_name"]] += 1
        if d.get("category"):
            by_cat[d["category"]] += 1
        if d.get("country"):
            by_country[d["country"]] += 1
    print()
    if not by_channel:
        print("_No channel plays in window._")
    else:
        print("| Plays | Channel |")
        print("|---|---|")
        for name, n in by_channel.most_common(15):
            print(f"| {n} | {name} |")
    print()

    # Categories + countries
    if by_cat or by_country:
        print("## Engagement by category / country")
        print()
        print("**Categories:** " + ", ".join(
            f"{cat} ({n})" for cat, n in by_cat.most_common(8)
        ) or "_none_")
        print()
        print("**Countries:** " + ", ".join(
            f"{co} ({n})" for co, n in by_country.most_common(8)
        ) or "_none_")
        print()

    # Activity by platform
    print("## Activity by platform")
    by_plat_events: collections.Counter = collections.Counter()
    by_plat_devs: dict[str, set] = collections.defaultdict(set)
    for r in rows:
        plat = r.get("platform", "?")
        by_plat_events[plat] += 1
        if r.get("device_id"):
            by_plat_devs[plat].add(r["device_id"])
    print()
    print("| Platform | Events | Devices |")
    print("|---|---|---|")
    for plat, n in by_plat_events.most_common():
        print(f"| {plat} | {n:,} | {len(by_plat_devs[plat])} |")
    print()

    # Generated marker — useful for parsing in workflows
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    print(f"---\n_Generated: {now}_")


def q_triage_lookup(hours: int, version: str, limit: int) -> None:
    """L2 — Triage helper. Look up the occurrence stats + signature index
    for the most recent errors. Output is JSON on stdout so the
    triage-on-issue workflow can parse it.

    --version is reused as ``--match <substring>`` to filter by error
    message substring (lets the workflow surface only the bug it just
    detected, rather than every error).
    """
    qs = {
        "select": "created_at,platform,app_version,device_id,event_data",
        "event_type": "in.(client_error,server_error)",
        "created_at": f"gte.{_since(hours)}",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    rows = _get(f"/rest/v1/analytics_events?{urllib.parse.urlencode(qs)}")

    match = (version or "").lower()
    if match:
        filtered = []
        for r in rows:
            d = r.get("event_data") or {}
            blob = " ".join(filter(None, [
                d.get("error_type"), d.get("error_message"),
                d.get("stack_top"), d.get("context"),
            ])).lower()
            if match in blob:
                filtered.append(r)
        rows = filtered

    sigs: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        sigs[_error_signature(r.get("event_data") or {})].append(r)

    out = []
    for sig, grp in sorted(sigs.items(), key=lambda kv: -len(kv[1])):
        plats = sorted({(r.get("platform") or "?") for r in grp})
        vers = sorted({(r.get("app_version") or "?") for r in grp})
        devs = {r.get("device_id") for r in grp if r.get("device_id")}
        sample = grp[0].get("event_data") or {}
        out.append({
            "signature": sig,
            "count": len(grp),
            "unique_devices": len(devs),
            "platforms": plats,
            "versions": vers,
            "first_seen": min(r["created_at"] for r in grp),
            "last_seen": max(r["created_at"] for r in grp),
            "sample": {
                "error_type": sample.get("error_type"),
                "error_message": sample.get("error_message"),
                "stack_top": sample.get("stack_top"),
                "context": sample.get("context"),
                "severity": sample.get("severity"),
            },
        })
    print(json.dumps({"window_hours": hours, "match": version, "signatures": out}, indent=2))


QUERIES = {
    "health": lambda a: q_health(),
    "events": lambda a: q_events(a.hours),
    "errors": lambda a: q_errors(a.hours, a.limit),
    "version": lambda a: q_version(a.hours),
    "devices": lambda a: q_devices(a.hours),
    "v_recent": lambda a: q_v_recent(a.hours, a.version, a.limit),
    "app_launches": lambda a: q_app_launches(a.hours),
    "channel_plays": lambda a: q_channel_plays(a.hours),
    "weekly_pulse": lambda a: q_weekly_pulse(a.hours),
    "triage_lookup": lambda a: q_triage_lookup(a.hours, a.version, a.limit),
}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("query", choices=sorted(QUERIES.keys()))
    p.add_argument("--hours", type=int, default=24)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--version", default="", help="Version prefix for v_recent")
    args = p.parse_args()
    QUERIES[args.query](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
