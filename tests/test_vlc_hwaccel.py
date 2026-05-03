"""Tests for HW acceleration argument selection (Issue #166)."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.vlc_controller import get_vlc_hardware_acceleration_args


class TestHWAccelArgs(unittest.TestCase):
    def test_software_args_omit_hwaccel(self):
        args = get_vlc_hardware_acceleration_args(prefer_hwaccel=False)
        joined = " ".join(args)
        self.assertNotIn("--avcodec-hw", joined)

    def test_software_args_keep_safe_baseline(self):
        args = get_vlc_hardware_acceleration_args(prefer_hwaccel=False)
        for must_have in ("--quiet", "--no-lua", "--network-caching=1000"):
            self.assertIn(must_have, args)

    @patch.object(sys, "platform", "win32")
    def test_windows_prefers_d3d11va_when_enabled(self):
        args = get_vlc_hardware_acceleration_args(prefer_hwaccel=True)
        self.assertIn("--avcodec-hw=d3d11va", args)
        self.assertIn("--avcodec-fast", args)

    @patch.object(sys, "platform", "win32")
    def test_windows_respects_opt_out_env(self):
        with patch.dict(os.environ, {"TV_VIEWER_NO_HWACCEL": "1"}):
            args = get_vlc_hardware_acceleration_args(prefer_hwaccel=True)
            self.assertNotIn("--avcodec-hw=d3d11va", " ".join(args))

    @patch.object(sys, "platform", "darwin")
    def test_macos_uses_videotoolbox(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TV_VIEWER_NO_HWACCEL", None)
            args = get_vlc_hardware_acceleration_args(prefer_hwaccel=True)
            self.assertIn("--avcodec-hw=videotoolbox", args)

    @patch.object(sys, "platform", "linux")
    def test_linux_uses_any(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TV_VIEWER_NO_HWACCEL", None)
            args = get_vlc_hardware_acceleration_args(prefer_hwaccel=True)
            self.assertIn("--avcodec-hw=any", args)


if __name__ == "__main__":
    unittest.main()
