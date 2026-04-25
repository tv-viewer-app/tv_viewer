"""
Toast notification system for TV Viewer — Fluent Design dark theme.

Provides non-blocking popup notifications that stack in the top-right
corner of the parent window and auto-dismiss after a configurable delay.

Usage:
    from ui.toast import ToastManager

    toast = ToastManager(root)
    toast.show_success("Channel loaded successfully")
    toast.show_error("Stream connection failed")
    toast.show_info("Scanning 1,500 channels...")
    toast.show_warning("VLC not found on system")
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

# Toast-type colour definitions (Fluent Design dark palette)
_TOAST_COLORS = {
    "success": {"accent": "#13a10e", "icon": "✅"},
    "error":   {"accent": "#f04a58", "icon": "❌"},
    "info":    {"accent": "#4da6ff", "icon": "ℹ️"},
    "warning": {"accent": "#ffb900", "icon": "⚠️"},
}

# Shared chrome colours
_BG      = "#2d2c31"
_TEXT    = "#ffffff"
_BORDER  = "#3b3a3f"
_CLOSE   = "#9d9d9d"

# Layout / timing defaults
_TOAST_WIDTH     = 340
_PADDING_X       = 16
_PADDING_Y       = 12
_CORNER_RADIUS   = 8       # visual only – tk Toplevel is rectangular
_MARGIN_RIGHT    = 18      # gap from parent's right edge
_MARGIN_TOP      = 12      # gap from parent's top edge
_STACK_GAP       = 8       # vertical gap between stacked toasts
_DEFAULT_TIMEOUT = 3000    # ms


class _Toast(tk.Toplevel):
    """A single toast notification popup."""

    def __init__(
        self,
        manager: "ToastManager",
        message: str,
        toast_type: str = "info",
        timeout: int = _DEFAULT_TIMEOUT,
    ):
        super().__init__(manager._parent)

        self._manager = manager
        self._timeout = timeout
        self._dismiss_timer: Optional[str] = None
        self._anim_timer: Optional[str] = None
        self._closed = False

        # ── Window chrome ────────────────────────────────────────────
        self.overrideredirect(True)              # frameless
        self.attributes("-topmost", True)        # always on top
        self.configure(bg=_BORDER)               # 1-px border hack

        colours = _TOAST_COLORS.get(toast_type, _TOAST_COLORS["info"])
        accent = colours["accent"]
        icon   = colours["icon"]

        # ── Inner frame (the visible "card") ─────────────────────────
        card = tk.Frame(self, bg=_BG)
        card.pack(padx=1, pady=1, fill="both", expand=True)

        # Accent stripe on the left edge
        stripe = tk.Frame(card, bg=accent, width=4)
        stripe.pack(side="left", fill="y")

        # Content area
        body = tk.Frame(card, bg=_BG)
        body.pack(side="left", fill="both", expand=True,
                  padx=_PADDING_X, pady=_PADDING_Y)

        # Close button (top-right of body)
        close_btn = tk.Label(
            body, text="✕", font=("Segoe UI", 10), fg=_CLOSE, bg=_BG,
            cursor="hand2",
        )
        close_btn.place(relx=1.0, rely=0.0, anchor="ne")
        close_btn.bind("<Button-1>", lambda _e: self.dismiss())

        # Icon + message in a horizontal row
        row = tk.Frame(body, bg=_BG)
        row.pack(anchor="w", fill="x", padx=(0, 20))  # 20 = room for ✕

        icon_lbl = tk.Label(
            row, text=icon, font=("Segoe UI Emoji", 13), fg=_TEXT, bg=_BG,
        )
        icon_lbl.pack(side="left", padx=(0, 8))

        msg_lbl = tk.Label(
            row, text=message, font=("Segoe UI", 11), fg=_TEXT, bg=_BG,
            wraplength=_TOAST_WIDTH - _PADDING_X * 2 - 50,
            justify="left", anchor="w",
        )
        msg_lbl.pack(side="left", fill="x", expand=True)

        # ── Geometry ─────────────────────────────────────────────────
        # Force layout to determine natural height
        self.update_idletasks()
        req_h = card.winfo_reqheight() + 2  # +2 for border
        self._width = _TOAST_WIDTH
        self._height = req_h

        # Animate entrance
        self._animate_in()

    # ── Animation ────────────────────────────────────────────────────

    def _animate_in(self):
        """Fade in if platform supports it, otherwise slide in from right."""
        try:
            # Try opacity-based fade-in
            self.attributes("-alpha", 0.0)
            self._fade_step(0.0)
        except tk.TclError:
            # Fallback: instant show (slide handled via position)
            self._on_animation_complete()

    def _fade_step(self, alpha: float):
        """Incrementally raise opacity from 0 → 1."""
        if self._closed:
            return
        alpha = min(alpha + 0.12, 1.0)
        try:
            self.attributes("-alpha", alpha)
        except tk.TclError:
            return  # window destroyed mid-animation
        if alpha < 1.0:
            self._anim_timer = self.after(16, self._fade_step, alpha)  # ~60 fps
        else:
            self._on_animation_complete()

    def _on_animation_complete(self):
        """Start the auto-dismiss countdown once the toast is fully visible."""
        if self._timeout > 0:
            self._dismiss_timer = self.after(self._timeout, self.dismiss)

    # ── Dismiss ──────────────────────────────────────────────────────

    def dismiss(self):
        """Remove the toast and re-stack remaining ones."""
        if self._closed:
            return
        self._closed = True
        self._cancel_timers()
        try:
            self.destroy()
        except tk.TclError:
            pass
        self._manager._remove(self)

    def _cancel_timers(self):
        for timer in (self._dismiss_timer, self._anim_timer):
            if timer is not None:
                try:
                    self.after_cancel(timer)
                except (tk.TclError, ValueError):
                    pass
        self._dismiss_timer = None
        self._anim_timer = None

    # ── Positioning helper ───────────────────────────────────────────

    def place_at(self, x: int, y: int):
        """Position the toast at an absolute screen coordinate."""
        self.geometry(f"{self._width}x{self._height}+{x}+{y}")


class ToastManager:
    """
    Manages a stack of toast notifications anchored to a parent window.

    Parameters
    ----------
    parent : tk.Tk | tk.Toplevel
        The root window (or any Toplevel) that toasts anchor to.
    default_timeout : int
        Default auto-dismiss delay in milliseconds (default 3 000).
    max_toasts : int
        Maximum visible toasts. Oldest are dismissed when exceeded.
    """

    def __init__(
        self,
        parent: tk.Misc,
        default_timeout: int = _DEFAULT_TIMEOUT,
        max_toasts: int = 5,
    ):
        self._parent = parent
        self._default_timeout = default_timeout
        self._max_toasts = max_toasts
        self._toasts: list[_Toast] = []

    # ── Public API ───────────────────────────────────────────────────

    def show_success(self, message: str, timeout: int | None = None) -> _Toast:
        """Show a green success toast."""
        return self._show(message, "success", timeout)

    def show_error(self, message: str, timeout: int | None = None) -> _Toast:
        """Show a red error toast."""
        return self._show(message, "error", timeout)

    def show_info(self, message: str, timeout: int | None = None) -> _Toast:
        """Show a blue informational toast."""
        return self._show(message, "info", timeout)

    def show_warning(self, message: str, timeout: int | None = None) -> _Toast:
        """Show an orange warning toast."""
        return self._show(message, "warning", timeout)

    # ── Internal ─────────────────────────────────────────────────────

    def _show(self, message: str, toast_type: str, timeout: int | None) -> _Toast:
        """Create a toast, enforce max limit, and restack."""
        if timeout is None:
            timeout = self._default_timeout

        # Enforce max visible toasts — dismiss oldest first
        while len(self._toasts) >= self._max_toasts:
            self._toasts[0].dismiss()

        toast = _Toast(self, message, toast_type, timeout)
        self._toasts.append(toast)
        self._restack()
        return toast

    def _remove(self, toast: _Toast):
        """Called by a toast when it dismisses itself."""
        try:
            self._toasts.remove(toast)
        except ValueError:
            pass
        self._restack()

    def _restack(self):
        """Recalculate positions for all visible toasts (top-right stack)."""
        try:
            px = self._parent.winfo_rootx()
            py = self._parent.winfo_rooty()
            pw = self._parent.winfo_width()
        except tk.TclError:
            return  # parent destroyed

        x = px + pw - _TOAST_WIDTH - _MARGIN_RIGHT
        y = py + _MARGIN_TOP

        for toast in self._toasts:
            if toast._closed:
                continue
            toast.place_at(x, y)
            y += toast._height + _STACK_GAP

    def dismiss_all(self):
        """Dismiss every active toast immediately."""
        for toast in list(self._toasts):
            toast.dismiss()
