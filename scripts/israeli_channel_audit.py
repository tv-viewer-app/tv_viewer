#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

SUPABASE_URL = "https://cdtxpefohpwtusmqengu.supabase.co"
SUPABASE_KEY = "sb_publishable_hp_c_ek7bYv33-fLqmgvnw_KS9T33Oi"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}
WRITE_HEADERS = {
    **HEADERS,
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}
REQUEST_HEADERS = {
    "User-Agent": "TVViewer-IsraelAudit/1.0",
    "Accept": "*/*",
}
VALID_CONTENT_TYPES = (
    "application/vnd.apple.mpegurl",
    "application/x-mpegurl",
    "audio/mpegurl",
    "audio/x-mpegurl",
    "application/octet-stream",
    "video/",
    "audio/",
)
OUTPUT_PATH = Path("docs") / "israeli_channels_audit.json"
URL_TIMEOUT = 8
CONCURRENCY = 12


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch_israeli_channels() -> list[dict[str, Any]]:
    url = (
        f"{SUPABASE_URL}/rest/v1/channels"
        "?select=name,urls,source,url_hash,category,country,media_type,logo"
        "&country=eq.Israel&order=name&limit=500"
    )
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def _body_looks_like_playlist(response: requests.Response) -> bool:
    try:
        for chunk in response.iter_content(chunk_size=512, decode_unicode=True):
            if not chunk:
                continue
            text = chunk if isinstance(chunk, str) else chunk.decode("utf-8", errors="ignore")
            return "#EXTM3U" in text or ".ts" in text or ".m3u8" in text
    except Exception:
        return False
    return False


def _classify_status(status_code: int, content_type: str, body_match: bool) -> tuple[bool, str]:
    if status_code == 403:
        return False, "geo_or_forbidden"
    if status_code >= 400:
        return False, "http_error"
    if any(token in content_type for token in VALID_CONTENT_TYPES) or body_match:
        return True, "working"
    if 200 <= status_code < 300:
        return True, "working_unknown_type"
    return False, "unexpected"


def test_url(url: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "url": url,
        "ok": False,
        "status": "unreachable",
        "http_status": None,
        "content_type": "",
        "final_url": url,
        "error": "",
    }
    session = requests.Session()
    for method in ("HEAD", "GET"):
        try:
            response = session.request(
                method,
                url,
                headers=REQUEST_HEADERS,
                timeout=URL_TIMEOUT,
                allow_redirects=True,
                stream=(method == "GET"),
            )
            result["http_status"] = response.status_code
            result["content_type"] = response.headers.get("Content-Type", "").lower()
            result["final_url"] = str(response.url)
            body_match = method == "GET" and _body_looks_like_playlist(response)
            ok, status = _classify_status(response.status_code, result["content_type"], body_match)
            result["ok"] = ok
            result["status"] = status
            if ok or method == "GET" or response.status_code == 403:
                return result
        except requests.exceptions.Timeout:
            result["status"] = "timeout"
            result["error"] = "timeout"
        except requests.exceptions.ConnectionError as exc:
            result["status"] = "connection_error"
            result["error"] = str(exc)
        except requests.RequestException as exc:
            result["status"] = "request_error"
            result["error"] = str(exc)
    return result


def audit_channel(channel: dict[str, Any]) -> dict[str, Any]:
    urls = [url for url in (channel.get("urls") or []) if isinstance(url, str) and url.startswith("http")]
    checks = [test_url(url) for url in urls]
    working = [entry for entry in checks if entry["ok"]]
    blocked = [entry for entry in checks if entry["status"] == "geo_or_forbidden"]
    return {
        "name": channel.get("name"),
        "source": channel.get("source"),
        "category": channel.get("category"),
        "media_type": channel.get("media_type"),
        "logo": channel.get("logo"),
        "url_hash": channel.get("url_hash"),
        "urls": urls,
        "checks": checks,
        "working_urls": [entry["url"] for entry in working],
        "primary_working": bool(working and working[0]["url"] == urls[0]) if urls else False,
        "any_working": bool(working),
        "geo_blocked": bool(blocked and not working),
    }


def run_audit() -> dict[str, Any]:
    channels = fetch_israeli_channels()
    audited: list[dict[str, Any]] = []
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = [pool.submit(audit_channel, channel) for channel in channels]
        for future in as_completed(futures):
            item = future.result()
            with lock:
                audited.append(item)
    audited.sort(key=lambda item: (item["name"] or "").casefold())
    working = sum(1 for item in audited if item["any_working"])
    blocked = sum(1 for item in audited if item["geo_blocked"])
    report = {
        "count": len(audited),
        "working_count": working,
        "broken_count": len(audited) - working,
        "geo_blocked_count": blocked,
        "channels": audited,
    }
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    report = run_audit()
    print(json.dumps(
        {
            "count": report["count"],
            "working_count": report["working_count"],
            "broken_count": report["broken_count"],
            "geo_blocked_count": report["geo_blocked_count"],
            "output": str(OUTPUT_PATH),
        },
        ensure_ascii=False,
    ))
