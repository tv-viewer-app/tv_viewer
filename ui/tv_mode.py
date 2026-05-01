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
    Page Up/Dn  — Jump rows quickly
    Home/End    — Jump to first/last in row
    F           — Toggle fullscreen on player
    M           — Mute/unmute
    +/-         — Volume up/down
"""

import tkinter as tk
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Set

from utils.logger import get_logger
from utils.favorites import FavoritesManager
from utils.history import WatchHistory
import config

logger = get_logger(__name__)

# ─── TV Mode Color Palette ──────────────────────────────────────────────────
class TVColors:
    """Dark theme optimized for 10-foot lean-back viewing."""
    BG = "#0A0A0F"
    BG_GRADIENT_TOP = "#0F1018"
    BG_ROW_ACTIVE = "#12121A"
    BG_CARD = "#1A1A24"
    BG_CARD_HOVER = "#222230"
    BG_CARD_FOCUS = "#1E2A3A"
    BG_CARD_FOCUS_INNER = "#243448"
    BORDER_FOCUS = "#4CC2FF"
    BORDER_FOCUS_GLOW = "#2A8ADB"
    BORDER_NORMAL = "#2A2A35"
    BORDER_SUBTLE = "#1E1E28"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B8B8C8"
    TEXT_DIM = "#6E6E80"
    TEXT_MUTED = "#4A4A5A"
    ACCENT = "#4CC2FF"
    ACCENT_SOFT = "#3A9AD9"
    CATEGORY_ICON = "#8080A0"
    INFO_BAR_BG = "#0D1520"
    INFO_BAR_BORDER = "#1A2535"
    OVERLAY_BG = "#000000E0"
    SUCCESS = "#4ADE80"
    LIVE_PULSE = "#EF4444"
    FAVORITE_STAR = "#FBBF24"
    MONOGRAM_BG_1 = "#1E3A5F"
    MONOGRAM_BG_2 = "#2D1B4E"
    MONOGRAM_BG_3 = "#1B4332"
    MONOGRAM_BG_4 = "#4A1D1D"
    TOAST_BG = "#1A1A2E"
    TOAST_BORDER = "#333348"


# ─── TV Mode Constants ──────────────────────────────────────────────────────
CARD_WIDTH = 240
CARD_HEIGHT = 140
CARD_WIDTH_FOCUS = 268
CARD_HEIGHT_FOCUS = 156
CARD_GAP = 18
ROW_HEIGHT = 200
ROW_LABEL_HEIGHT = 42
VISIBLE_ROWS = 4
ANIM_FRAMES = 8
ANIM_INTERVAL_MS = 16
NUMBER_TIMEOUT_MS = 1800
MAX_NUMBER_DIGITS = 4
FONT_FAMILY = "Segoe UI"
CLOCK_UPDATE_MS = 30000

# Category emoji mapping
CATEGORY_ICONS = {
    "News": "📰", "Sports": "⚽", "Entertainment": "🎬", "Music": "🎵",
    "Kids": "🧸", "Movies": "🎥", "Documentary": "🌍", "Science": "🔬",
    "Education": "📚", "Religious": "🕌", "Business": "💼", "Lifestyle": "🏡",
    "Food": "🍳", "Travel": "✈️", "Weather": "🌤️", "Comedy": "😂",
    "Drama": "🎭", "Culture": "🎨", "Technology": "💻", "Health": "❤️",
    "Shopping": "🛒", "Gaming": "🎮", "Animation": "🎞️", "Classic": "📺",
}


def _get_monogram_color(name: str) -> str:
    """Deterministic background color for channel monogram based on name."""
    colors = [TVColors.MONOGRAM_BG_1, TVColors.MONOGRAM_BG_2,
              TVColors.MONOGRAM_BG_3, TVColors.MONOGRAM_BG_4]
    return colors[hash(name) % len(colors)]


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
        self._rows: List[Dict[str, Any]] = []
        self._row_index = 0
        self._col_index = 0
        self._col_offsets: List[int] = []

        # Cached data (rebuilt with rows)
        self._favorite_urls: Set[str] = set()
        self._channel_numbers: Dict[int, int] = {}  # id(channel) → number
        self._max_channel_number = 0

        # Number entry
        self._number_buffer = ""
        self._number_timer = None

        # Animation state
        self._anim_id = None
        self._scroll_target_offsets: List[int] = []

        # Clock timer
        self._clock_timer = None

        # Toast state
        self._toast_timer = None

        # UI elements
        self._canvas: Optional[tk.Canvas] = None
        self._info_label: Optional[tk.Label] = None
        self._clock_label: Optional[tk.Label] = None
        self._number_label: Optional[tk.Label] = None

        self._build_rows()
        self._setup_window()
        self._create_ui()
        self._bind_keys()

        # Defer first draw to after window is mapped
        self.after(50, self._draw)
        self.after(100, self._start_clock)

    # ─── Data Preparation ───────────────────────────────────────────────────

    def _build_rows(self):
        """Organize channels into category rows with Favorites and Recent at top."""
        self._rows = []

        # Cache favorite URLs (favorites stores URLs, not names)
        self._favorite_urls = set()
        if self._favorites_manager:
            favs = self._favorites_manager.get_favorites()
            if favs:
                self._favorite_urls = set(favs) if isinstance(favs, (set, list)) else set()

        # Favorites row — match by URL
        if self._favorite_urls:
            fav_channels = [ch for ch in self._all_channels
                           if ch.get('url') in self._favorite_urls and ch.get('is_working')]
            if fav_channels:
                self._rows.append({"label": "★ Favorites", "channels": fav_channels,
                                   "icon": "⭐"})

        # Recent row — WatchHistory.get_recent() returns dicts with 'url', 'name' keys
        if self._watch_history:
            recent_entries = self._watch_history.get_recent(limit=20)
            if recent_entries:
                recent_channels = []
                seen_urls = set()
                for entry in recent_entries:
                    # entry is a dict: {url, name, country, category, last_played, play_count}
                    entry_url = entry.get('url', '') if isinstance(entry, dict) else str(entry)
                    if entry_url in seen_urls:
                        continue
                    for ch in self._all_channels:
                        if ch.get('url') == entry_url and ch.get('is_working'):
                            recent_channels.append(ch)
                            seen_urls.add(entry_url)
                            break
                if recent_channels:
                    self._rows.append({"label": "🕐 Continue Watching", "channels": recent_channels,
                                       "icon": "🕐"})

        # Most Played row (if we have history)
        if self._watch_history:
            try:
                most_played = self._watch_history.get_most_played(limit=15)
                if most_played:
                    mp_channels = []
                    seen = set()
                    for entry in most_played:
                        url = entry.get('url', '') if isinstance(entry, dict) else ''
                        if url in seen or entry.get('play_count', 0) < 2:
                            continue
                        for ch in self._all_channels:
                            if ch.get('url') == url and ch.get('is_working'):
                                mp_channels.append(ch)
                                seen.add(url)
                                break
                    if len(mp_channels) >= 3:
                        self._rows.append({"label": "🔥 Most Played", "channels": mp_channels,
                                           "icon": "🔥"})
            except Exception:
                pass

        # Category rows (only working channels, stable alphabetical order)
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for ch in self._all_channels:
            if not ch.get('is_working'):
                continue
            cat = ch.get('category', 'Other') or 'Other'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(ch)

        # Sort: larger categories first, then alphabetical for ties
        for cat in sorted(categories, key=lambda c: (-len(categories[c]), c)):
            if categories[cat]:
                icon = CATEGORY_ICONS.get(cat, "📺")
                self._rows.append({"label": f"{icon} {cat}", "channels": categories[cat],
                                   "icon": icon})

        # Initialize scroll offsets
        self._col_offsets = [0] * len(self._rows)
        self._scroll_target_offsets = [0] * len(self._rows)

        # Build canonical channel number map (deduplicated, category rows only)
        self._channel_numbers = {}
        num = 0
        seen_ids = set()
        for row in self._rows:
            for ch in row["channels"]:
                ch_id = id(ch)
                if ch_id not in seen_ids:
                    num += 1
                    self._channel_numbers[ch_id] = num
                    seen_ids.add(ch_id)
        self._max_channel_number = num

    # ─── Window Setup ───────────────────────────────────────────────────────

    def _setup_window(self):
        """Configure fullscreen window."""
        self.title(f"{config.APP_NAME} — TV Mode")
        self.configure(bg=TVColors.BG)
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._exit_tv_mode)

    # ─── UI Creation ────────────────────────────────────────────────────────

    def _create_ui(self):
        """Create the TV mode interface."""
        # Info bar at bottom (pack first so it stays below canvas)
        self._info_frame = tk.Frame(self, bg=TVColors.INFO_BAR_BG, height=60)
        self._info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self._info_frame.pack_propagate(False)

        # Separator line at top of info bar
        tk.Frame(self._info_frame, bg=TVColors.INFO_BAR_BORDER, height=1).pack(
            fill=tk.X, side=tk.TOP)

        # App branding (left)
        tk.Label(
            self._info_frame, text=f"📺 {config.APP_NAME}",
            bg=TVColors.INFO_BAR_BG, fg=TVColors.ACCENT,
            font=(FONT_FAMILY, 13, "bold")
        ).pack(side=tk.LEFT, padx=24, pady=14)

        # Channel info (center-left)
        self._info_label = tk.Label(
            self._info_frame, text="",
            bg=TVColors.INFO_BAR_BG, fg=TVColors.TEXT_PRIMARY,
            font=(FONT_FAMILY, 12)
        )
        self._info_label.pack(side=tk.LEFT, padx=20, pady=14)

        # Clock (right)
        self._clock_label = tk.Label(
            self._info_frame, text="",
            bg=TVColors.INFO_BAR_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 13)
        )
        self._clock_label.pack(side=tk.RIGHT, padx=24, pady=14)

        # Navigation hints (right of center)
        tk.Label(
            self._info_frame,
            text="↑↓←→ Navigate  │  Enter Play  │  Esc Exit  │  0-9 Jump",
            bg=TVColors.INFO_BAR_BG, fg=TVColors.TEXT_MUTED,
            font=(FONT_FAMILY, 10)
        ).pack(side=tk.RIGHT, padx=16, pady=14)

        # Main canvas
        self._canvas = tk.Canvas(
            self, bg=TVColors.BG, highlightthickness=0, borderwidth=0
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.bind("<Button-1>", self._on_canvas_click)
        self._canvas.bind("<Configure>", self._on_resize)

        # Number overlay (hidden)
        self._number_label = tk.Label(
            self, text="", bg=TVColors.OVERLAY_BG, fg=TVColors.ACCENT,
            font=(FONT_FAMILY, 56, "bold"), padx=24, pady=12
        )

        # Toast label (hidden)
        self._toast_label = tk.Label(
            self, text="", bg=TVColors.TOAST_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 14), padx=16, pady=8,
            highlightbackground=TVColors.TOAST_BORDER, highlightthickness=1
        )

    # ─── Drawing ────────────────────────────────────────────────────────────

    def _draw(self):
        """Render the channel grid on canvas."""
        canvas = self._canvas
        if not canvas:
            return
        canvas.delete("all")

        cw = canvas.winfo_width()
        ch_height = canvas.winfo_height()
        if cw < 100 or ch_height < 100:
            cw = self.winfo_screenwidth()
            ch_height = self.winfo_screenheight() - 60

        if not self._rows:
            canvas.create_text(
                cw // 2, ch_height // 2,
                text="No channels available\nPress Escape to exit",
                fill=TVColors.TEXT_SECONDARY,
                font=(FONT_FAMILY, 22),
                justify=tk.CENTER
            )
            return

        # Background gradient at top (simulated with horizontal bands)
        for i in range(6):
            alpha_hex = format(max(0, 15 - i * 2), '02x')
            color = f"#0F10{18 + i * 3:02x}"
            canvas.create_rectangle(0, i * 12, cw, (i + 1) * 12,
                                    fill=color, outline="")

        y_offset = 28

        # Visible row window (centered on focused row)
        start_row = max(0, self._row_index - 1)
        end_row = min(len(self._rows), start_row + VISIBLE_ROWS)
        if end_row - start_row < VISIBLE_ROWS and start_row > 0:
            start_row = max(0, end_row - VISIBLE_ROWS)

        for row_idx in range(start_row, end_row):
            row = self._rows[row_idx]
            is_active = (row_idx == self._row_index)
            channels = row["channels"]

            # Active row highlight band
            if is_active:
                canvas.create_rectangle(
                    0, y_offset - 6, cw, y_offset + ROW_LABEL_HEIGHT + CARD_HEIGHT_FOCUS + 12,
                    fill=TVColors.BG_ROW_ACTIVE, outline=""
                )

            # Row label with channel count
            label_font_size = 16 if is_active else 13
            label_weight = "bold" if is_active else "normal"
            label_color = TVColors.TEXT_PRIMARY if is_active else TVColors.TEXT_SECONDARY
            canvas.create_text(
                32, y_offset + 6,
                text=row["label"],
                fill=label_color,
                font=(FONT_FAMILY, label_font_size, label_weight),
                anchor="nw"
            )

            # Channel count (use bbox for proper positioning)
            count_text = f"  {len(channels)}"
            label_bbox = canvas.bbox(canvas.find_all()[-1])
            count_x = (label_bbox[2] + 12) if label_bbox else 200
            canvas.create_text(
                count_x, y_offset + 10,
                text=count_text,
                fill=TVColors.TEXT_DIM,
                font=(FONT_FAMILY, 11),
                anchor="nw"
            )

            y_offset += ROW_LABEL_HEIGHT

            # Cards
            scroll_offset = self._col_offsets[row_idx]
            x_start = 32 - scroll_offset * (CARD_WIDTH + CARD_GAP)

            for col_idx, channel in enumerate(channels):
                is_focused = (is_active and col_idx == self._col_index)
                card_w = CARD_WIDTH_FOCUS if is_focused else CARD_WIDTH
                card_h = CARD_HEIGHT_FOCUS if is_focused else CARD_HEIGHT
                x = x_start + col_idx * (CARD_WIDTH + CARD_GAP)

                # Center focused card vertically in row
                y_card = y_offset
                if is_focused:
                    y_card -= (CARD_HEIGHT_FOCUS - CARD_HEIGHT) // 2

                # Cull off-screen cards
                if x + card_w < -50 or x > cw + 50:
                    continue

                self._draw_card(canvas, x, y_card, card_w, card_h,
                                channel, is_focused, is_active)

            y_offset += CARD_HEIGHT_FOCUS + 20

        # Update info bar
        self._update_info_bar()

    def _draw_card(self, canvas: tk.Canvas, x: int, y: int,
                   w: int, h: int, channel: Dict[str, Any],
                   is_focused: bool, is_active_row: bool):
        """Draw a single channel card with depth and visual hierarchy."""
        name = channel.get('name', 'Unknown')
        ch_url = channel.get('url', '')

        if is_focused:
            # Outer glow
            canvas.create_rectangle(
                x - 4, y - 4, x + w + 4, y + h + 4,
                fill="", outline=TVColors.BORDER_FOCUS_GLOW, width=2,
                stipple="gray50"
            )
            # Card body
            canvas.create_rectangle(
                x, y, x + w, y + h,
                fill=TVColors.BG_CARD_FOCUS, outline=TVColors.BORDER_FOCUS, width=2
            )
            # Inner gradient band (top accent)
            canvas.create_rectangle(
                x + 1, y + 1, x + w - 1, y + 4,
                fill=TVColors.BORDER_FOCUS, outline=""
            )
        elif is_active_row:
            canvas.create_rectangle(
                x, y, x + w, y + h,
                fill=TVColors.BG_CARD_HOVER, outline=TVColors.BORDER_NORMAL, width=1
            )
        else:
            canvas.create_rectangle(
                x, y, x + w, y + h,
                fill=TVColors.BG_CARD, outline=TVColors.BORDER_SUBTLE, width=1
            )

        # Monogram background circle (simulates channel logo)
        mono_color = _get_monogram_color(name)
        cx, cy = x + w // 2, y + h // 2 - 10
        mono_r = 24 if is_focused else 20
        canvas.create_oval(
            cx - mono_r, cy - mono_r, cx + mono_r, cy + mono_r,
            fill=mono_color, outline=""
        )
        # Monogram letter
        letter = name[0].upper() if name else "?"
        canvas.create_text(
            cx, cy,
            text=letter,
            fill=TVColors.TEXT_PRIMARY,
            font=(FONT_FAMILY, 16 if is_focused else 13, "bold")
        )

        # Channel name (below monogram)
        display_name = name if len(name) <= 24 else name[:22] + "…"
        name_y = cy + mono_r + 14
        canvas.create_text(
            x + w // 2, name_y,
            text=display_name,
            fill=TVColors.TEXT_PRIMARY if is_focused else TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 12 if is_focused else 10,
                  "bold" if is_focused else "normal"),
            anchor="center", width=w - 20
        )

        # Channel number badge (top-left)
        ch_num = self._channel_numbers.get(id(channel))
        if ch_num is not None:
            canvas.create_text(
                x + 10, y + 10,
                text=str(ch_num),
                fill=TVColors.ACCENT if is_focused else TVColors.TEXT_DIM,
                font=(FONT_FAMILY, 9, "bold" if is_focused else "normal"),
                anchor="nw"
            )

        # Live indicator (top-right, pulsing dot)
        if channel.get('is_working'):
            dot_color = TVColors.LIVE_PULSE if is_focused else TVColors.SUCCESS
            canvas.create_oval(
                x + w - 16, y + 8, x + w - 6, y + 18,
                fill=dot_color, outline=""
            )

        # Favorite star (bottom-right)
        if ch_url in self._favorite_urls:
            canvas.create_text(
                x + w - 14, y + h - 14,
                text="★",
                fill=TVColors.FAVORITE_STAR,
                font=(FONT_FAMILY, 13),
                anchor="center"
            )

        # Category subtitle (bottom-left, only on focused)
        if is_focused:
            cat = channel.get('category', '')
            country = channel.get('country', '')
            sub = cat + (f" • {country}" if country else "")
            if sub:
                canvas.create_text(
                    x + 10, y + h - 12,
                    text=sub[:30],
                    fill=TVColors.TEXT_DIM,
                    font=(FONT_FAMILY, 9),
                    anchor="sw"
                )

    def _update_info_bar(self):
        """Update the info bar with focused channel details."""
        if not self._rows or not self._info_label:
            return
        row = self._rows[self._row_index]
        channels = row["channels"]
        if 0 <= self._col_index < len(channels):
            ch = channels[self._col_index]
            name = ch.get('name', 'Unknown')
            cat = ch.get('category', '')
            country = ch.get('country', '')
            num = self._channel_numbers.get(id(ch))
            parts = []
            if num:
                parts.append(f"Ch.{num}")
            parts.append(name)
            if cat:
                parts.append(cat)
            if country:
                parts.append(country)
            self._info_label.config(text="  │  ".join(parts))

    # ─── Clock ──────────────────────────────────────────────────────────────

    def _start_clock(self):
        """Start the clock update loop."""
        self._update_clock()

    def _update_clock(self):
        """Update clock display."""
        if self._clock_label:
            now = datetime.now()
            self._clock_label.config(text=now.strftime("%H:%M"))
        self._clock_timer = self.after(CLOCK_UPDATE_MS, self._update_clock)

    # ─── Navigation ─────────────────────────────────────────────────────────

    def _bind_keys(self):
        """Bind keyboard and mouse navigation."""
        self.bind("<Up>", self._nav_up)
        self.bind("<Down>", self._nav_down)
        self.bind("<Left>", self._nav_left)
        self.bind("<Right>", self._nav_right)
        self.bind("<Return>", self._play_selected)
        self.bind("<KP_Enter>", self._play_selected)
        self.bind("<Escape>", self._on_escape)
        self.bind("<BackSpace>", self._on_escape)
        self.bind("<F11>", lambda e: self._exit_tv_mode())
        self.bind("<Prior>", self._page_up)    # Page Up
        self.bind("<Next>", self._page_down)   # Page Down
        self.bind("<Home>", self._jump_home)
        self.bind("<End>", self._jump_end)

        # Number keys
        for i in range(10):
            self.bind(str(i), self._on_number_key)
            self.bind(f"<KP_{i}>", self._on_number_key)

        # Volume
        self.bind("<plus>", lambda e: self._volume_change(5))
        self.bind("<KP_Add>", lambda e: self._volume_change(5))
        self.bind("<minus>", lambda e: self._volume_change(-5))
        self.bind("<KP_Subtract>", lambda e: self._volume_change(-5))

    def _nav_up(self, event=None):
        """Move to previous row."""
        if self._row_index > 0:
            self._row_index -= 1
            self._clamp_col()
            self._ensure_col_visible()
            self._draw()

    def _nav_down(self, event=None):
        """Move to next row."""
        if self._row_index < len(self._rows) - 1:
            self._row_index += 1
            self._clamp_col()
            self._ensure_col_visible()
            self._draw()

    def _nav_left(self, event=None):
        """Move left in current row."""
        if self._col_index > 0:
            self._col_index -= 1
            self._ensure_col_visible()
            self._draw()

    def _nav_right(self, event=None):
        """Move right in current row."""
        row_len = len(self._rows[self._row_index]["channels"])
        if self._col_index < row_len - 1:
            self._col_index += 1
            self._ensure_col_visible()
            self._draw()

    def _page_up(self, event=None):
        """Jump up by 3 rows."""
        self._row_index = max(0, self._row_index - 3)
        self._clamp_col()
        self._ensure_col_visible()
        self._draw()

    def _page_down(self, event=None):
        """Jump down by 3 rows."""
        self._row_index = min(len(self._rows) - 1, self._row_index + 3)
        self._clamp_col()
        self._ensure_col_visible()
        self._draw()

    def _jump_home(self, event=None):
        """Jump to first card in row."""
        self._col_index = 0
        self._col_offsets[self._row_index] = 0
        self._draw()

    def _jump_end(self, event=None):
        """Jump to last card in row."""
        row_len = len(self._rows[self._row_index]["channels"])
        self._col_index = max(0, row_len - 1)
        self._ensure_col_visible()
        self._draw()

    def _clamp_col(self):
        """Clamp column index to current row length."""
        if self._rows:
            row_len = len(self._rows[self._row_index]["channels"])
            if self._col_index >= row_len:
                self._col_index = max(0, row_len - 1)

    def _ensure_col_visible(self):
        """Adjust scroll offset so focused card is visible."""
        if not self._canvas:
            return
        cw = self._canvas.winfo_width()
        if cw < 100:
            cw = self.winfo_screenwidth()
        visible_cards = max(1, (cw - 64) // (CARD_WIDTH + CARD_GAP))
        row_idx = self._row_index

        if self._col_index < self._col_offsets[row_idx]:
            self._col_offsets[row_idx] = self._col_index
        elif self._col_index >= self._col_offsets[row_idx] + visible_cards:
            self._col_offsets[row_idx] = self._col_index - visible_cards + 1

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
        if self._clock_timer:
            self.after_cancel(self._clock_timer)
        if self._number_timer:
            self.after_cancel(self._number_timer)
        if self._toast_timer:
            self.after_cancel(self._toast_timer)
        self.attributes("-fullscreen", False)
        self.attributes("-topmost", False)
        if self._on_exit:
            self._on_exit()
        self.destroy()

    # ─── Mouse Support ──────────────────────────────────────────────────────

    def _on_canvas_click(self, event):
        """Handle mouse click on canvas — find clicked card and focus/play."""
        if not self._rows:
            return
        # Determine which row/col was clicked based on geometry
        cw = self._canvas.winfo_width()
        ch_h = self._canvas.winfo_height()
        y_offset = 28

        start_row = max(0, self._row_index - 1)
        end_row = min(len(self._rows), start_row + VISIBLE_ROWS)
        if end_row - start_row < VISIBLE_ROWS and start_row > 0:
            start_row = max(0, end_row - VISIBLE_ROWS)

        for row_idx in range(start_row, end_row):
            row = self._rows[row_idx]
            is_active = (row_idx == self._row_index)
            y_top = y_offset + ROW_LABEL_HEIGHT
            card_h = CARD_HEIGHT_FOCUS if is_active else CARD_HEIGHT

            if y_top <= event.y <= y_top + card_h:
                # Click is in this row — find column
                scroll_offset = self._col_offsets[row_idx]
                x_start = 32 - scroll_offset * (CARD_WIDTH + CARD_GAP)
                for col_idx in range(len(row["channels"])):
                    x = x_start + col_idx * (CARD_WIDTH + CARD_GAP)
                    if x <= event.x <= x + CARD_WIDTH:
                        if self._row_index == row_idx and self._col_index == col_idx:
                            # Double-click effect: play
                            self._play_selected()
                        else:
                            self._row_index = row_idx
                            self._col_index = col_idx
                            self._draw()
                        return

            y_offset += ROW_LABEL_HEIGHT + CARD_HEIGHT_FOCUS + 20

    def _on_resize(self, event=None):
        """Handle window/canvas resize."""
        self.after(50, self._draw)

    # ─── Channel Number Jump ────────────────────────────────────────────────

    def _on_number_key(self, event):
        """Handle number key press for channel jump."""
        digit = event.char if event.char and event.char.isdigit() else ''
        if not digit:
            # Try keysym for numpad
            ks = event.keysym
            if ks.startswith("KP_") and ks[-1].isdigit():
                digit = ks[-1]
        if not digit:
            return

        # Cap digits
        if len(self._number_buffer) >= MAX_NUMBER_DIGITS:
            return

        self._number_buffer += digit
        self._show_number_overlay()

        # Reset timer
        if self._number_timer:
            self.after_cancel(self._number_timer)
        self._number_timer = self.after(NUMBER_TIMEOUT_MS, self._execute_number_jump)

    def _show_number_overlay(self):
        """Show the channel number being entered."""
        self._number_label.config(text=f"Ch. {self._number_buffer}_")
        self._number_label.place(relx=0.5, rely=0.12, anchor="center")

    def _execute_number_jump(self):
        """Jump to the entered channel number."""
        self._number_timer = None
        target_text = self._number_buffer
        self._number_buffer = ""
        self._number_label.place_forget()

        try:
            target = int(target_text)
        except ValueError:
            return

        if target < 1 or target > self._max_channel_number:
            self._show_toast(f"Channel {target} not found")
            return

        # Find channel by number (reverse lookup)
        for row_idx, row in enumerate(self._rows):
            for col_idx, ch in enumerate(row["channels"]):
                if self._channel_numbers.get(id(ch)) == target:
                    self._row_index = row_idx
                    self._col_index = col_idx
                    self._ensure_col_visible()
                    self._draw()
                    return

        self._show_toast(f"Channel {target} not found")

    # ─── Toast ──────────────────────────────────────────────────────────────

    def _show_toast(self, message: str, duration_ms: int = 2000):
        """Show a brief toast notification."""
        self._toast_label.config(text=message)
        self._toast_label.place(relx=0.5, rely=0.88, anchor="center")
        if self._toast_timer:
            self.after_cancel(self._toast_timer)
        self._toast_timer = self.after(duration_ms, self._hide_toast)

    def _hide_toast(self):
        """Hide toast."""
        self._toast_label.place_forget()
        self._toast_timer = None

    # ─── Volume ─────────────────────────────────────────────────────────────

    def _volume_change(self, delta: int):
        """Adjust volume (stub — integrates with player if active)."""
        pass

    # ─── Public Methods ─────────────────────────────────────────────────────

    def refresh_channels(self, channels: List[Dict[str, Any]]):
        """Refresh channel data (e.g., after scan completes)."""
        # Preserve focused channel
        focused_ch = None
        if self._rows and self._row_index < len(self._rows):
            row = self._rows[self._row_index]
            if self._col_index < len(row["channels"]):
                focused_ch = row["channels"][self._col_index]

        self._all_channels = channels
        self._build_rows()

        # Restore focus by channel identity
        if focused_ch:
            focused_url = focused_ch.get('url', '')
            for row_idx, row in enumerate(self._rows):
                for col_idx, ch in enumerate(row["channels"]):
                    if ch.get('url') == focused_url:
                        self._row_index = row_idx
                        self._col_index = col_idx
                        self._ensure_col_visible()
                        self._draw()
                        return

        # Fallback: reset
        self._row_index = min(self._row_index, max(0, len(self._rows) - 1))
        self._clamp_col()
        self._draw()
