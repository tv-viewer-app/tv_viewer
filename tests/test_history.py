"""
Unit tests for utils/history.py — WatchHistory.

Run with: pytest tests/test_history.py -v
"""

import json
import os
import sys
import tempfile
import threading
import time

import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.history import WatchHistory, DEFAULT_MAX_ENTRIES, SAVE_DEBOUNCE_SECONDS


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_channel(name="Test Channel", url="http://example.com/stream.m3u8",
                  country="US", category="News"):
    return {"name": name, "url": url, "country": country, "category": category}


@pytest.fixture
def tmp_history(tmp_path):
    """Return a WatchHistory backed by a temp file."""
    filepath = str(tmp_path / "watch_history.json")
    return WatchHistory(filepath=filepath, max_entries=DEFAULT_MAX_ENTRIES)


# ── Basic record / retrieve ──────────────────────────────────────────────


class TestRecordPlay:

    def test_record_single_play(self, tmp_history):
        ch = _make_channel()
        tmp_history.record_play(ch)

        recent = tmp_history.get_recent(limit=10)
        assert len(recent) == 1
        assert recent[0]["url"] == ch["url"]
        assert recent[0]["name"] == ch["name"]
        assert recent[0]["play_count"] == 1
        assert recent[0]["last_played"] > 0

    def test_record_increments_play_count(self, tmp_history):
        ch = _make_channel()
        tmp_history.record_play(ch)
        tmp_history.record_play(ch)
        tmp_history.record_play(ch)

        recent = tmp_history.get_recent()
        assert len(recent) == 1
        assert recent[0]["play_count"] == 3

    def test_record_updates_last_played(self, tmp_history):
        ch = _make_channel()
        tmp_history.record_play(ch)
        first_ts = tmp_history.get_recent()[0]["last_played"]

        time.sleep(0.05)
        tmp_history.record_play(ch)
        second_ts = tmp_history.get_recent()[0]["last_played"]

        assert second_ts > first_ts

    def test_record_ignores_empty_url(self, tmp_history):
        tmp_history.record_play({"name": "No URL"})
        assert len(tmp_history.get_recent()) == 0

    def test_record_updates_metadata(self, tmp_history):
        ch = _make_channel(name="Old Name", country="US")
        tmp_history.record_play(ch)

        ch2 = _make_channel(name="New Name", country="UK")
        tmp_history.record_play(ch2)

        entry = tmp_history.get_recent()[0]
        assert entry["name"] == "New Name"
        assert entry["country"] == "UK"


# ── Ordering ──────────────────────────────────────────────────────────────


class TestOrdering:

    def test_get_recent_sorted_by_last_played(self, tmp_history):
        for i in range(5):
            tmp_history.record_play(_make_channel(
                name=f"Ch{i}", url=f"http://example.com/{i}"))
            time.sleep(0.02)

        recent = tmp_history.get_recent(limit=5)
        timestamps = [e["last_played"] for e in recent]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_most_played(self, tmp_history):
        ch_a = _make_channel(name="A", url="http://a.com")
        ch_b = _make_channel(name="B", url="http://b.com")

        for _ in range(5):
            tmp_history.record_play(ch_a)
        for _ in range(10):
            tmp_history.record_play(ch_b)

        most = tmp_history.get_most_played(limit=2)
        assert most[0]["url"] == ch_b["url"]
        assert most[0]["play_count"] == 10
        assert most[1]["url"] == ch_a["url"]

    def test_get_recent_respects_limit(self, tmp_history):
        for i in range(10):
            tmp_history.record_play(_make_channel(
                name=f"Ch{i}", url=f"http://example.com/{i}"))

        assert len(tmp_history.get_recent(limit=3)) == 3

    def test_get_most_played_respects_limit(self, tmp_history):
        for i in range(10):
            tmp_history.record_play(_make_channel(
                name=f"Ch{i}", url=f"http://example.com/{i}"))

        assert len(tmp_history.get_most_played(limit=2)) == 2


# ── Max entries / eviction ────────────────────────────────────────────────


