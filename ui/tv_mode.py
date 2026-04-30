"""TV Mode — Fullscreen Google TV / Android Streamer lean-back interface.

Provides a fullscreen channel browser navigated entirely with arrow keys,
Enter, and Escape — designed for use with a remote control or keyboard,
no mouse required. Channels are displayed in horizontal rows grouped by
category, with Favorites and Recent at the top.

Keyboard Controls:
    Arrow keys  — Navigate between channels
    Enter       — Play selected channel
    Escape/Back — Return from player / exit TV mode
    0-9         — Channel number quick-jump
    F           — Toggle fullscreen on player
    M           — Mute/unmute
    +/-         — Volume up/down
"""

import tkinter as tk
from tkinter import ttk
import time
from typing import Optional, Dict, Any, List, Callable

from utils.logger import get_logger
from utils.favorites import FavoritesManager
from utils.history import WatchHistory
import config

logger = get_logger(__name__)

# ─── TV Mode Color Palette ──────────────────────────────────────────────────
class TVColors:
    """Dark theme colors for TV mode (optimized for 10-foot viewing)."""
    BG = "#0D0D0D"
    BG_ROW = "#141414"
    BG_CARD = "#1E1E1E"
    BG_CARD_FOCUS = "#2A2A2A"
    BORDER_FOCUS = "#4CC2FF"
    BORDER_NORMAL = "#333333"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#A0A0A0"
    TEXT_DIM = "#666666"
    ACCENT = "#4CC2FF"
    CATEGORY_BG = "#1A1A1A"
    NOW_PLAYING_BG = "#1B2838"
    OVERLAY_BG = "#000000"
    SUCCESS = "#6CCB5F"
    LIVE_BADGE = "#E53935"


# ─── TV Mode Constants ──────────────────────────────────────────────────────
CARD_WIDTH = 220
CARD_HEIGHT = 130
CARD_GAP = 16
ROW_HEIGHT = 180
ROW_LABEL_HEIGHT = 36
VISIBLE_ROWS = 5
SCROLL_SPEED = 4
NUMBER_OVERLAY_TIMEOUT_MS = 2000
FONT_FAMILY = "Segoe UI"


