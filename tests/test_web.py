"""Automated tests for the TV Viewer Web interface.

Tests API endpoints, proxy functionality, and server health.
Run with: pytest tests/test_web.py -v

Note: Channel data tests use >= 0 assertions since CI may not have
access to Supabase. Tests validate API structure and response format.
"""

import asyncio
import logging
import pytest
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from web import server
from web.server import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI web server."""
    return TestClient(app)


# ─── Health & Status ────────────────────────────────────────────────────────

class TestHealth:
    def test_status_endpoint(self, client):
        r = client.get("/api/status")
        assert r.status_code == 200
        data = r.json()
        assert "total_channels" in data
        assert "version" in data
        assert isinstance(data["total_channels"], int)
        assert data["total_channels"] >= 0

    def test_static_index(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "TV Viewer" in r.text

    def test_favicon(self, client):
        r = client.get("/static/favicon.ico")
        assert r.status_code == 200
        assert r.headers["content-type"] in ("image/x-icon", "image/vnd.microsoft.icon")

    def test_icon_png(self, client):
        r = client.get("/static/icon-192.png")
        assert r.status_code == 200
        assert "image/png" in r.headers["content-type"]

    def test_version_endpoint(self, client, monkeypatch):
        async def fake_refresh(force=False):
            assert force is False
            return {
                "current": "2.21.3",
                "latest": "2.21.4",
                "update_available": True,
                "download_url": "https://github.com/tv-viewer-app/tv_viewer/releases/tag/v2.21.4",
            }

        monkeypatch.setattr(server, "_refresh_version_cache", fake_refresh)
        r = client.get("/api/version")
        assert r.status_code == 200
        data = r.json()
        assert data["current"] == "2.21.3"
        assert data["latest"] == "2.21.4"
        assert data["update_available"] is True
        assert data["download_url"].endswith("/v2.21.4")


# ─── Channel API ────────────────────────────────────────────────────────────

class TestChannels:
    def test_list_channels(self, client):
        r = client.get("/api/channels")
        assert r.status_code == 200
        data = r.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)

    def test_channels_include_health_and_sort_verified_first(self, client, monkeypatch):
        class _DummyCache:
            sorted_channels = [
                {
                    "name": "Unchecked One",
                    "url": "https://example.com/unchecked.m3u8",
                    "urls": ["https://example.com/unchecked.m3u8"],
                    "category": "News",
                    "country": "United States",
                    "logo": "",
                    "status": "unchecked",
                    "media_type": "TV",
                },
                {
                    "name": "Reliable One",
                    "url": "https://example.com/reliable.m3u8",
                    "urls": [
                        "https://example.com/reliable.m3u8",
                        "https://backup.example.com/reliable.m3u8",
                    ],
                    "category": "News",
                    "country": "Israel",
                    "logo": "https://example.com/reliable.png",
                    "status": "working",
                    "media_type": "TV",
                },
                {
                    "name": "Failed One",
                    "url": "https://example.com/failed.m3u8",
                    "urls": ["https://example.com/failed.m3u8"],
                    "category": "News",
                    "country": "United States",
                    "logo": "",
                    "status": "failed",
                    "media_type": "TV",
                },
            ]
            by_category = {}
            by_country = {}
            by_cat_country = {}
            local_channels = []
            favorites = set()

        monkeypatch.setattr(server, "_cache", _DummyCache())
        monkeypatch.setattr(server, "_channel_has_epg", lambda name: name == "Reliable One")

        r = client.get("/api/channels?show_all=true")
        assert r.status_code == 200
        data = r.json()
        assert [ch["name"] for ch in data["channels"]] == [
            "Reliable One",
            "Unchecked One",
            "Failed One",
        ]
        assert data["channels"][0]["health_score"] == 70
        assert data["channels"][0]["health"] == "reliable"
        assert data["channels"][1]["health"] == "offline"
        assert data["channels"][2]["health"] == "offline"

    def test_channels_verified_only_filter(self, client, monkeypatch):
        class _DummyCache:
            sorted_channels = [
                {
                    "name": "Reliable One",
                    "url": "https://example.com/reliable.m3u8",
                    "urls": ["https://example.com/reliable.m3u8"],
                    "category": "Sports",
                    "country": "Israel",
                    "logo": "",
                    "status": "working",
                    "media_type": "TV",
                },
                {
                    "name": "Unchecked One",
                    "url": "https://example.com/unchecked.m3u8",
                    "urls": ["https://example.com/unchecked.m3u8"],
                    "category": "Sports",
                    "country": "Israel",
                    "logo": "",
                    "status": "unchecked",
                    "media_type": "TV",
                },
            ]
            by_category = {}
            by_country = {}
            by_cat_country = {}
            local_channels = []
            favorites = set()

        monkeypatch.setattr(server, "_cache", _DummyCache())
        monkeypatch.setattr(server, "_channel_has_epg", lambda _name: False)

        r = client.get("/api/channels?verified_only=true")
        assert r.status_code == 200
        data = r.json()
        assert [ch["name"] for ch in data["channels"]] == ["Reliable One"]
        assert data["channels"][0]["health"] == "reliable"

    def test_channels_with_category(self, client):
        r = client.get("/api/channels?category=News")
        assert r.status_code == 200
        data = r.json()
        assert "channels" in data
        # All returned channels should be News category
        for ch in data["channels"]:
            assert ch.get("category", "").lower() == "news"

    def test_channels_with_country(self, client):
        r = client.get("/api/channels?country=US")
        assert r.status_code == 200
        data = r.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)

    def test_channels_pagination(self, client):
        r = client.get("/api/channels?limit=10&offset=0")
        assert r.status_code == 200
        data = r.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)
        assert len(data["channels"]) <= 10

    def test_categories(self, client):
        r = client.get("/api/categories")
        assert r.status_code == 200
        data = r.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
        # If categories exist, validate structure
        for cat in data["categories"]:
            assert "name" in cat
            assert "count" in cat

    def test_countries(self, client):
        r = client.get("/api/countries")
        assert r.status_code == 200
        data = r.json()
        assert "countries" in data
        assert isinstance(data["countries"], list)

    def test_sources(self, client):
        r = client.get("/api/sources/CNN")
        assert r.status_code == 200
        data = r.json()
        assert "channel" in data
        assert "sources" in data
        assert data["channel"] == "CNN"


# ─── Favorites API ──────────────────────────────────────────────────────────

class TestFavorites:
    def test_get_favorites(self, client):
        r = client.get("/api/favorites")
        assert r.status_code == 200
        data = r.json()
        assert "urls" in data
        assert isinstance(data["urls"], list)

    def test_toggle_favorite(self, client):
        test_url = "http://test-stream.example.com/test.m3u8"
        # Toggle ON
        r = client.post("/api/favorites/toggle",
                       json={"url": test_url})
        assert r.status_code == 200
        data = r.json()
        assert "is_favorite" in data

        # Toggle OFF (cleanup)
        client.post("/api/favorites/toggle", json={"url": test_url})


# ─── Proxy ──────────────────────────────────────────────────────────────────

class TestProxy:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("Upstream returned 403", "geo_blocked"),
            ("geo_blocked", "geo_blocked"),
            ("not_found", "not_found"),
            ("timed out while loading stream", "timeout"),
            ("SSL certificate verify failed", "tls_error"),
            ("codec unsupported", "unsupported_format"),
        ],
    )
    def test_classify_failure(self, message, expected):
        assert server.classify_failure(message) == expected

    @pytest.mark.parametrize(
        ("upstream_error", "error_name"),
        [
            (asyncio.TimeoutError("timed out"), "TimeoutError"),
            (server.aiohttp.ClientError("upstream failed"), "ClientError"),
            (ConnectionResetError("connection reset"), "ConnectionResetError"),
            (OSError("socket closed"), "OSError"),
        ],
    )
    def test_proxy_stream_ends_cleanly_on_expected_upstream_errors(
        self,
        client,
        monkeypatch,
        caplog,
        upstream_error,
        error_name,
    ):
        class _FakeStream:
            async def iter_chunked(self, _chunk_size):
                yield b"first-chunk"
                raise upstream_error

        class _FakeResponse:
            def __init__(self):
                self.status = 200
                self.headers = {"content-type": "video/mp2t"}
                self.content = _FakeStream()
                self.released = False

            async def release(self):
                self.released = True

        class _FakeSession:
            def __init__(self, response):
                self._response = response
                self.closed = False

            async def get(self, *_args, **_kwargs):
                return self._response

            async def close(self):
                self.closed = True

        fake_response = _FakeResponse()
        fake_session = _FakeSession(fake_response)

        monkeypatch.setattr(server, "_validate_proxy_url", lambda _url: None)
        monkeypatch.setattr(server.aiohttp, "ClientSession", lambda **_kwargs: fake_session)

        with caplog.at_level(logging.DEBUG, logger=server.logger.name):
            with client.stream(
                "GET",
                "/api/proxy",
                params={"url": "https://example.com/live.ts"},
            ) as response:
                body = b"".join(response.iter_bytes())

        assert response.status_code == 200
        assert body == b"first-chunk"
        assert fake_response.released is True
        assert fake_session.closed is True
        debug_messages = [
            record.getMessage()
            for record in caplog.records
            if record.levelno == logging.DEBUG
        ]
        assert any(
            "Proxy stream ended quietly" in message and error_name in message
            for message in debug_messages
        )

    def test_proxy_rejects_invalid_url(self, client):
        r = client.get("/api/proxy?url=not-a-url")
        assert r.status_code == 400

    def test_proxy_rejects_missing_url(self, client):
        r = client.get("/api/proxy")
        assert r.status_code == 422  # FastAPI validation error

    def test_proxy_rejects_long_query_url(self, client):
        long_url = "https://example.com/" + ("a" * 5000)
        r = client.get("/api/proxy", params={"url": long_url})
        assert r.status_code == 414

    def test_proxy_forwards_upstream_failure_headers(self, client, monkeypatch):
        class _FakeResponse:
            def __init__(self):
                self.status = 403
                self.headers = {"content-type": "application/vnd.apple.mpegurl"}
                self.released = False

            async def release(self):
                self.released = True

        class _FakeSession:
            def __init__(self, response):
                self._response = response
                self.closed = False

            async def get(self, *_args, **_kwargs):
                return self._response

            async def close(self):
                self.closed = True

        fake_response = _FakeResponse()
        fake_session = _FakeSession(fake_response)

        monkeypatch.setattr(server, "_validate_proxy_url", lambda _url: None)
        monkeypatch.setattr(server.aiohttp, "ClientSession", lambda **_kwargs: fake_session)

        r = client.get("/api/proxy", params={"url": "https://example.com/live.m3u8"})

        assert r.status_code == 403
        assert r.json()["failure_type"] == "geo_blocked"
        assert r.headers["x-stream-status"] == "failed"
        assert r.headers["x-stream-failure-type"] == "geo_blocked"
        assert r.headers["x-stream-status-reason"] == "geo_blocked"
        assert r.headers["x-upstream-status"] == "403"
        assert r.headers["x-proxy-upstream"] == "true"
        assert fake_response.released is True
        assert fake_session.closed is True

    def test_proxy_post_returns_tokenized_url_for_long_input(self, client):
        long_url = "https://example.com/" + ("a" * 5000)
        r = client.post("/api/proxy", json={"url": long_url})
        assert r.status_code == 200
        data = r.json()
        assert data["tokenized"] is True
        assert data["proxy_url"].startswith("http://testserver/api/proxy/")

    def test_proxy_hls_manifest(self, client):
        """Test proxy with a known working public HLS stream."""
        # Use a public test stream
        url = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
        r = client.get(f"/api/proxy?url={url}")
        # May fail if test stream is down, but should not error on our side
        if r.status_code == 200:
            assert "#EXTM3U" in r.text or "#EXT-X" in r.text
            assert "application/vnd.apple.mpegurl" in r.headers["content-type"]
            # URLs should be rewritten to go through proxy
            for line in r.text.split('\n'):
                if line.strip() and not line.startswith('#'):
                    assert "/api/proxy?url=" in line

    def test_proxy_cors_headers(self, client):
        """Proxy responses must include CORS headers."""
        url = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
        r = client.get(f"/api/proxy?url={url}")
        if r.status_code == 200:
            assert r.headers.get("access-control-allow-origin") == "*"

    def test_statistics_include_live_and_today_metrics(self, client, monkeypatch):
        async def fake_refresh(force=False):
            return {
                "total_channels": 12,
                "working_channels": 10,
                "has_analytics": True,
                "unique_users": 7,
                "live_sessions": 3,
                "today_plays": 9,
                "today_active": 4,
                "total_plays": 21,
                "total_events": 40,
                "unique_channels_played": 5,
                "platforms": {"web": 40},
                "user_countries": [],
                "top_channels": [],
                "channel_countries": [],
                "categories": [],
                "recently_added": [],
                "country_last_access": [],
                "country_top_channels": {},
            }

        monkeypatch.setattr(server, "_refresh_statistics_cache", fake_refresh)
        monkeypatch.setattr(server, "_rate_limit_check", lambda *_args, **_kwargs: True)

        r = client.get("/api/statistics")
        assert r.status_code == 200
        data = r.json()
        assert data["live_sessions"] == 3
        assert data["today_plays"] == 9
        assert data["today_active"] == 4


# ─── Map ────────────────────────────────────────────────────────────────────

class TestMap:
    def test_map_data(self, client):
        r = client.get("/api/map")
        assert r.status_code == 200
        data = r.json()
        assert "countries" in data
        assert isinstance(data["countries"], list)
        # If countries exist, validate structure
        for c in data["countries"][:5]:
            assert "name" in c
            assert "count" in c


# ─── Health report security (v2.15.2) ──────────────────────────────────────

class TestHealthReportSecurity:
    """Verify defences added in v2.15.2: PostgREST-metacharacter rejection,
    rate limiting, and case-handling of channel names."""

    def test_unsafe_channel_name_rejected(self, client):
        # Import the validator directly to assert behaviour without hitting Supabase
        from web.server import _is_safe_channel_name
        # Safe names
        assert _is_safe_channel_name("BBC News")
        assert _is_safe_channel_name("Kan 11")
        assert _is_safe_channel_name("Disney+ HD")
        # PostgREST filter metacharacters — all must be rejected
        # (these are the delimiters that can break out of `name=eq.{val}`
        # or `name=ilike.{val}` even after URL-encoding via params=)
        for bad in ["X,Y", "X(1)", "X)", "X*", "X:eq.0"]:
            assert not _is_safe_channel_name(bad), f"should reject {bad!r}"
        # Control chars
        assert not _is_safe_channel_name("name\nwith newline")
        assert not _is_safe_channel_name("name\twith tab")
        # Empty / too long
        assert not _is_safe_channel_name("")
        assert not _is_safe_channel_name("X" * 201)
        # Non-string
        assert not _is_safe_channel_name(None)
        assert not _is_safe_channel_name(123)

    def test_health_report_accepts_safe_payload(self, client):
        # Endpoint must accept well-formed reports without 500ing
        r = client.post(
            "/api/health/report",
            json={"url": "https://example.com/stream.m3u8", "status": "working"},
        )
        assert r.status_code == 200
        assert r.json().get("status") in ("recorded", "ignored")

    def test_health_report_classifies_failure_reason(self, client):
        r = client.post(
            "/api/health/report",
            json={
                "url": "https://example.com/stream.m3u8",
                "status": "broken",
                "reason": "Upstream returned 403",
            },
        )
        assert r.status_code == 200
        assert r.json().get("failure_type") == "geo_blocked"

    def test_health_report_skips_geo_blocked_broken_votes(self, client, monkeypatch):
        import utils.supabase_channels as supabase_channels

        called = {"broken": 0, "local_broken": 0}

        async def _fake_report_channel(_url_hash):
            called["broken"] += 1
            return True

        monkeypatch.setattr(server, "_mark_local_broken", lambda _url: called.__setitem__("local_broken", called["local_broken"] + 1))
        monkeypatch.setattr(supabase_channels, "is_configured", lambda: True)
        monkeypatch.setattr(supabase_channels, "report_channel", _fake_report_channel)

        r = client.post(
            "/api/health/report",
            json={
                "url": "https://example.com/stream.m3u8",
                "status": "broken",
                "reason": "geo_blocked",
            },
        )

        assert r.status_code == 200
        assert r.json().get("failure_type") == "geo_blocked"
        assert r.json().get("counted") is False
        assert called["broken"] == 0
        assert called["local_broken"] == 0

    def test_health_report_ignores_missing_fields(self, client):
        r = client.post("/api/health/report", json={"url": ""})
        assert r.status_code == 200
        assert r.json() == {"status": "ignored"}

    def test_health_report_rate_limit_global(self, client, monkeypatch):
        """Global bucket: the (cap + 1)th request is deterministically throttled.

        Keep the window long inside the test so slow CI runners cannot age out the
        earliest requests before the final assertion.
        """
        import web.server as server

        cap = 5
        monkeypatch.setattr(server, "_HEALTH_RATE_GLOBAL", (cap, 120.0))

        # Reset buckets to isolate from other tests
        with server._health_buckets_lock:
            server._health_buckets.clear()

        payload = {
            "url": "https://example.com/rl.m3u8",
            "status": "working",
        }

        for _ in range(cap):
            r = client.post("/api/health/report", json=payload)
            assert r.status_code == 200, f"Unexpected status {r.status_code}"
            assert r.json().get("status") in ("recorded", "ignored")

        r = client.post("/api/health/report", json=payload)
        assert r.status_code == 200, f"Unexpected status {r.status_code}"
        assert r.json() == {"status": "throttled"}


# ─── Report ─────────────────────────────────────────────────────────────────

class TestReport:
    def test_report_broken(self, client):
        r = client.post("/api/report",
                       json={"url": "http://broken.example.com/stream.m3u8",
                             "name": "Test Channel"})
        assert r.status_code == 200
        data = r.json()
        assert "status" in data


# ─── EPG ────────────────────────────────────────────────────────────────────

class TestEpg:
    def test_epg_endpoint(self, client):
        r = client.get("/api/epg/CNN")
        assert r.status_code == 200
        data = r.json()
        assert "channel" in data
        assert "now" in data
        assert "next" in data
        assert "schedule" in data


# ─── Docker & Deployment ────────────────────────────────────────────────────

class TestDeployment:
    def test_dockerfile_exists(self):
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile must exist for web deployment"

    def test_dockerfile_valid(self):
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        assert "python" in content.lower()
        assert "8765" in content
        assert "web.server" in content
        assert "HEALTHCHECK" in content

    def test_requirements_available(self):
        """Web server dependencies must be importable."""
        import fastapi
        import uvicorn
        import aiohttp
        assert True