class TestEviction:

    def test_max_entries_enforced(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")
        wh = WatchHistory(filepath=filepath, max_entries=5)

        for i in range(10):
            wh.record_play(_make_channel(name=f"Ch{i}", url=f"http://ex.com/{i}"))
            time.sleep(0.01)  # ensure distinct timestamps

        assert len(wh.get_recent(limit=100)) == 5

    def test_oldest_entries_dropped(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")
        wh = WatchHistory(filepath=filepath, max_entries=3)

        for i in range(5):
            wh.record_play(_make_channel(name=f"Ch{i}", url=f"http://ex.com/{i}"))
            time.sleep(0.01)

        recent = wh.get_recent(limit=100)
        names = {e["name"] for e in recent}
        # The last 3 should survive (Ch2, Ch3, Ch4)
        assert "Ch4" in names
        assert "Ch3" in names
        assert "Ch2" in names
        assert "Ch0" not in names
        assert "Ch1" not in names


# ── Remove / Clear ────────────────────────────────────────────────────────


class TestRemoveAndClear:

    def test_remove_by_url(self, tmp_history):
        ch = _make_channel()
        tmp_history.record_play(ch)
        assert len(tmp_history.get_recent()) == 1

        tmp_history.remove(ch["url"])
        assert len(tmp_history.get_recent()) == 0

    def test_remove_nonexistent_url_no_error(self, tmp_history):
        tmp_history.remove("http://nonexistent.com")

    def test_clear(self, tmp_history):
        for i in range(5):
            tmp_history.record_play(_make_channel(
                name=f"Ch{i}", url=f"http://ex.com/{i}"))

        tmp_history.clear()
        assert len(tmp_history.get_recent()) == 0


# ── Persistence ───────────────────────────────────────────────────────────


class TestPersistence:

    def test_save_and_reload(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")

        wh1 = WatchHistory(filepath=filepath)
        wh1.record_play(_make_channel(name="Saved Channel"))
        wh1.flush()  # force immediate write

        # Reload from disk
        wh2 = WatchHistory(filepath=filepath)
        recent = wh2.get_recent()
        assert len(recent) == 1
        assert recent[0]["name"] == "Saved Channel"
        assert recent[0]["play_count"] == 1

    def test_flush_writes_immediately(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")
        wh = WatchHistory(filepath=filepath)
        wh.record_play(_make_channel())
        wh.flush()

        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["entries"]) == 1

    def test_corrupt_file_handled(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")
        with open(filepath, "w") as f:
            f.write("{{{corrupt json")

        # Should not raise — logs error, starts empty
        wh = WatchHistory(filepath=filepath)
        assert len(wh.get_recent()) == 0

    def test_missing_file_starts_empty(self, tmp_path):
        filepath = str(tmp_path / "nonexistent.json")
        wh = WatchHistory(filepath=filepath)
        assert len(wh.get_recent()) == 0

    def test_play_count_persists_across_reload(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")
        ch = _make_channel()

        wh1 = WatchHistory(filepath=filepath)
        wh1.record_play(ch)
        wh1.record_play(ch)
        wh1.flush()

        wh2 = WatchHistory(filepath=filepath)
        assert wh2.get_recent()[0]["play_count"] == 2


# ── Thread safety ─────────────────────────────────────────────────────────


class TestThreadSafety:

    def test_concurrent_record_play(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")
        wh = WatchHistory(filepath=filepath, max_entries=50)

        errors = []

        def worker(thread_id):
            try:
                for i in range(20):
                    wh.record_play(_make_channel(
                        name=f"T{thread_id}-Ch{i}",
                        url=f"http://ex.com/t{thread_id}/{i}",
                    ))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"
        # max_entries=50, so at most 50 remain
        assert len(wh.get_recent(limit=200)) <= 50

    def test_concurrent_record_and_read(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")
        wh = WatchHistory(filepath=filepath)

        errors = []
        stop = threading.Event()

        def writer():
            try:
                for i in range(50):
                    wh.record_play(_make_channel(
                        name=f"Ch{i}", url=f"http://ex.com/{i}"))
            except Exception as exc:
                errors.append(exc)
            finally:
                stop.set()

        def reader():
            try:
                while not stop.is_set():
                    wh.get_recent(limit=10)
                    wh.get_most_played(limit=5)
            except Exception as exc:
                errors.append(exc)

        tw = threading.Thread(target=writer)
        tr = threading.Thread(target=reader)
        tw.start()
        tr.start()
        tw.join(timeout=10)
        tr.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"


# ── Debounce ──────────────────────────────────────────────────────────────


class TestDebounce:

    def test_debounce_batches_saves(self, tmp_path):
        """Multiple rapid record_play calls should result in a single save."""
        filepath = str(tmp_path / "watch_history.json")
        wh = WatchHistory(filepath=filepath)

        for i in range(10):
            wh.record_play(_make_channel(name=f"Ch{i}", url=f"http://ex.com/{i}"))

        # File may not exist yet (debounce hasn't fired)
        # Force flush and verify all entries are present
        wh.flush()
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["entries"]) == 10

    def test_debounce_eventually_saves(self, tmp_path):
        """After debounce period, data should be on disk."""
        filepath = str(tmp_path / "watch_history.json")
        wh = WatchHistory(filepath=filepath)
        wh.record_play(_make_channel())

        # Wait for debounce timer to fire (2s + margin)
        time.sleep(SAVE_DEBOUNCE_SECONDS + 0.5)

        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["entries"]) == 1


# ── Edge cases ────────────────────────────────────────────────────────────


class TestEdgeCases:

    def test_channel_missing_optional_fields(self, tmp_history):
        tmp_history.record_play({"url": "http://minimal.com"})
        entry = tmp_history.get_recent()[0]
        assert entry["name"] == ""
        assert entry["country"] == ""
        assert entry["category"] == ""
        assert entry["play_count"] == 1

    def test_get_recent_empty_history(self, tmp_history):
        assert tmp_history.get_recent() == []

    def test_get_most_played_empty_history(self, tmp_history):
        assert tmp_history.get_most_played() == []

    def test_clear_then_record(self, tmp_history):
        tmp_history.record_play(_make_channel())
        tmp_history.clear()
        tmp_history.record_play(_make_channel(name="After Clear"))
        assert len(tmp_history.get_recent()) == 1
        assert tmp_history.get_recent()[0]["name"] == "After Clear"

    def test_remove_then_record_same_url(self, tmp_history):
        ch = _make_channel()
        tmp_history.record_play(ch)
        tmp_history.record_play(ch)
        assert tmp_history.get_recent()[0]["play_count"] == 2

        tmp_history.remove(ch["url"])
        tmp_history.record_play(ch)
        assert tmp_history.get_recent()[0]["play_count"] == 1  # reset

    def test_max_entries_one(self, tmp_path):
        filepath = str(tmp_path / "watch_history.json")
        wh = WatchHistory(filepath=filepath, max_entries=1)

        wh.record_play(_make_channel(name="First", url="http://1.com"))
        wh.record_play(_make_channel(name="Second", url="http://2.com"))

        recent = wh.get_recent(limit=100)
        assert len(recent) == 1
        assert recent[0]["name"] == "Second"
