from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from web import server
from web.server import app


def _make_cache(channels):
    class _DummyCache:
        sorted_channels = channels
        by_category = {}
        by_country = {}
        by_cat_country = {}
        local_channels = []
        favorites = set()

    return _DummyCache()


def test_stale_channels_hidden_from_default_listing(monkeypatch):
    stale_checked = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    monkeypatch.setattr(
        server,
        "_cache",
        _make_cache([
            {
                "name": "Healthy One",
                "url": "https://example.com/healthy.m3u8",
                "urls": ["https://example.com/healthy.m3u8"],
                "category": "News",
                "country": "Israel",
                "logo": "",
                "status": "working",
                "media_type": "TV",
            },
            {
                "name": "Dead One",
                "url": "https://example.com/dead.m3u8",
                "urls": ["https://example.com/dead.m3u8"],
                "category": "News",
                "country": "United States",
                "logo": "",
                "status": "broken",
                "media_type": "TV",
                "report_count": 12,
                "last_checked": stale_checked,
            },
        ]),
    )
    monkeypatch.setattr(server, "_channel_has_epg", lambda _name: False)

    client = TestClient(app)
    response = client.get("/api/channels")

    assert response.status_code == 200
    assert [channel["name"] for channel in response.json()["channels"]] == ["Healthy One"]


def test_stale_channels_remain_searchable(monkeypatch):
    stale_checked = (datetime.now(timezone.utc) - timedelta(days=9)).isoformat()
    monkeypatch.setattr(
        server,
        "_cache",
        _make_cache([
            {
                "name": "Dead One",
                "url": "https://example.com/dead.m3u8",
                "urls": ["https://example.com/dead.m3u8"],
                "category": "News",
                "country": "United States",
                "logo": "",
                "status": "broken",
                "media_type": "TV",
                "report_count": 10,
                "last_checked": stale_checked,
            },
        ]),
    )
    monkeypatch.setattr(server, "_channel_has_epg", lambda _name: False)

    client = TestClient(app)
    response = client.get("/api/channels?search=dead")

    assert response.status_code == 200
    data = response.json()
    assert [channel["name"] for channel in data["channels"]] == ["Dead One"]


def test_include_dead_shows_stale_channels(monkeypatch):
    stale_checked = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    monkeypatch.setattr(
        server,
        "_cache",
        _make_cache([
            {
                "name": "Dead One",
                "url": "https://example.com/dead.m3u8",
                "urls": ["https://example.com/dead.m3u8"],
                "category": "News",
                "country": "United States",
                "logo": "",
                "status": "broken",
                "media_type": "TV",
                "report_count": 15,
                "last_checked": stale_checked,
            },
        ]),
    )
    monkeypatch.setattr(server, "_channel_has_epg", lambda _name: False)

    client = TestClient(app)
    response = client.get("/api/channels?include_dead=true")

    assert response.status_code == 200
    data = response.json()
    assert [channel["name"] for channel in data["channels"]] == ["Dead One"]
    assert data["channels"][0]["health_score"] == -35