class TVModeWindow(tk.Toplevel):
    """Fullscreen TV mode with Google TV-style horizontal category rows."""

    def __init__(self, parent, channels: List[Dict[str, Any]],
                 favorites_manager: FavoritesManager,
                 watch_history: WatchHistory,
                 on_play: Optional[Callable] = None,
                 on_exit: Optional[Callable] = None):
        super().__init__(parent)
        self.parent = parent
        self._all_channels = channels
        self._favorites_manager = favorites_manager
        self._watch_history = watch_history
        self._on_play = on_play
        self._on_exit = on_exit

        # Navigation state
        self._rows: List[Dict[str, Any]] = []  # [{label, channels}]
        self._row_index = 0  # Current focused row
        self._col_index = 0  # Current focused column within row
        self._col_offsets: List[int] = []  # Per-row horizontal scroll offset

        # Number entry for channel jump
        self._number_buffer = ""
        self._number_timer = None

        # UI elements
        self._canvas = None
        self._info_bar = None
        self._number_overlay = None
        self._card_widgets: List[List[Optional[tk.Frame]]] = []

        self._build_rows()
        self._setup_window()
        self._create_ui()
        self._bind_keys()
        self._draw()

    # ─── Data Preparation ───────────────────────────────────────────────────

    def _build_rows(self):
        """Organize channels into category rows with Favorites and Recent at top."""
        self._rows = []

        # Favorites row
        fav_names = self._favorites_manager.get_favorites() if self._favorites_manager else []
        if fav_names:
            fav_channels = [ch for ch in self._all_channels
                           if ch.get('name') in fav_names and ch.get('is_working')]
            if fav_channels:
                self._rows.append({"label": "★ Favorites", "channels": fav_channels})

        # Recent row
        recent = self._watch_history.get_recent(limit=20) if self._watch_history else []
        if recent:
            recent_channels = []
            for name in recent:
                for ch in self._all_channels:
                    if ch.get('name') == name and ch.get('is_working'):
                        recent_channels.append(ch)
                        break
            if recent_channels:
                self._rows.append({"label": "🕐 Recent", "channels": recent_channels})

        # Category rows (only working channels)
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for ch in self._all_channels:
            if not ch.get('is_working'):
                continue
            cat = ch.get('category', 'Other') or 'Other'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(ch)

        # Sort categories by channel count (most popular first)
        for cat in sorted(categories, key=lambda c: len(categories[c]), reverse=True):
            if len(categories[cat]) >= 1:
                self._rows.append({"label": f"  {cat}", "channels": categories[cat]})

        # Initialize column offsets
        self._col_offsets = [0] * len(self._rows)

    # ─── Window Setup ───────────────────────────────────────────────────────

    def _setup_window(self):
        """Configure fullscreen window."""
        self.title(f"{config.APP_NAME} — TV Mode")
        self.configure(bg=TVColors.BG)
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.focus_force()

        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._exit_tv_mode)

    # ─── UI Creation ────────────────────────────────────────────────────────

    def _create_ui(self):
        """Create the TV mode interface."""
        # Main canvas (fills entire screen)
        self._canvas = tk.Canvas(
            self, bg=TVColors.BG, highlightthickness=0,
            borderwidth=0
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Info bar at bottom
        self._info_frame = tk.Frame(self, bg=TVColors.NOW_PLAYING_BG, height=56)
        self._info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self._info_frame.pack_propagate(False)

        # App name on left
        tk.Label(
            self._info_frame, text=f"📺 {config.APP_NAME}",
            bg=TVColors.NOW_PLAYING_BG, fg=TVColors.ACCENT,
            font=(FONT_FAMILY, 14, "bold")
        ).pack(side=tk.LEFT, padx=20, pady=10)

        # Navigation hint on right
        tk.Label(
            self._info_frame,
            text="←→↑↓ Navigate  •  Enter Play  •  Esc Exit  •  0-9 Jump",
            bg=TVColors.NOW_PLAYING_BG, fg=TVColors.TEXT_DIM,
            font=(FONT_FAMILY, 11)
        ).pack(side=tk.RIGHT, padx=20, pady=10)

        # Current channel info (center)
        self._info_label = tk.Label(
            self._info_frame, text="",
            bg=TVColors.NOW_PLAYING_BG, fg=TVColors.TEXT_PRIMARY,
            font=(FONT_FAMILY, 13)
        )
        self._info_label.pack(side=tk.LEFT, padx=40, pady=10)

        # Number overlay (hidden by default)
        self._number_label = tk.Label(
            self, text="", bg=TVColors.OVERLAY_BG, fg=TVColors.ACCENT,
            font=(FONT_FAMILY, 48, "bold"), padx=20, pady=10
        )

    # ─── Drawing ────────────────────────────────────────────────────────────

    def _draw(self):
        """Render the channel grid on canvas."""
        self._canvas.delete("all")

        if not self._rows:
            self._canvas.create_text(
                self.winfo_screenwidth() // 2,
                self.winfo_screenheight() // 2,
                text="No channels available.\nPress Escape to exit.",
                fill=TVColors.TEXT_SECONDARY,
                font=(FONT_FAMILY, 24),
                justify=tk.CENTER
            )
            return

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight() - 56  # Subtract info bar
        y_offset = 30

        # Determine visible row range (centered on current row)
        start_row = max(0, self._row_index - 2)
        end_row = min(len(self._rows), start_row + VISIBLE_ROWS)
        if end_row - start_row < VISIBLE_ROWS and start_row > 0:
            start_row = max(0, end_row - VISIBLE_ROWS)

        for row_idx in range(start_row, end_row):
            row = self._rows[row_idx]
            is_active_row = (row_idx == self._row_index)

            # Row label
            label_color = TVColors.ACCENT if is_active_row else TVColors.TEXT_SECONDARY
            self._canvas.create_text(
                30, y_offset + 4,
                text=row["label"],
                fill=label_color,
                font=(FONT_FAMILY, 15 if is_active_row else 13,
                      "bold" if is_active_row else "normal"),
                anchor="nw"
            )

            # Channel count
            count_text = f"{len(row['channels'])} channels"
            self._canvas.create_text(
                30 + len(row["label"]) * 10 + 20, y_offset + 7,
                text=count_text,
                fill=TVColors.TEXT_DIM,
                font=(FONT_FAMILY, 10),
                anchor="nw"
            )

            y_offset += ROW_LABEL_HEIGHT

            # Draw channel cards in this row
            channels = row["channels"]
            x_start = 30 - self._col_offsets[row_idx] * (CARD_WIDTH + CARD_GAP)

            for col_idx, ch in enumerate(channels):
                x = x_start + col_idx * (CARD_WIDTH + CARD_GAP)

                # Skip off-screen cards (optimization)
                if x + CARD_WIDTH < -CARD_WIDTH or x > screen_w + CARD_WIDTH:
                    continue

                is_focused = (is_active_row and col_idx == self._col_index)
                self._draw_card(x, y_offset, ch, is_focused, col_idx)

            y_offset += CARD_HEIGHT + 24  # Card height + bottom padding

        # Update info bar with focused channel info
        self._update_info_bar()

    def _draw_card(self, x: int, y: int, channel: Dict[str, Any],
                   is_focused: bool, index: int):
        """Draw a single channel card."""
        # Card background
        if is_focused:
            # Focused card: larger, brighter, with accent border
            pad = 4
            self._canvas.create_rectangle(
                x - pad, y - pad,
                x + CARD_WIDTH + pad, y + CARD_HEIGHT + pad,
                fill=TVColors.BG_CARD_FOCUS,
                outline=TVColors.BORDER_FOCUS,
                width=3,
                tags="card"
            )
            # Glow effect
            self._canvas.create_rectangle(
                x - pad - 2, y - pad - 2,
                x + CARD_WIDTH + pad + 2, y + CARD_HEIGHT + pad + 2,
                fill="",
                outline=TVColors.BORDER_FOCUS,
                width=1,
                stipple="gray25",
                tags="card"
            )
        else:
            self._canvas.create_rectangle(
                x, y, x + CARD_WIDTH, y + CARD_HEIGHT,
                fill=TVColors.BG_CARD,
                outline=TVColors.BORDER_NORMAL,
                width=1,
                tags="card"
            )

        # Channel number badge (top-left)
        global_idx = self._get_global_channel_number(channel)
        if global_idx is not None:
            self._canvas.create_text(
                x + 8, y + 8,
                text=str(global_idx),
                fill=TVColors.TEXT_DIM if not is_focused else TVColors.ACCENT,
                font=(FONT_FAMILY, 9),
                anchor="nw"
            )

        # Channel name (center, bold)
        name = channel.get('name', 'Unknown')
        # Truncate long names
        if len(name) > 22:
            name = name[:20] + "…"
        name_color = TVColors.TEXT_PRIMARY if is_focused else TVColors.TEXT_SECONDARY
        self._canvas.create_text(
            x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2 - 8,
            text=name,
            fill=name_color,
            font=(FONT_FAMILY, 12 if is_focused else 11, "bold" if is_focused else "normal"),
            anchor="center",
            width=CARD_WIDTH - 16
        )

        # Category/Country (below name)
        cat = channel.get('category', '')
        country = channel.get('country', '')
        subtitle = f"{cat}" + (f" • {country}" if country else "")
        if len(subtitle) > 28:
            subtitle = subtitle[:26] + "…"
        self._canvas.create_text(
            x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2 + 16,
            text=subtitle,
            fill=TVColors.TEXT_DIM,
            font=(FONT_FAMILY, 10),
            anchor="center"
        )

        # Live badge (top-right)
        if channel.get('is_working'):
            self._canvas.create_oval(
                x + CARD_WIDTH - 18, y + 8,
                x + CARD_WIDTH - 8, y + 18,
                fill=TVColors.SUCCESS,
                outline=""
            )

        # Favorite star
        if self._favorites_manager and channel.get('name') in (
                self._favorites_manager.get_favorites() or []):
            self._canvas.create_text(
                x + CARD_WIDTH - 20, y + CARD_HEIGHT - 16,
                text="★",
                fill="#FFB900",
                font=(FONT_FAMILY, 14),
                anchor="center"
            )

    def _update_info_bar(self):
        """Update the info bar with the focused channel's details."""
        if not self._rows:
            return
        row = self._rows[self._row_index]
        channels = row["channels"]
        if 0 <= self._col_index < len(channels):
            ch = channels[self._col_index]
            name = ch.get('name', 'Unknown')
            cat = ch.get('category', '')
            country = ch.get('country', '')
            num = self._get_global_channel_number(ch)
            num_text = f"Ch.{num} — " if num is not None else ""
            self._info_label.config(
                text=f"{num_text}{name}  |  {cat}  |  {country}"
            )

    # ─── Navigation ─────────────────────────────────────────────────────────

    def _bind_keys(self):
        """Bind keyboard navigation."""
        self.bind("<Up>", self._nav_up)
        self.bind("<Down>", self._nav_down)
        self.bind("<Left>", self._nav_left)
        self.bind("<Right>", self._nav_right)
        self.bind("<Return>", self._play_selected)
        self.bind("<KP_Enter>", self._play_selected)
        self.bind("<Escape>", self._on_escape)
        self.bind("<BackSpace>", self._on_escape)
        self.bind("<F11>", lambda e: self._exit_tv_mode())

        # Number keys for channel jump
        for i in range(10):
            self.bind(str(i), self._on_number_key)
            self.bind(f"<KP_{i}>", self._on_number_key)

        # Volume keys
        self.bind("<plus>", lambda e: self._volume_change(5))
        self.bind("<KP_Add>", lambda e: self._volume_change(5))
        self.bind("<minus>", lambda e: self._volume_change(-5))
        self.bind("<KP_Subtract>", lambda e: self._volume_change(-5))

    def _nav_up(self, event=None):
        """Move to previous row."""
        if self._row_index > 0:
            self._row_index -= 1
            # Clamp column to row length
            row_len = len(self._rows[self._row_index]["channels"])
            if self._col_index >= row_len:
                self._col_index = max(0, row_len - 1)
            self._draw()

    def _nav_down(self, event=None):
        """Move to next row."""
        if self._row_index < len(self._rows) - 1:
            self._row_index += 1
            # Clamp column to row length
            row_len = len(self._rows[self._row_index]["channels"])
            if self._col_index >= row_len:
                self._col_index = max(0, row_len - 1)
            self._draw()

    def _nav_left(self, event=None):
        """Move left in current row."""
        if self._col_index > 0:
            self._col_index -= 1
            # Scroll row if needed
            if self._col_index < self._col_offsets[self._row_index]:
                self._col_offsets[self._row_index] = self._col_index
            self._draw()

    def _nav_right(self, event=None):
        """Move right in current row."""
        row_len = len(self._rows[self._row_index]["channels"])
        if self._col_index < row_len - 1:
            self._col_index += 1
            # Scroll row if card goes off-screen
            screen_w = self.winfo_screenwidth()
            visible_cards = (screen_w - 60) // (CARD_WIDTH + CARD_GAP)
            if self._col_index >= self._col_offsets[self._row_index] + visible_cards:
                self._col_offsets[self._row_index] = self._col_index - visible_cards + 1
            self._draw()

    def _play_selected(self, event=None):
        """Play the currently focused channel."""
        if not self._rows:
            return
        row = self._rows[self._row_index]
        channels = row["channels"]
        if 0 <= self._col_index < len(channels):
            channel = channels[self._col_index]
            if self._on_play:
                self._on_play(channel)

    def _on_escape(self, event=None):
        """Exit TV mode."""
        self._exit_tv_mode()

    def _exit_tv_mode(self):
        """Close TV mode and return to main window."""
        self.attributes("-fullscreen", False)
        self.attributes("-topmost", False)
        if self._on_exit:
            self._on_exit()
        self.destroy()

    # ─── Channel Number Jump ────────────────────────────────────────────────

    def _on_number_key(self, event):
        """Handle number key press for channel jump."""
        digit = event.char if event.char.isdigit() else event.keysym[-1]
        if not digit.isdigit():
            return

        self._number_buffer += digit
        self._show_number_overlay()

        # Reset timer
        if self._number_timer:
            self.after_cancel(self._number_timer)
        self._number_timer = self.after(NUMBER_OVERLAY_TIMEOUT_MS, self._execute_number_jump)

    def _show_number_overlay(self):
        """Show the channel number overlay."""
        self._number_label.config(text=f"Ch. {self._number_buffer}")
        self._number_label.place(
            relx=0.5, rely=0.15, anchor="center"
        )

    def _execute_number_jump(self):
        """Jump to the entered channel number."""
        self._number_timer = None
        try:
            target = int(self._number_buffer)
        except ValueError:
            self._number_buffer = ""
            self._number_label.place_forget()
            return

        self._number_buffer = ""
        self._number_label.place_forget()

        # Find channel by global index
        global_idx = 0
        for row_idx, row in enumerate(self._rows):
            for col_idx, ch in enumerate(row["channels"]):
                global_idx += 1
                if global_idx == target:
                    self._row_index = row_idx
                    self._col_index = col_idx
                    # Adjust scroll offset
                    screen_w = self.winfo_screenwidth()
                    visible_cards = (screen_w - 60) // (CARD_WIDTH + CARD_GAP)
                    if col_idx >= visible_cards:
                        self._col_offsets[row_idx] = col_idx - visible_cards // 2
                    else:
                        self._col_offsets[row_idx] = 0
                    self._draw()
                    return

    def _get_global_channel_number(self, channel: Dict[str, Any]) -> Optional[int]:
        """Get the global sequential number for a channel across all rows."""
        idx = 0
        for row in self._rows:
            for ch in row["channels"]:
                idx += 1
                if ch is channel:
                    return idx
        return None

    # ─── Volume ─────────────────────────────────────────────────────────────

    def _volume_change(self, delta: int):
        """Adjust volume (delegates to parent's player if active)."""
        # This would integrate with the player window if open
        pass

    # ─── Public Methods ─────────────────────────────────────────────────────

    def refresh_channels(self, channels: List[Dict[str, Any]]):
        """Refresh channel data (e.g., after scan completes)."""
        self._all_channels = channels
        self._build_rows()
        self._col_offsets = [0] * len(self._rows)
        if self._row_index >= len(self._rows):
            self._row_index = 0
        if self._rows:
            row_len = len(self._rows[self._row_index]["channels"])
            if self._col_index >= row_len:
                self._col_index = max(0, row_len - 1)
        self._draw()
