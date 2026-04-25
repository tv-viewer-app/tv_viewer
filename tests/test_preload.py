"""Tests for channel preloading in PlayerWindow."""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# Stub out heavy dependencies so we can test preload logic without VLC/Tk
_vlc_mod = types.ModuleType("vlc")


class _FakeState:
    Error = 0
    Ended = 1
    Playing = 3
    Paused = 4


_vlc_mod.State = _FakeState
_vlc_mod.Instance = MagicMock
_vlc_mod.MediaPlayer = MagicMock
sys.modules.setdefault("vlc", _vlc_mod)


class _FakeVLCController:
    """Minimal stand-in for VLCController that supports preload testing."""

    def __init__(self):
        self._instance = MagicMock()
        self._player = MagicMock()
        self._preload_player = None
        self._preload_url = None

    @property
    def is_available(self):
        return True

    @property
    def instance(self):
        return self._instance

    @property
    def player(self):
        return self._player

    @property
    def preload_player(self):
        return self._preload_player

    @property
    def preload_url(self):
        return self._preload_url

    def create_preload_player(self, url):
        self._preload_player = MagicMock()
        self._preload_url = url
        return True

    def release_preload(self):
        if self._preload_player:
            self._preload_player.stop()
            self._preload_player.release()
        self._preload_player = None
        self._preload_url = None


class _FakePlayerWindow:
    """Minimal stand-in that inherits preload methods from PlayerWindow source."""

    def __init__(self, channel_list, channel_index):
        # Copied from PlayerWindow.__init__ — only preload-related state
        self.channel_list = channel_list
        self.channel_index = channel_index
        self.channel = channel_list[channel_index] if channel_list else {}
        self.vlc = _FakeVLCController()
        self.is_playing = True
        self.volume_var = MagicMock(get=MagicMock(return_value=80))
        self.video_canvas = MagicMock(winfo_id=MagicMock(return_value=12345))
        self.play_btn = MagicMock()
        self.time_label = MagicMock()
        self._playback_confirmed = False
        self._preload_index = None
        self._preload_job = None
        self._after_callbacks = {}
        self._after_counter = 0

    # Emulate tkinter after/after_cancel
    def after(self, ms, func):
        self._after_counter += 1
        self._after_callbacks[self._after_counter] = func
        return self._after_counter

    def after_cancel(self, job_id):
        self._after_callbacks.pop(job_id, None)

    def fire_after(self, job_id):
        func = self._after_callbacks.pop(job_id, None)
        if func:
            func()


# Inject the real preload methods from the source module
from ui.player_window import PlayerWindow as _Real

for name in (
    "_schedule_preload",
    "_preload_next_channel",
    "_release_preload",
):
    setattr(_FakePlayerWindow, name, getattr(_Real, name))

# Copy the static method properly so self isn't passed
_FakePlayerWindow._resolve_channel_url = staticmethod(_Real._resolve_channel_url)


def _make_channels(n=5):
    return [
        {"name": f"Channel {i}", "url": f"http://stream.example.com/ch{i}"}
        for i in range(n)
    ]


class TestResolveChannelUrl(unittest.TestCase):
    """_resolve_channel_url static helper."""

    def test_single_url(self):
        ch = {"url": "http://example.com/stream"}
        self.assertEqual(
            _FakePlayerWindow._resolve_channel_url(ch),
            "http://example.com/stream",
        )

    def test_multiple_urls_uses_working_index(self):
        ch = {
            "urls": ["http://a.com/1", "http://b.com/2", "http://c.com/3"],
            "working_url_index": 1,
        }
        self.assertEqual(
            _FakePlayerWindow._resolve_channel_url(ch), "http://b.com/2"
        )

    def test_no_url_returns_none(self):
        self.assertIsNone(_FakePlayerWindow._resolve_channel_url({}))

    def test_blocked_scheme_returns_none(self):
        ch = {"url": "file:///etc/passwd"}
        self.assertIsNone(_FakePlayerWindow._resolve_channel_url(ch))

    def test_rtmp_allowed(self):
        ch = {"url": "rtmp://live.example.com/stream"}
        self.assertEqual(
            _FakePlayerWindow._resolve_channel_url(ch),
            "rtmp://live.example.com/stream",
        )


class TestSchedulePreload(unittest.TestCase):
    """_schedule_preload and _preload_next_channel."""

    def test_schedule_creates_after_job(self):
        pw = _FakePlayerWindow(_make_channels(), 0)
        pw._schedule_preload()
        self.assertIsNotNone(pw._preload_job)
        self.assertIn(pw._preload_job, pw._after_callbacks)

    def test_preload_creates_player_for_next_channel(self):
        pw = _FakePlayerWindow(_make_channels(), 2)
        pw._preload_next_channel()
        self.assertEqual(pw._preload_index, 3)
        self.assertIsNotNone(pw.vlc.preload_player)
        self.assertEqual(pw.vlc.preload_url, "http://stream.example.com/ch3")

    def test_preload_noop_at_last_channel(self):
        channels = _make_channels(3)
        pw = _FakePlayerWindow(channels, 2)  # last channel
        pw._preload_next_channel()
        self.assertIsNone(pw.vlc.preload_player)
        self.assertIsNone(pw._preload_index)

    def test_preload_skips_if_already_loaded(self):
        pw = _FakePlayerWindow(_make_channels(), 1)
        pw._preload_next_channel()
        first_player = pw.vlc.preload_player
        # Call again — should not create a new player
        pw._preload_next_channel()
        self.assertIs(pw.vlc.preload_player, first_player)

    def test_reschedule_cancels_previous(self):
        pw = _FakePlayerWindow(_make_channels(), 0)
        pw._schedule_preload()
        first_job = pw._preload_job
        pw._schedule_preload()
        self.assertNotIn(first_job, pw._after_callbacks)


class TestReleasePreload(unittest.TestCase):
    def test_release_clears_state(self):
        pw = _FakePlayerWindow(_make_channels(), 0)
        pw._preload_next_channel()
        self.assertIsNotNone(pw.vlc.preload_player)
        pw._release_preload()
        self.assertIsNone(pw.vlc.preload_player)
        self.assertIsNone(pw._preload_index)
        self.assertIsNone(pw.vlc.preload_url)

    def test_release_noop_when_empty(self):
        pw = _FakePlayerWindow(_make_channels(), 0)
        pw._release_preload()  # should not raise


class TestPreloadNoChannelList(unittest.TestCase):
    def test_no_channel_list(self):
        pw = _FakePlayerWindow([], 0)
        pw.channel_list = None
        pw._preload_next_channel()
        self.assertIsNone(pw.vlc.preload_player)


if __name__ == "__main__":
    unittest.main()
