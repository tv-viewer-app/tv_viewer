"""Automated tests for the TV Viewer Web interface.

Tests API endpoints, proxy functionality, and server health.
Run with: pytest tests/test_web.py -v

Note: Channel data tests use >= 0 assertions since CI may not have
access to Supabase. Tests validate API structure and response format.
"""

import pytest
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
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


# ─── Channel API ────────────────────────────────────────────────────────────

class TestChannels:
    def test_list_channels(self, client):
        r = client.get("/api/channels")
        assert r.status_code == 200
        data = r.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)

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
    def test_proxy_rejects_invalid_url(self, client):
        r = client.get("/api/proxy?url=not-a-url")
        assert r.status_code == 400

    def test_proxy_rejects_missing_url(self, client):
        r = client.get("/api/proxy")
        assert r.status_code == 422  # FastAPI validation error

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
