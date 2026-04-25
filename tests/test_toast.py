"""
Unit tests for ui.toast — ToastManager & _Toast.

All tests use a hidden Tk root (withdraw) so no window flashes on screen.
Timers are driven manually via root.update() / root.after() where possible.
"""

import sys
import os
import tkinter as tk
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.toast import ToastManager, _Toast, _TOAST_COLORS, _DEFAULT_TIMEOUT


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture()
def root():
    """Create (and later destroy) a hidden Tk root window."""
    _root = tk.Tk()
    _root.withdraw()
    # Give it a known size so geometry calculations work
    _root.geometry("800x600+100+100")
    _root.update_idletasks()
    yield _root
    try:
        _root.destroy()
    except tk.TclError:
        pass


@pytest.fixture()
def toast_mgr(root):
    """Return a ToastManager bound to the hidden root."""
    return ToastManager(root)


# ── Basic construction ───────────────────────────────────────────────────


class TestToastManagerInit:
    def test_creates_with_defaults(self, root):
        mgr = ToastManager(root)
        assert mgr._parent is root
        assert mgr._default_timeout == _DEFAULT_TIMEOUT
        assert mgr._max_toasts == 5
        assert mgr._toasts == []

    def test_custom_timeout_and_max(self, root):
        mgr = ToastManager(root, default_timeout=5000, max_toasts=3)
        assert mgr._default_timeout == 5000
        assert mgr._max_toasts == 3


# ── Showing toasts ──────────────────────────────────────────────────────


class TestShowToasts:
    def test_show_success_returns_toast(self, toast_mgr: ToastManager, root):
        t = toast_mgr.show_success("OK")
        root.update_idletasks()
        assert isinstance(t, _Toast)
        assert len(toast_mgr._toasts) == 1

    def test_show_error(self, toast_mgr, root):
        t = toast_mgr.show_error("Fail")
        root.update_idletasks()
        assert isinstance(t, _Toast)

    def test_show_info(self, toast_mgr, root):
        t = toast_mgr.show_info("FYI")
        root.update_idletasks()
        assert isinstance(t, _Toast)

    def test_show_warning(self, toast_mgr, root):
        t = toast_mgr.show_warning("Careful")
        root.update_idletasks()
        assert isinstance(t, _Toast)

    def test_toast_registered_in_manager(self, toast_mgr, root):
        toast_mgr.show_info("A")
        toast_mgr.show_error("B")
        root.update_idletasks()
        assert len(toast_mgr._toasts) == 2


# ── Stacking / max limit ────────────────────────────────────────────────


class TestStacking:
    def test_toasts_stack_vertically(self, root):
        """Each successive toast should be placed lower than the previous one."""
        mgr = ToastManager(root)
        t1 = mgr.show_info("First")
        t2 = mgr.show_info("Second")
        root.update_idletasks()
        # After restacking, toast2's y should be greater than toast1's y
        y1 = t1.winfo_y()
        y2 = t2.winfo_y()
        assert y2 > y1, f"t2.y ({y2}) should be > t1.y ({y1})"

    def test_max_toasts_enforced(self, root):
        """When max_toasts is exceeded the oldest toast is dismissed."""
        mgr = ToastManager(root, max_toasts=2)
        t1 = mgr.show_info("1")
        t2 = mgr.show_info("2")
        root.update_idletasks()
        assert len(mgr._toasts) == 2

        t3 = mgr.show_info("3")
        root.update_idletasks()
        assert len(mgr._toasts) == 2
        # t1 should have been dismissed
        assert t1 not in mgr._toasts
        assert t3 in mgr._toasts


# ── Dismiss ──────────────────────────────────────────────────────────────


class TestDismiss:
    def test_manual_dismiss(self, toast_mgr, root):
        t = toast_mgr.show_info("Bye")
        root.update_idletasks()
        assert len(toast_mgr._toasts) == 1
        t.dismiss()
        root.update_idletasks()
        assert len(toast_mgr._toasts) == 0

    def test_dismiss_all(self, toast_mgr, root):
        toast_mgr.show_info("A")
        toast_mgr.show_error("B")
        toast_mgr.show_warning("C")
        root.update_idletasks()
        assert len(toast_mgr._toasts) == 3
        toast_mgr.dismiss_all()
        root.update_idletasks()
        assert len(toast_mgr._toasts) == 0

    def test_double_dismiss_is_safe(self, toast_mgr, root):
        t = toast_mgr.show_info("X")
        root.update_idletasks()
        t.dismiss()
        t.dismiss()  # should not raise
        assert len(toast_mgr._toasts) == 0

    def test_dismiss_restacks_remaining(self, root):
        mgr = ToastManager(root)
        t1 = mgr.show_info("A")
        t2 = mgr.show_info("B")
        t3 = mgr.show_info("C")
        root.update_idletasks()

        old_y3 = t3.winfo_y()
        t1.dismiss()
        root.update_idletasks()

        # t3 should have moved up
        new_y3 = t3.winfo_y()
        assert new_y3 < old_y3, "Remaining toasts should restack upward"


# ── Custom timeout ───────────────────────────────────────────────────────


class TestTimeout:
    def test_custom_timeout_on_show(self, toast_mgr, root):
        t = toast_mgr.show_info("Quick", timeout=500)
        root.update_idletasks()
        assert t._timeout == 500

    def test_default_timeout_used(self, root):
        mgr = ToastManager(root, default_timeout=7000)
        t = mgr.show_info("Slow")
        root.update_idletasks()
        assert t._timeout == 7000


# ── Toast type colours ───────────────────────────────────────────────────


class TestToastTypes:
    """Ensure all four toast types are defined."""

    @pytest.mark.parametrize("ttype", ["success", "error", "info", "warning"])
    def test_type_in_palette(self, ttype):
        assert ttype in _TOAST_COLORS
        assert "accent" in _TOAST_COLORS[ttype]
        assert "icon" in _TOAST_COLORS[ttype]

    def test_success_colour(self):
        assert _TOAST_COLORS["success"]["accent"] == "#13a10e"

    def test_error_colour(self):
        assert _TOAST_COLORS["error"]["accent"] == "#f04a58"

    def test_info_colour(self):
        assert _TOAST_COLORS["info"]["accent"] == "#4da6ff"

    def test_warning_colour(self):
        assert _TOAST_COLORS["warning"]["accent"] == "#ffb900"


# ── Edge cases ───────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_message(self, toast_mgr, root):
        t = toast_mgr.show_info("")
        root.update_idletasks()
        assert isinstance(t, _Toast)

    def test_long_message_wraps(self, toast_mgr, root):
        long_msg = "A" * 300
        t = toast_mgr.show_info(long_msg)
        root.update_idletasks()
        assert isinstance(t, _Toast)

    def test_show_after_dismiss_all(self, toast_mgr, root):
        toast_mgr.show_info("A")
        root.update_idletasks()
        toast_mgr.dismiss_all()
        root.update_idletasks()
        t = toast_mgr.show_success("B")
        root.update_idletasks()
        assert len(toast_mgr._toasts) == 1
        assert t in toast_mgr._toasts

    def test_zero_timeout_no_auto_dismiss(self, toast_mgr, root):
        """Timeout=0 means the toast never auto-dismisses."""
        t = toast_mgr.show_info("Persistent", timeout=0)
        root.update_idletasks()
        # Process events for a bit — toast should still be alive
        for _ in range(10):
            root.update()
        assert len(toast_mgr._toasts) == 1
        assert not t._closed
