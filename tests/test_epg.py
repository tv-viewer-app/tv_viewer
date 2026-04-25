"""Tests for EPG (Electronic Program Guide) service."""

import json
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.epg import (
    EPGProgram,
    EPGService,
    _parse_xmltv_datetime,
    parse_xmltv,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_XMLTV = """<?xml version="1.0" encoding="UTF-8"?>
<tv>
  <channel id="BBCOne.uk">
    <display-name>BBC One</display-name>
  </channel>
  <channel id="CNN.us">
    <display-name>CNN</display-name>
  </channel>
  <programme start="{now_start}" stop="{now_end}" channel="BBCOne.uk">
    <title>BBC News</title>
    <desc>Latest headlines</desc>
    <category>News</category>
  </programme>
  <programme start="{next_start}" stop="{next_end}" channel="BBCOne.uk">
    <title>EastEnders</title>
    <sub-title>Episode 5</sub-title>
  </programme>
  <programme start="{old_start}" stop="{old_end}" channel="CNN.us">
    <title>Anderson Cooper 360</title>
  </programme>
</tv>
"""


def _make_xmltv(now=None):
    """Generate XMLTV with programs relative to *now*."""
    now = now or datetime.now(timezone.utc)
    fmt = "%Y%m%d%H%M%S +0000"
    return SAMPLE_XMLTV.format(
        now_start=(now - timedelta(minutes=15)).strftime(fmt),
        now_end=(now + timedelta(minutes=15)).strftime(fmt),
        next_start=(now + timedelta(minutes=15)).strftime(fmt),
        next_end=(now + timedelta(minutes=75)).strftime(fmt),
        old_start=(now - timedelta(minutes=90)).strftime(fmt),
        old_end=(now - timedelta(minutes=30)).strftime(fmt),
    )


# ---------------------------------------------------------------------------
# _parse_xmltv_datetime
# ---------------------------------------------------------------------------

class TestParseXmltvDatetime:
    def test_with_timezone(self):
        dt = _parse_xmltv_datetime("20250416200000 +0300")
        assert dt is not None
        assert dt.year == 2025
        assert dt.hour == 20
        assert dt.tzinfo is not None

    def test_without_timezone_defaults_utc(self):
        dt = _parse_xmltv_datetime("20250416200000")
        assert dt is not None
        assert dt.tzinfo == timezone.utc

    def test_empty_string(self):
        assert _parse_xmltv_datetime("") is None

    def test_none(self):
        assert _parse_xmltv_datetime(None) is None

    def test_invalid_format(self):
        assert _parse_xmltv_datetime("not-a-date") is None

    def test_negative_offset(self):
        dt = _parse_xmltv_datetime("20250101120000 -0500")
        assert dt is not None
        assert dt.utcoffset().total_seconds() == -5 * 3600


# ---------------------------------------------------------------------------
# parse_xmltv
# ---------------------------------------------------------------------------

class TestParseXmltv:
    def test_parses_channels(self):
        xml = _make_xmltv()
        channels, _ = parse_xmltv(xml)
        assert "BBCOne.uk" in channels
        assert channels["BBCOne.uk"] == "BBC One"
        assert "CNN.us" in channels

    def test_parses_current_program(self):
        xml = _make_xmltv()
        _, schedules = parse_xmltv(xml)
        assert "BBCOne.uk" in schedules
        titles = [p.title for p in schedules["BBCOne.uk"]]
        assert "BBC News" in titles

    def test_parses_description(self):
        xml = _make_xmltv()
        _, schedules = parse_xmltv(xml)
        news = [p for p in schedules["BBCOne.uk"] if p.title == "BBC News"][0]
        assert news.description == "Latest headlines"

    def test_parses_category(self):
        xml = _make_xmltv()
        _, schedules = parse_xmltv(xml)
        news = [p for p in schedules["BBCOne.uk"] if p.title == "BBC News"][0]
        assert news.category == "News"

    def test_sorted_by_start_time(self):
        xml = _make_xmltv()
        _, schedules = parse_xmltv(xml)
        for programs in schedules.values():
            for i in range(len(programs) - 1):
                assert programs[i].start <= programs[i + 1].start

    def test_invalid_xml(self):
        channels, schedules = parse_xmltv("<broken")
        assert channels == {}
        assert schedules == {}

    def test_empty_xml(self):
        channels, schedules = parse_xmltv("<tv></tv>")
        assert channels == {}
        assert schedules == {}


# ---------------------------------------------------------------------------
# EPGProgram
# ---------------------------------------------------------------------------

class TestEPGProgram:
    def test_is_current(self):
        now = datetime.now(timezone.utc)
        p = EPGProgram("Test", now - timedelta(minutes=10), now + timedelta(minutes=10))
        assert p.is_current(now) is True

    def test_is_not_current_past(self):
        now = datetime.now(timezone.utc)
        p = EPGProgram("Test", now - timedelta(hours=2), now - timedelta(hours=1))
        assert p.is_current(now) is False

    def test_is_upcoming(self):
        now = datetime.now(timezone.utc)
        p = EPGProgram("Test", now + timedelta(minutes=5), now + timedelta(minutes=35))
        assert p.is_upcoming(now) is True

    def test_duration_minutes(self):
        now = datetime.now(timezone.utc)
        p = EPGProgram("Test", now, now + timedelta(minutes=60))
        assert p.duration_minutes == 60

    def test_progress_percent_midway(self):
        now = datetime.now(timezone.utc)
        p = EPGProgram("Test", now - timedelta(minutes=30), now + timedelta(minutes=30))
        progress = p.progress_percent
        assert 45 <= progress <= 55  # ~50%

    def test_progress_percent_not_started(self):
        now = datetime.now(timezone.utc)
        p = EPGProgram("Test", now + timedelta(hours=1), now + timedelta(hours=2))
        assert p.progress_percent == 0.0

    def test_progress_percent_finished(self):
        now = datetime.now(timezone.utc)
        p = EPGProgram("Test", now - timedelta(hours=2), now - timedelta(hours=1))
        assert p.progress_percent == 100.0

    def test_to_dict_round_trip(self):
        now = datetime.now(timezone.utc)
        p = EPGProgram("News", now, now + timedelta(hours=1),
                        channel_id="ch1", description="Desc", category="News")
        d = p.to_dict()
        p2 = EPGProgram.from_dict(d)
        assert p2.title == "News"
        assert p2.channel_id == "ch1"
        assert p2.description == "Desc"


# ---------------------------------------------------------------------------
# EPGService
# ---------------------------------------------------------------------------

class TestEPGService:
    def test_fresh_service_not_initialized(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.epg.EPG_CACHE_FILE", str(tmp_path / "no_cache.json"))
        svc = EPGService()
        assert svc.is_loaded is False

    def test_get_now_next_returns_tuple(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.epg.EPG_CACHE_FILE", str(tmp_path / "no_cache.json"))
        svc = EPGService()
        result = svc.get_now_next(channel_name="nonexistent")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result == (None, None)

    def test_get_schedule_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.epg.EPG_CACHE_FILE", str(tmp_path / "no_cache.json"))
        svc = EPGService()
        assert svc.get_schedule(channel_name="x") == []

    def test_channel_count_zero_initially(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.epg.EPG_CACHE_FILE", str(tmp_path / "no_cache.json"))
        svc = EPGService()
        assert svc.channel_count == 0


class TestEPGServiceWithData:
    """Tests with manually loaded EPG data."""

    @pytest.fixture
    def svc(self):
        svc = EPGService()
        xml = _make_xmltv()
        channels, schedules = parse_xmltv(xml)
        with svc._lock:
            svc._channel_map = channels
            svc._schedules = schedules
            svc._build_name_index()
            svc._initialized = True
        return svc

    def test_get_current_program(self, svc):
        prog = svc.get_current_program(channel_name="BBC One")
        assert prog is not None
        assert prog.title == "BBC News"

    def test_get_next_program(self, svc):
        prog = svc.get_next_program(channel_name="BBC One")
        assert prog is not None
        assert prog.title == "EastEnders"

    def test_get_now_next(self, svc):
        now, nxt = svc.get_now_next(channel_name="BBC One")
        assert now is not None and now.title == "BBC News"
        assert nxt is not None and nxt.title == "EastEnders"

    def test_case_insensitive_lookup(self, svc):
        prog = svc.get_current_program(channel_name="bbc one")
        assert prog is not None

    def test_channel_id_lookup(self, svc):
        prog = svc.get_current_program(channel_id="BBCOne.uk")
        assert prog is not None

    def test_get_schedule(self, svc):
        schedule = svc.get_schedule(channel_name="BBC One", hours=2)
        assert len(schedule) >= 1
        titles = [p.title for p in schedule]
        assert "BBC News" in titles

    def test_channel_count(self, svc):
        assert svc.channel_count == 2

    def test_is_loaded(self, svc):
        assert svc.is_loaded is True

    def test_nonexistent_channel(self, svc):
        assert svc.get_current_program(channel_name="ZZZZ") is None

    def test_thread_safe_read(self, svc):
        """Concurrent reads should not raise."""
        errors = []

        def _read():
            try:
                for _ in range(50):
                    svc.get_now_next(channel_name="BBC One")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_read) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        assert errors == []


class TestEPGCache:
    def test_save_and_load_cache(self):
        svc = EPGService()
        xml = _make_xmltv()
        channels, schedules = parse_xmltv(xml)
        with svc._lock:
            svc._channel_map = channels
            svc._schedules = schedules
            svc._build_name_index()
            svc._initialized = True
            svc._last_fetch = time.time()

        # Save cache
        svc._save_cache()

        # Create a new service and load from cache
        svc2 = EPGService()
        assert svc2.channel_count >= 1  # loaded from cache

    def test_corrupt_cache_handled(self, tmp_path):
        cache_file = tmp_path / "epg_cache.json"
        cache_file.write_text("{corrupt")
        with patch("utils.epg.EPG_CACHE_FILE", str(cache_file)):
            svc = EPGService()
            # Should not crash
            assert svc.channel_count == 0
