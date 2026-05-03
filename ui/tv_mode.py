"""TV Mode — Standalone Google TV / Android Streamer lean-back interface.

Primary application UI: a full-window channel browser navigated with
arrow keys, Enter, and Escape — designed for use with a remote control
or keyboard.  Channels are displayed in horizontal rows grouped by
category, with Favorites and Recent at the top.

Keyboard Controls (browse):
    Arrow keys  — Navigate between channels
    Enter       — Play selected channel
    Escape      — Stop player / quit app
    0-9         — Channel number quick-jump
    Page Up/Dn  — Jump rows quickly
    Home/End    — Jump to first/last in row
    F           — Toggle favorite on focused card
    F11         — Toggle fullscreen
    Ctrl+F or / — Open search
    S           — Open settings

Keyboard Controls (player):
    Escape      — Stop and return to browse
    Ch Up/Down  — Next/previous channel
    M           — Mute/unmute
    +/-         — Volume up/down
    Space       — Pause/resume
"""

__all__ = ['TVModeApp']

import sys
import tkinter as tk
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Set

from utils.logger import get_logger
from utils.favorites import FavoritesManager
from utils.history import WatchHistory
from ui.logo_manager import get_logo_manager, PIL_AVAILABLE
import config

logger = get_logger(__name__)

# Try to import optional modules
try:
    from icon import set_window_icon
except ImportError:
    set_window_icon = None

try:
    from utils.parental import ParentalControls
except ImportError:
    ParentalControls = None

try:
    from ui.vlc_controller import VLCController, VLC_AVAILABLE
except ImportError:
    VLCController = None
    VLC_AVAILABLE = False


# ─── TV Mode Color Palette ──────────────────────────────────────────────────────────
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
    OVERLAY_BG = "#0A0A0F"
    SUCCESS = "#4ADE80"
    LIVE_PULSE = "#EF4444"
    FAVORITE_STAR = "#FBBF24"
    MONOGRAM_BG_1 = "#1E3A5F"
    MONOGRAM_BG_2 = "#2D1B4E"
    MONOGRAM_BG_3 = "#1B4332"
    MONOGRAM_BG_4 = "#4A1D1D"
    TOAST_BG = "#1A1A2E"
    TOAST_BORDER = "#333348"
    NAV_BG = "#0D0D14"
    NAV_ACTIVE = "#1A2535"
    SCAN_BAR_BG = "#1A3A5F"
    SEARCH_BG = "#16161E"
    SEARCH_BORDER = "#2A2A3A"
    PLAYER_OSD_BG = "#0D0D14"


# ─── TV Mode Constants ────────────────────────────────────────────────────────────
CARD_WIDTH = 260
CARD_HEIGHT = 160
CARD_WIDTH_FOCUS = 288
CARD_HEIGHT_FOCUS = 180
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
SCAN_POLL_MS = 3000
OSD_FADE_MS = 3000

# Category emoji mapping
CATEGORY_ICONS = {
    "News": "\U0001f4f0", "Sports": "\u26bd", "Entertainment": "\U0001f3ac", "Music": "\U0001f3b5",
    "Kids": "\U0001f9f8", "Movies": "\U0001f3a5", "Documentary": "\U0001f30d", "Science": "\U0001f52c",
    "Education": "\U0001f4da", "Religious": "\U0001f54c", "Business": "\U0001f4bc", "Lifestyle": "\U0001f3e1",
    "Food": "\U0001f373", "Travel": "\u2708\ufe0f", "Weather": "\U0001f324\ufe0f", "Comedy": "\U0001f602",
    "Drama": "\U0001f3ad", "Culture": "\U0001f3a8", "Technology": "\U0001f4bb", "Health": "\u2764\ufe0f",
    "Shopping": "\U0001f6d2", "Gaming": "\U0001f3ae", "Animation": "\U0001f39e\ufe0f", "Classic": "\U0001f4fa",
}


def _get_monogram_color(name: str) -> str:
    """Deterministic background color for channel monogram based on name."""
    colors = [TVColors.MONOGRAM_BG_1, TVColors.MONOGRAM_BG_2,
              TVColors.MONOGRAM_BG_3, TVColors.MONOGRAM_BG_4]
    return colors[hash(name) % len(colors)]


class TVModeApp:
    """Standalone TV-mode application with embedded VLC player.

    Creates its own root window via ``ui.compat.create_window`` and manages
    channel scanning, browsing, search, favorites, playback, and settings.
    """

    def __init__(self, channel_manager=None,
                 favorites_manager: Optional[FavoritesManager] = None,
                 watch_history: Optional[WatchHistory] = None):
        # External dependencies (create if not provided)
        if channel_manager is None:
            from core.channel_manager import ChannelManager
            channel_manager = ChannelManager()
        self._channel_manager = channel_manager

        self._favorites_manager = favorites_manager or FavoritesManager()
        self._watch_history = watch_history or WatchHistory()

        # Parental controls
        self._parental = None
        if ParentalControls is not None:
            try:
                self._parental = ParentalControls()
            except Exception:
                pass

        # Root window — force plain tk.Tk for reliable rendering
        # CTk has frozen-build (PyInstaller) issues where the window may not appear.
        self.root = tk.Tk()
        self.root.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.root.geometry(
            f"{getattr(config, 'WINDOW_WIDTH', 1280)}x{getattr(config, 'WINDOW_HEIGHT', 720)}"
        )
        self.root.configure(bg=TVColors.BG)
        # DPI awareness on Windows
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        # Force visibility
        self.root.deiconify()
        self.root.lift()
        self.root.update_idletasks()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        if set_window_icon:
            try:
                set_window_icon(self.root)
            except Exception:
                pass

        # Application state
        self._state = "browse"  # "browse" | "playing"
        self._is_fullscreen = False
        self._all_channels: List[Dict[str, Any]] = []

        # Navigation state
        self._rows: List[Dict[str, Any]] = []
        self._row_index = 0
        self._col_index = 0
        self._col_offsets: List[int] = []
        self._row_pixel_offsets: List[float] = []
        self._row_pixel_targets: List[float] = []
        self._row_pixel_velocity: List[float] = []  # #175 spring physics
        self._vertical_offset: float = 0.0
        self._vertical_target: float = 0.0
        self._vertical_velocity: float = 0.0  # #175 spring physics
        self._filtered_channels: Optional[List[Dict[str, Any]]] = None
        self._active_filters: Dict[str, set] = {  # #160 filter state
            'language': set(), 'country': set(), 'category': set()
        }

        # Logo manager + PhotoImage refs (must keep alive for tk)
        self._logo_mgr = get_logo_manager() if PIL_AVAILABLE else None
        self._logo_refs: Dict[str, Any] = {}
        self._logo_redraw_pending = False

        # Cached data
        self._favorite_urls: Set[str] = set()
        self._channel_numbers: Dict[int, int] = {}
        self._max_channel_number = 0

        # Number entry
        self._number_buffer = ""
        self._number_timer = None

        # Animation
        self._anim_id = None
        self._scroll_target_offsets: List[int] = []

        # Timers
        self._clock_timer = None
        self._toast_timer = None
        self._scan_timer = None
        self._osd_timer = None

        # Current nav tab
        self._current_tab = "home"

        # Mouse hover tracking — last (row_idx, col_idx) under cursor
        self._hover_pos: Optional[tuple] = None

        # Search state
        self._search_active = False
        self._search_var = tk.StringVar(self.root)
        self._search_var.trace_add("write", self._on_search_changed)

        # VLC player
        self._vlc = None
        self._player_frame: Optional[tk.Frame] = None
        self._player_channel: Optional[Dict[str, Any]] = None
        self._player_volume = 80

        # UI elements
        self._canvas: Optional[tk.Canvas] = None
        self._info_label: Optional[tk.Label] = None
        self._clock_label: Optional[tk.Label] = None
        self._number_label: Optional[tk.Label] = None
        self._scan_bar: Optional[tk.Frame] = None
        self._scan_label: Optional[tk.Label] = None
        self._search_frame: Optional[tk.Frame] = None
        self._search_entry: Optional[tk.Entry] = None
        self._nav_tabs: Dict[str, tk.Label] = {}

        # Build UI
        self._create_nav_bar()
        self._create_ui()
        self._bind_keys()

        # Initialise channels
        self.root.after(50, self._initialize)

    # ---- Initialisation & Scanning ------------------------------------------

    def _initialize(self):
        """Load cached channels and start background scan."""
        # Issue #170 — first-launch privacy / consent dialog
        try:
            from ui.privacy_dialog import maybe_show_privacy_dialog
            maybe_show_privacy_dialog(self.root)
        except Exception as e:
            logger.warning(f"Privacy dialog skipped: {e}")

        # Issue #160 — restore persisted filter selections
        try:
            from ui.filter_dialog import load_filters
            self._active_filters = load_filters()
        except Exception:
            self._active_filters = {'language': set(), 'country': set(), 'category': set()}

        loaded = self._channel_manager.load_cached_channels()
        if loaded:
            self._all_channels = list(self._channel_manager.channels)
            logger.info(f"Loaded {len(self._all_channels)} cached channels")
        else:
            self._all_channels = []
            logger.info("No cached channels found, starting fresh scan")

        self._build_rows()
        self._draw()
        self.root.after(100, self._start_clock)

        # Start smooth-scroll animation loop (~60fps)
        self._anim_id = self.root.after(16, self._animate_scroll)

        # Start background fetch
        self._channel_manager.fetch_channels_async(callback=self._on_fetch_complete)
        self._scan_timer = self.root.after(SCAN_POLL_MS, self._poll_scan_progress)

        # Issue #162 — first-run tooltip tour (after window settles)
        try:
            from ui.tour_overlay import maybe_show_tour
            maybe_show_tour(self.root)
        except Exception as e:
            logger.warning(f"Tour skipped: {e}")

    def _on_fetch_complete(self):
        """Called from background thread when fetch finishes."""
        try:
            self.root.after(0, self._refresh_from_manager)
        except Exception:
            pass

    def _refresh_from_manager(self):
        """Refresh channel list from manager (main thread)."""
        self._all_channels = list(self._channel_manager.channels)
        self._build_rows()
        self._draw()
        self._update_scan_bar(done=True)
        self._show_toast(f"{len(self._all_channels)} channels loaded")
        logger.info(f"Channels refreshed: {len(self._all_channels)} total")

    def _poll_scan_progress(self):
        """Periodically check scan status and refresh rows."""
        try:
            current = list(self._channel_manager.channels)
            if len(current) != len(self._all_channels):
                self._all_channels = current
                self._build_rows()
                self._draw()
            self._update_scan_bar()
        except Exception:
            pass
        self._scan_timer = self.root.after(SCAN_POLL_MS, self._poll_scan_progress)

    def _update_scan_bar(self, done=False):
        """Update the scan progress indicator (with simple animation — Issue #164)."""
        if not self._scan_bar:
            return
        working = len([c for c in self._all_channels if c.get('is_working')])
        total = len(self._all_channels)
        if done or total == 0:
            self._scan_label.config(text=f"\u2713 {working} working channels")
            self.root.after(5000, lambda: self._scan_bar.pack_forget() if self._scan_bar else None)
        else:
            # Animated dots cycle while scanning
            phase = (getattr(self, '_scan_phase', 0) + 1) % 4
            self._scan_phase = phase
            dots = "." * phase + " " * (3 - phase)
            self._scan_label.config(text=f"\u26ec Scanning{dots}  {working}/{total} working")
            self._scan_bar.pack(fill=tk.X, side=tk.TOP, before=self._canvas)

    # ---- Data Preparation ---------------------------------------------------

    def _build_rows(self):
        """Organize channels into category rows with Favorites and Recent at top."""
        self._rows = []

        # Determine source channels based on tab/search
        if self._filtered_channels is not None:
            source = self._filtered_channels
        else:
            source = self._all_channels

        # Filter parental-blocked channels
        if self._parental:
            source = [ch for ch in source if not self._parental.is_channel_blocked(ch)]

        # Issue #160: apply user-selected language/country/category filters
        if any(self._active_filters.values()):
            try:
                from ui.filter_dialog import channel_passes
                source = [ch for ch in source if channel_passes(ch, self._active_filters)]
            except Exception:
                pass

        # Cache favorite URLs
        self._favorite_urls = set()
        if self._favorites_manager:
            favs = self._favorites_manager.get_favorites()
            if favs:
                self._favorite_urls = set(favs) if isinstance(favs, (set, list)) else set()

        if self._current_tab == "favorites":
            if self._favorite_urls:
                fav_channels = [ch for ch in source
                               if ch.get('url') in self._favorite_urls and ch.get('is_working')]
                if fav_channels:
                    self._rows.append({"label": "\u2605 Favorites", "channels": fav_channels, "icon": "\u2b50"})
        elif self._current_tab == "recent":
            if self._watch_history:
                recent_entries = self._watch_history.get_recent(limit=50)
                if recent_entries:
                    recent_channels = []
                    seen_urls = set()
                    for entry in recent_entries:
                        entry_url = entry.get('url', '') if isinstance(entry, dict) else str(entry)
                        if entry_url in seen_urls:
                            continue
                        for ch in source:
                            if ch.get('url') == entry_url and ch.get('is_working'):
                                recent_channels.append(ch)
                                seen_urls.add(entry_url)
                                break
                    if recent_channels:
                        self._rows.append({"label": "\U0001f550 Recently Watched", "channels": recent_channels, "icon": "\U0001f550"})
        else:
            # Home tab
            # Issue #169: "Local" row pinned at top — uses system locale country.
            try:
                local_country = self._get_local_country()
                if local_country:
                    local_channels = [
                        ch for ch in source
                        if ch.get('is_working')
                        and ch.get('country', '').strip().lower() == local_country.lower()
                    ]
                    if local_channels:
                        self._rows.append({
                            "label": f"\U0001f3e0 Local ({local_country})",
                            "channels": local_channels,
                            "icon": "\U0001f3e0",
                        })
            except Exception:
                pass

            if self._favorite_urls:
                fav_channels = [ch for ch in source
                               if ch.get('url') in self._favorite_urls and ch.get('is_working')]
                if fav_channels:
                    self._rows.append({"label": "\u2605 Favorites", "channels": fav_channels, "icon": "\u2b50"})

            if self._watch_history:
                recent_entries = self._watch_history.get_recent(limit=20)
                if recent_entries:
                    recent_channels = []
                    seen_urls = set()
                    for entry in recent_entries:
                        entry_url = entry.get('url', '') if isinstance(entry, dict) else str(entry)
                        if entry_url in seen_urls:
                            continue
                        for ch in source:
                            if ch.get('url') == entry_url and ch.get('is_working'):
                                recent_channels.append(ch)
                                seen_urls.add(entry_url)
                                break
                    if recent_channels:
                        self._rows.append({"label": "\U0001f550 Continue Watching", "channels": recent_channels, "icon": "\U0001f550"})

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
                            for ch in source:
                                if ch.get('url') == url and ch.get('is_working'):
                                    mp_channels.append(ch)
                                    seen.add(url)
                                    break
                        if len(mp_channels) >= 3:
                            self._rows.append({"label": "\U0001f525 Most Played", "channels": mp_channels, "icon": "\U0001f525"})
                except Exception:
                    pass

            # Category rows
            categories: Dict[str, List[Dict[str, Any]]] = {}
            for ch in source:
                if not ch.get('is_working'):
                    continue
                cat = ch.get('category', 'Other') or 'Other'
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(ch)

            for cat in sorted(categories, key=lambda c: (-len(categories[c]), c)):
                if categories[cat]:
                    icon = CATEGORY_ICONS.get(cat, "\U0001f4fa")
                    self._rows.append({"label": f"{icon} {cat}", "channels": categories[cat], "icon": icon})

        # Initialize scroll offsets
        self._col_offsets = [0] * len(self._rows)
        self._scroll_target_offsets = [0] * len(self._rows)
        self._row_pixel_offsets = [0.0] * len(self._rows)
        self._row_pixel_targets = [0.0] * len(self._rows)

        # Build canonical channel number map
        self._channel_numbers = {}
        num = 0
        seen_ids: Set[int] = set()
        for row in self._rows:
            for ch in row["channels"]:
                ch_id = id(ch)
                if ch_id not in seen_ids:
                    num += 1
                    self._channel_numbers[ch_id] = num
                    seen_ids.add(ch_id)
        self._max_channel_number = num

    # ---- Top Navigation Bar -------------------------------------------------

    def _create_nav_bar(self):
        """Create top navigation bar with tabs."""
        self._nav_frame = tk.Frame(self.root, bg=TVColors.NAV_BG, height=44)
        self._nav_frame.pack(fill=tk.X, side=tk.TOP)
        self._nav_frame.pack_propagate(False)

        tk.Label(
            self._nav_frame, text=f"\U0001f4fa {config.APP_NAME}",
            bg=TVColors.NAV_BG, fg=TVColors.ACCENT,
            font=(FONT_FAMILY, 13, "bold")
        ).pack(side=tk.LEFT, padx=16, pady=8)

        tabs = [("home", "\U0001f3e0 Home"), ("favorites", "\u2b50 Favorites"), ("recent", "\U0001f550 Recent")]
        for tab_id, label_text in tabs:
            lbl = tk.Label(
                self._nav_frame, text=label_text,
                bg=TVColors.NAV_ACTIVE if tab_id == self._current_tab else TVColors.NAV_BG,
                fg=TVColors.ACCENT if tab_id == self._current_tab else TVColors.TEXT_SECONDARY,
                font=(FONT_FAMILY, 11, "bold" if tab_id == self._current_tab else "normal"),
                padx=14, pady=8, cursor="hand2",
            )
            lbl.pack(side=tk.LEFT, padx=2)
            lbl.bind("<Button-1>", lambda e, t=tab_id: self._switch_tab(t))
            self._nav_tabs[tab_id] = lbl

        search_btn = tk.Label(
            self._nav_frame, text="\U0001f50d",
            bg=TVColors.NAV_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 14), padx=12, pady=8, cursor="hand2",
        )
        search_btn.pack(side=tk.RIGHT, padx=8)
        search_btn.bind("<Button-1>", lambda e: self._toggle_search())

        settings_btn = tk.Label(
            self._nav_frame, text="\u2699",
            bg=TVColors.NAV_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 14), padx=12, pady=8, cursor="hand2",
        )
        settings_btn.pack(side=tk.RIGHT, padx=4)
        settings_btn.bind("<Button-1>", lambda e: self._open_settings())

        # Issue #161: Submit / Contribute Channel button
        submit_btn = tk.Label(
            self._nav_frame, text="\U0001f4e1 Submit",
            bg=TVColors.NAV_BG, fg=TVColors.ACCENT,
            font=(FONT_FAMILY, 11, "bold"), padx=12, pady=8, cursor="hand2",
        )
        submit_btn.pack(side=tk.RIGHT, padx=4)
        submit_btn.bind("<Button-1>", lambda e: self._open_submit_dialog())

        # Issue #167: Map view button
        map_btn = tk.Label(
            self._nav_frame, text="\U0001f5fa",
            bg=TVColors.NAV_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 14), padx=12, pady=8, cursor="hand2",
        )
        map_btn.pack(side=tk.RIGHT, padx=4)
        map_btn.bind("<Button-1>", lambda e: self._open_map())

        # Issue #160: Filter button
        filter_btn = tk.Label(
            self._nav_frame, text="\U0001f50e Filter",
            bg=TVColors.NAV_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 11, "bold"), padx=12, pady=8, cursor="hand2",
        )
        filter_btn.pack(side=tk.RIGHT, padx=4)
        filter_btn.bind("<Button-1>", lambda e: self._open_filter())
        self._filter_btn = filter_btn

        # Issue #162: Help / tour button
        help_btn = tk.Label(
            self._nav_frame, text="?",
            bg=TVColors.NAV_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 14, "bold"), padx=12, pady=8, cursor="hand2",
        )
        help_btn.pack(side=tk.RIGHT, padx=4)
        help_btn.bind("<Button-1>", lambda e: self._open_tour())

    def _switch_tab(self, tab_id: str):
        """Switch between Home / Favorites / Recent views."""
        self._current_tab = tab_id
        for tid, lbl in self._nav_tabs.items():
            if tid == tab_id:
                lbl.configure(bg=TVColors.NAV_ACTIVE, fg=TVColors.ACCENT,
                              font=(FONT_FAMILY, 11, "bold"))
            else:
                lbl.configure(bg=TVColors.NAV_BG, fg=TVColors.TEXT_SECONDARY,
                              font=(FONT_FAMILY, 11, "normal"))
        self._row_index = 0
        self._col_index = 0
        self._build_rows()
        self._draw()

    # ---- UI Creation --------------------------------------------------------

    def _create_ui(self):
        """Create the TV mode interface."""
        # Info bar at bottom
        self._info_frame = tk.Frame(self.root, bg=TVColors.INFO_BAR_BG, height=50)
        self._info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self._info_frame.pack_propagate(False)

        tk.Frame(self._info_frame, bg=TVColors.INFO_BAR_BORDER, height=1).pack(
            fill=tk.X, side=tk.TOP)

        self._info_label = tk.Label(
            self._info_frame, text="",
            bg=TVColors.INFO_BAR_BG, fg=TVColors.TEXT_PRIMARY,
            font=(FONT_FAMILY, 13)
        )
        self._info_label.pack(side=tk.LEFT, padx=20, pady=10)

        self._clock_label = tk.Label(
            self._info_frame, text="",
            bg=TVColors.INFO_BAR_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 12)
        )
        self._clock_label.pack(side=tk.RIGHT, padx=20, pady=10)

        tk.Label(
            self._info_frame,
            text="\u2191\u2193\u2190\u2192 Navigate \u2502 Enter Play \u2502 F Fav \u2502 / Search \u2502 F11 Fullscreen \u2502 Esc Quit",
            bg=TVColors.INFO_BAR_BG, fg=TVColors.TEXT_MUTED,
            font=(FONT_FAMILY, 9)
        ).pack(side=tk.RIGHT, padx=12, pady=10)

        # Scan progress bar (initially hidden)
        self._scan_bar = tk.Frame(self.root, bg=TVColors.SCAN_BAR_BG, height=24)
        self._scan_label = tk.Label(
            self._scan_bar, text="Scanning\u2026",
            bg=TVColors.SCAN_BAR_BG, fg=TVColors.ACCENT,
            font=(FONT_FAMILY, 9)
        )
        self._scan_label.pack(side=tk.LEFT, padx=12, pady=2)

        # Search bar (initially hidden)
        self._search_frame = tk.Frame(self.root, bg=TVColors.SEARCH_BG, height=40)
        self._search_frame.pack_propagate(False)
        tk.Label(
            self._search_frame, text="\U0001f50d",
            bg=TVColors.SEARCH_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 14)
        ).pack(side=tk.LEFT, padx=(12, 4), pady=6)
        self._search_entry = tk.Entry(
            self._search_frame, textvariable=self._search_var,
            bg=TVColors.BG_CARD, fg=TVColors.TEXT_PRIMARY,
            insertbackground=TVColors.ACCENT,
            font=(FONT_FAMILY, 13), relief=tk.FLAT,
            highlightbackground=TVColors.SEARCH_BORDER, highlightthickness=1,
        )
        self._search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=6)
        self._search_entry.bind("<Escape>", lambda e: self._close_search())
        self._search_entry.bind("<Return>", lambda e: self._search_select())

        # Main canvas
        self._canvas = tk.Canvas(
            self.root, bg=TVColors.BG, highlightthickness=0, borderwidth=0
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.bind("<Button-1>", self._on_canvas_click)
        self._canvas.bind("<Configure>", self._on_resize)
        self._canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self._canvas.bind("<Shift-MouseWheel>", self._on_shift_mouse_wheel)
        self._canvas.bind("<Button-4>", lambda e: self._mouse_wheel_step(-1, True))
        self._canvas.bind("<Button-5>", lambda e: self._mouse_wheel_step(1, True))
        self._canvas.bind("<Motion>", self._on_canvas_motion)

        # Number overlay (hidden)
        self._number_label = tk.Label(
            self.root, text="", bg=TVColors.OVERLAY_BG, fg=TVColors.ACCENT,
            font=(FONT_FAMILY, 56, "bold"), padx=24, pady=12
        )

        # Toast label (hidden)
        self._toast_label = tk.Label(
            self.root, text="", bg=TVColors.TOAST_BG, fg=TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 14), padx=16, pady=8,
            highlightbackground=TVColors.TOAST_BORDER, highlightthickness=1
        )

    # ---- Drawing ------------------------------------------------------------

    def _draw(self):
        """Render the channel grid on canvas."""
        if self._state != "browse":
            return
        canvas = self._canvas
        if not canvas:
            return
        canvas.delete("all")

        cw = canvas.winfo_width()
        ch_height = canvas.winfo_height()
        if cw < 100 or ch_height < 100:
            cw = self.root.winfo_width() or 1280
            ch_height = (self.root.winfo_height() or 720) - 94

        if not self._rows:
            msg = "No channels available"
            if self._search_active:
                msg = "No matching channels"
            canvas.create_text(
                cw // 2, ch_height // 2,
                text=msg,
                fill=TVColors.TEXT_SECONDARY,
                font=(FONT_FAMILY, 22),
                justify=tk.CENTER
            )
            return

        # Hero area
        focused_ch = self._get_focused_channel()
        hero_h = 72
        if focused_ch:
            canvas.create_rectangle(0, 0, cw, hero_h, fill=TVColors.BG_GRADIENT_TOP, outline="")
            name = focused_ch.get('name', '')
            cat = focused_ch.get('category', '')
            country = focused_ch.get('country', '')
            ch_num = self._channel_numbers.get(id(focused_ch), 0)
            hero_text = f"Ch.{ch_num}  {name}" if ch_num else name
            canvas.create_text(
                32, hero_h // 2 - 6, text=hero_text,
                fill=TVColors.TEXT_PRIMARY, font=(FONT_FAMILY, 18, "bold"), anchor="w"
            )
            sub_parts = [p for p in [cat, country] if p]
            if sub_parts:
                canvas.create_text(
                    32, hero_h // 2 + 18, text=" \u2022 ".join(sub_parts),
                    fill=TVColors.TEXT_DIM, font=(FONT_FAMILY, 11), anchor="w"
                )
            if focused_ch.get('url', '') in self._favorite_urls:
                canvas.create_text(
                    cw - 32, hero_h // 2, text="\u2605 Favorite",
                    fill=TVColors.FAVORITE_STAR, font=(FONT_FAMILY, 12), anchor="e"
                )

        y_offset = hero_h + 8 + int(self._vertical_offset)

        start_row = max(0, self._row_index - 1)
        end_row = min(len(self._rows), start_row + VISIBLE_ROWS)
        if end_row - start_row < VISIBLE_ROWS and start_row > 0:
            start_row = max(0, end_row - VISIBLE_ROWS)

        for row_idx in range(start_row, end_row):
            row = self._rows[row_idx]
            is_active = (row_idx == self._row_index)
            channels = row["channels"]

            if is_active:
                canvas.create_rectangle(
                    0, y_offset - 6, cw, y_offset + ROW_LABEL_HEIGHT + CARD_HEIGHT_FOCUS + 12,
                    fill=TVColors.BG_ROW_ACTIVE, outline=""
                )

            label_font_size = 20 if is_active else 15
            label_weight = "bold" if is_active else "normal"
            label_color = TVColors.TEXT_PRIMARY if is_active else TVColors.TEXT_SECONDARY
            canvas.create_text(
                32, y_offset + 6, text=row["label"],
                fill=label_color,
                font=(FONT_FAMILY, label_font_size, label_weight),
                anchor="nw"
            )

            count_text = f"  {len(channels)}"
            label_bbox = canvas.bbox(canvas.find_all()[-1])
            count_x = (label_bbox[2] + 12) if label_bbox else 200
            canvas.create_text(
                count_x, y_offset + 12, text=count_text,
                fill=TVColors.TEXT_DIM, font=(FONT_FAMILY, 13), anchor="nw"
            )

            y_offset += ROW_LABEL_HEIGHT

            # Pixel-based smooth horizontal scroll
            if row_idx < len(self._row_pixel_offsets):
                x_start = 32 - self._row_pixel_offsets[row_idx]
            else:
                x_start = 32

            for col_idx, channel in enumerate(channels):
                is_focused = (is_active and col_idx == self._col_index)
                card_w = CARD_WIDTH_FOCUS if is_focused else CARD_WIDTH
                card_h = CARD_HEIGHT_FOCUS if is_focused else CARD_HEIGHT
                x = x_start + col_idx * (CARD_WIDTH + CARD_GAP)

                y_card = y_offset
                if is_focused:
                    y_card -= (CARD_HEIGHT_FOCUS - CARD_HEIGHT) // 2

                if x + card_w < -50 or x > cw + 50:
                    continue

                self._draw_card(canvas, x, y_card, card_w, card_h,
                                channel, is_focused, is_active)

            y_offset += CARD_HEIGHT_FOCUS + 20

        self._update_info_bar()

    def _draw_card(self, canvas, x, y, w, h, channel, is_focused, is_active_row):
        """Draw a single channel card with depth and visual hierarchy."""
        name = channel.get('name', 'Unknown')
        ch_url = channel.get('url', '')

        if is_focused:
            canvas.create_rectangle(
                x - 4, y - 4, x + w + 4, y + h + 4,
                fill="", outline=TVColors.BORDER_FOCUS_GLOW, width=2,
                stipple="gray50"
            )
            canvas.create_rectangle(
                x, y, x + w, y + h,
                fill=TVColors.BG_CARD_FOCUS, outline=TVColors.BORDER_FOCUS, width=2
            )
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

        # Try logo (cached) — fall back to monogram
        logo_img = None
        if self._logo_mgr is not None:
            cached = self._logo_refs.get(ch_url)
            if cached is not None:
                logo_img = cached
            else:
                def _on_logo(img, key=ch_url):
                    if img is not None:
                        self._logo_refs[key] = img
                        if not self._logo_redraw_pending:
                            self._logo_redraw_pending = True
                            self.root.after_idle(self._do_logo_redraw)
                logo_img = self._logo_mgr.get_logo(channel, _on_logo)
                if logo_img is not None:
                    self._logo_refs[ch_url] = logo_img

        cx = x + w // 2
        cy = y + h // 2 - 14
        mono_r = 28 if is_focused else 24
        if logo_img is not None:
            # Soft circular backdrop so transparent PNGs read on the card
            canvas.create_oval(
                cx - mono_r - 2, cy - mono_r - 2,
                cx + mono_r + 2, cy + mono_r + 2,
                fill=TVColors.BG_CARD, outline=""
            )
            canvas.create_image(cx, cy, image=logo_img, anchor='center')
        else:
            mono_color = _get_monogram_color(name)
            canvas.create_oval(
                cx - mono_r, cy - mono_r, cx + mono_r, cy + mono_r,
                fill=mono_color, outline=""
            )
            # Issue #158: only draw the monogram letter when the channel has
            # NO logo URL — otherwise the letter "flashes" then is replaced
            # by the logo, looking like override text.
            has_logo_url = bool((channel.get('logo') or '').startswith(('http://', 'https://')))
            if not has_logo_url:
                letter = name[0].upper() if name else "?"
                canvas.create_text(
                    cx, cy, text=letter,
                    fill=TVColors.TEXT_PRIMARY,
                    font=(FONT_FAMILY, 18 if is_focused else 15, "bold")
                )

        display_name = name if len(name) <= 24 else name[:22] + "\u2026"
        name_y = y + h - 24 if is_focused else y + h - 22
        canvas.create_text(
            x + w // 2, name_y, text=display_name,
            fill=TVColors.TEXT_PRIMARY if is_focused else TVColors.TEXT_SECONDARY,
            font=(FONT_FAMILY, 17 if is_focused else 15,
                  "bold" if is_focused else "normal"),
            anchor="center", width=w - 20
        )

        ch_num = self._channel_numbers.get(id(channel))
        if ch_num is not None:
            canvas.create_text(
                x + 10, y + 10, text=str(ch_num),
                fill=TVColors.ACCENT if is_focused else TVColors.TEXT_DIM,
                font=(FONT_FAMILY, 11, "bold"),
                anchor="nw"
            )

        if channel.get('is_working'):
            dot_color = TVColors.LIVE_PULSE if is_focused else TVColors.SUCCESS
            canvas.create_oval(
                x + w - 16, y + 8, x + w - 6, y + 18,
                fill=dot_color, outline=""
            )

        if ch_url in self._favorite_urls:
            canvas.create_text(
                x + w - 14, y + 10, text="\u2605",
                fill=TVColors.FAVORITE_STAR, font=(FONT_FAMILY, 13), anchor="ne"
            )

        if is_focused:
            cat = channel.get('category', '')
            country = channel.get('country', '')
            sub = cat + (f" \u2022 {country}" if country else "")
            if sub:
                canvas.create_text(
                    x + 10, y + h - 8, text=sub[:30],
                    fill=TVColors.TEXT_DIM, font=(FONT_FAMILY, 10), anchor="sw"
                )

    def _do_logo_redraw(self):
        """Coalesced redraw triggered by async logo loads."""
        self._logo_redraw_pending = False
        if self._state == "browse":
            self._draw()

    def _get_focused_channel(self):
        """Return the currently focused channel dict, or None."""
        if not self._rows or self._row_index >= len(self._rows):
            return None
        row = self._rows[self._row_index]
        if 0 <= self._col_index < len(row["channels"]):
            return row["channels"][self._col_index]
        return None

    def _update_info_bar(self):
        """Update the info bar with focused channel details."""
        if not self._rows or not self._info_label:
            return
        ch = self._get_focused_channel()
        if ch:
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
            self._info_label.config(text="  \u2502  ".join(parts))

    # ---- Clock --------------------------------------------------------------

    def _start_clock(self):
        self._update_clock()

    def _update_clock(self):
        if self._clock_label:
            self._clock_label.config(text=datetime.now().strftime("%H:%M"))
        self._clock_timer = self.root.after(CLOCK_UPDATE_MS, self._update_clock)

    # ---- Navigation ---------------------------------------------------------

    def _bind_keys(self):
        """Bind keyboard navigation."""
        r = self.root
        r.bind("<Up>", self._nav_up)
        r.bind("<Down>", self._nav_down)
        r.bind("<Left>", self._nav_left)
        r.bind("<Right>", self._nav_right)
        r.bind("<Return>", self._play_selected)
        r.bind("<KP_Enter>", self._play_selected)
        r.bind("<Escape>", self._on_escape)
        r.bind("<BackSpace>", self._on_backspace)
        r.bind("<F11>", lambda e: self._toggle_fullscreen())
        r.bind("<Prior>", self._page_up)
        r.bind("<Next>", self._page_down)
        r.bind("<Home>", self._jump_home)
        r.bind("<End>", self._jump_end)

        for i in range(10):
            r.bind(str(i), self._on_number_key)
            r.bind(f"<KP_{i}>", self._on_number_key)

        r.bind("<plus>", lambda e: self._volume_change(5))
        r.bind("<KP_Add>", lambda e: self._volume_change(5))
        r.bind("<minus>", lambda e: self._volume_change(-5))
        r.bind("<KP_Subtract>", lambda e: self._volume_change(-5))

        r.bind("f", self._on_f_key)
        r.bind("F", self._on_f_key)
        r.bind("s", lambda e: self._open_settings())
        r.bind("S", lambda e: self._open_settings())
        r.bind("m", lambda e: self._toggle_mute())
        r.bind("M", lambda e: self._toggle_mute())
        r.bind("<space>", self._on_space)
        r.bind("/", lambda e: self._toggle_search())
        r.bind("<Control-f>", lambda e: self._toggle_search())
        # Issue #161: 'a' / 'A' opens Submit Channel
        r.bind("a", lambda e: self._open_submit_dialog())
        r.bind("A", lambda e: self._open_submit_dialog())

    def _row_pitch(self) -> int:
        """Approximate vertical pitch of a row (label + focused card + gap)."""
        return ROW_LABEL_HEIGHT + CARD_HEIGHT_FOCUS + 20

    def _change_row(self, new_row: int):
        """Move row focus with an animated vertical slide."""
        new_row = max(0, min(len(self._rows) - 1, new_row))
        if new_row == self._row_index:
            return
        delta_rows = self._row_index - new_row  # positive when going up
        self._row_index = new_row
        # Snap offset so the new row appears at the old position, then ease to 0
        self._vertical_offset = float(delta_rows * self._row_pitch())
        self._vertical_target = 0.0
        self._clamp_col()
        self._ensure_col_visible()
        self._draw()

    def _nav_up(self, event=None):
        if self._state == "playing":
            return
        if self._row_index > 0:
            self._change_row(self._row_index - 1)

    def _nav_down(self, event=None):
        if self._state == "playing":
            return
        if self._rows and self._row_index < len(self._rows) - 1:
            self._change_row(self._row_index + 1)

    def _nav_left(self, event=None):
        if self._state == "playing":
            self._channel_prev()
            return
        if self._col_index > 0:
            self._col_index -= 1
            self._ensure_col_visible()
            self._draw()

    def _nav_right(self, event=None):
        if self._state == "playing":
            self._channel_next()
            return
        if not self._rows:
            return
        row_len = len(self._rows[self._row_index]["channels"])
        if self._col_index < row_len - 1:
            self._col_index += 1
            self._ensure_col_visible()
            self._draw()

    def _page_up(self, event=None):
        if self._state == "playing":
            self._channel_prev()
            return
        self._change_row(max(0, self._row_index - 3))

    def _page_down(self, event=None):
        if self._state == "playing":
            self._channel_next()
            return
        if self._rows:
            self._change_row(min(len(self._rows) - 1, self._row_index + 3))

    def _jump_home(self, event=None):
        if self._state == "playing":
            return
        self._col_index = 0
        if self._rows:
            self._col_offsets[self._row_index] = 0
            if self._row_index < len(self._row_pixel_targets):
                self._row_pixel_targets[self._row_index] = 0.0
        self._draw()

    def _jump_end(self, event=None):
        if self._state == "playing":
            return
        if not self._rows:
            return
        row_len = len(self._rows[self._row_index]["channels"])
        self._col_index = max(0, row_len - 1)
        self._ensure_col_visible()
        self._draw()

    def _clamp_col(self):
        if self._rows:
            row_len = len(self._rows[self._row_index]["channels"])
            if self._col_index >= row_len:
                self._col_index = max(0, row_len - 1)

    def _ensure_col_visible(self):
        if not self._canvas or not self._rows:
            return
        cw = self._canvas.winfo_width()
        if cw < 100:
            cw = self.root.winfo_width() or 1280
        row_idx = self._row_index

        # Keep legacy integer offset roughly in sync (used by click hit-testing)
        visible_cards = max(1, (cw - 64) // (CARD_WIDTH + CARD_GAP))
        if self._col_index < self._col_offsets[row_idx]:
            self._col_offsets[row_idx] = self._col_index
        elif self._col_index >= self._col_offsets[row_idx] + visible_cards:
            self._col_offsets[row_idx] = self._col_index - visible_cards + 1

        # Pixel-based smooth scroll target
        card_pitch = CARD_WIDTH + CARD_GAP
        target_card_x = self._col_index * card_pitch
        visible_w = max(1, cw - 64)
        current = self._row_pixel_targets[row_idx] if row_idx < len(self._row_pixel_targets) else 0.0
        if target_card_x < current:
            self._row_pixel_targets[row_idx] = float(target_card_x)
        elif target_card_x + CARD_WIDTH > current + visible_w:
            self._row_pixel_targets[row_idx] = float(target_card_x + CARD_WIDTH - visible_w)

    # ---- Smooth-scroll animation -------------------------------------------

    def _animate_scroll(self):
        """Per-frame critically-damped spring scroll (#175).

        Velocity-aware spring gives a TV-style fluid feel: the row
        gently accelerates toward the target and decelerates as it
        approaches, instead of the linear easing it had before.
        """
        try:
            changed = False
            # Tuned for ~60fps tick. stiffness ~ k/m, damping ~ c/m
            stiffness = 0.18
            damping = 0.55

            # Ensure velocity arrays match length (rows can change at runtime)
            while len(self._row_pixel_velocity) < len(self._row_pixel_offsets):
                self._row_pixel_velocity.append(0.0)
            while len(self._row_pixel_velocity) > len(self._row_pixel_offsets):
                self._row_pixel_velocity.pop()

            for i in range(len(self._row_pixel_offsets)):
                delta = self._row_pixel_targets[i] - self._row_pixel_offsets[i]
                v = self._row_pixel_velocity[i]
                if abs(delta) > 0.4 or abs(v) > 0.4:
                    v = v * (1.0 - damping) + delta * stiffness
                    self._row_pixel_velocity[i] = v
                    self._row_pixel_offsets[i] += v
                    changed = True
                else:
                    self._row_pixel_offsets[i] = self._row_pixel_targets[i]
                    self._row_pixel_velocity[i] = 0.0

            v_delta = self._vertical_target - self._vertical_offset
            vv = self._vertical_velocity
            if abs(v_delta) > 0.4 or abs(vv) > 0.4:
                vv = vv * (1.0 - damping) + v_delta * stiffness
                self._vertical_velocity = vv
                self._vertical_offset += vv
                changed = True
            else:
                self._vertical_offset = self._vertical_target
                self._vertical_velocity = 0.0

            if changed and self._state == "browse":
                self._draw()
        finally:
            self._anim_id = self.root.after(16, self._animate_scroll)

    # ---- Playback -----------------------------------------------------------

    def _play_selected(self, event=None):
        """Play the currently focused channel."""
        if self._state == "playing":
            return
        ch = self._get_focused_channel()
        if not ch:
            return

        if self._parental and self._parental.is_channel_blocked(ch):
            self._show_toast("Channel blocked by parental controls")
            return

        url = ch.get('url', '')
        if not url:
            self._show_toast("No stream URL")
            return

        if self._watch_history:
            try:
                self._watch_history.record_play(ch)
            except Exception:
                pass

        self._player_channel = ch
        self._start_player(url, ch.get('name', 'Unknown'))

    def _start_player(self, url, channel_name):
        """Switch to playing state with embedded VLC."""
        if not VLC_AVAILABLE or VLCController is None:
            self._show_toast("VLC not available \u2014 install python-vlc")
            return

        self._state = "playing"

        self._canvas.pack_forget()
        if self._search_frame.winfo_ismapped():
            self._search_frame.pack_forget()

        self._player_frame = tk.Frame(self.root, bg="#000000")
        self._player_frame.pack(fill=tk.BOTH, expand=True, before=self._info_frame)

        self._vlc_canvas = tk.Canvas(self._player_frame, bg="#000000",
                                     highlightthickness=0, borderwidth=0)
        self._vlc_canvas.pack(fill=tk.BOTH, expand=True)

        self._player_frame.update_idletasks()

        self._vlc = VLCController()
        hwnd = self._vlc_canvas.winfo_id()
        if not self._vlc.initialize(hwnd, self._player_volume):
            self._show_toast("Failed to initialise VLC")
            self._stop_player()
            return

        if not self._vlc.play_url(url):
            self._show_toast("Failed to play stream")
            self._stop_player()
            return

        self._show_player_osd(channel_name)
        self._info_label.config(text=f"\u25b6 {channel_name}")

    def _show_player_osd(self, channel_name):
        """Show channel name overlay + live metadata strip (Issues #165 + #172)."""
        if self._osd_timer:
            self.root.after_cancel(self._osd_timer)

        ch_num = ""
        if self._player_channel:
            n = self._channel_numbers.get(id(self._player_channel))
            if n:
                ch_num = f"Ch.{n}  "

        self._osd_label = tk.Label(
            self._player_frame, text=f"{ch_num}{channel_name}",
            bg=TVColors.PLAYER_OSD_BG, fg=TVColors.TEXT_PRIMARY,
            font=(FONT_FAMILY, 22, "bold"), padx=20, pady=10,
        )
        self._osd_label.place(relx=0.02, rely=0.04, anchor="nw")
        # Lift above VLC canvas so the label is actually visible (#175)
        try:
            self._osd_label.lift()
        except Exception:
            pass

        # Bottom-right metadata strip (resolution / fps / bitrate / cast)
        self._osd_meta_label = tk.Label(
            self._player_frame, text="",
            bg=TVColors.PLAYER_OSD_BG, fg=TVColors.TEXT_SECONDARY,
            font=("Consolas", 11), padx=14, pady=6,
        )
        self._osd_meta_label.place(relx=0.98, rely=0.96, anchor="se")
        try:
            self._osd_meta_label.lift()
        except Exception:
            pass

        self._osd_timer = self.root.after(OSD_FADE_MS, self._hide_osd)
        # Start metadata polling (cancelled when player stops or OSD hides)
        self._meta_poll_active = True
        self._poll_player_metadata()

    def _poll_player_metadata(self):
        """Periodically refresh the bottom OSD strip with VLC metadata."""
        if not getattr(self, '_meta_poll_active', False):
            return
        if self._state != "playing" or not self._vlc:
            return
        try:
            w, h = self._vlc.get_video_dimensions()
            fps = self._vlc.get_fps()
            stats = self._vlc.get_media_stats()
            bitrate_kbps = 0
            if stats is not None:
                # demux_bitrate is float in MB/s — convert to kb/s
                try:
                    bitrate_kbps = int(getattr(stats, 'demux_bitrate', 0.0) * 8000)
                except Exception:
                    bitrate_kbps = 0

            parts = []
            if w and h:
                parts.append(f"{w}\u00d7{h}")
            if fps and fps > 0.1:
                parts.append(f"{fps:.0f}fps")
            if bitrate_kbps:
                parts.append(f"{bitrate_kbps}kbps")
            if not parts:
                parts.append("buffering\u2026")
            text = "  \u2022  ".join(parts)
            if hasattr(self, '_osd_meta_label') and self._osd_meta_label is not None:
                try:
                    self._osd_meta_label.config(text=text)
                except Exception:
                    pass
        except Exception:
            pass
        # Keep polling every 1s while playing
        self.root.after(1000, self._poll_player_metadata)

    def _hide_osd(self):
        try:
            if hasattr(self, '_osd_label') and self._osd_label:
                self._osd_label.place_forget()
                self._osd_label.destroy()
                self._osd_label = None
        except Exception:
            pass
        # Keep meta strip visible — it stays until player stops
        self._osd_timer = None

    def _show_osd_again(self, event=None):
        """Re-show channel name OSD on user input during playback."""
        if self._state != "playing" or not self._player_channel:
            return
        name = self._player_channel.get('name', 'Unknown')
        # Restart the title label only
        if hasattr(self, '_osd_label') and self._osd_label is not None:
            try:
                self._osd_label.destroy()
            except Exception:
                pass
            self._osd_label = None
        ch_num = ""
        n = self._channel_numbers.get(id(self._player_channel))
        if n:
            ch_num = f"Ch.{n}  "
        self._osd_label = tk.Label(
            self._player_frame, text=f"{ch_num}{name}",
            bg=TVColors.PLAYER_OSD_BG, fg=TVColors.TEXT_PRIMARY,
            font=(FONT_FAMILY, 22, "bold"), padx=20, pady=10,
        )
        self._osd_label.place(relx=0.02, rely=0.04, anchor="nw")
        if self._osd_timer:
            try:
                self.root.after_cancel(self._osd_timer)
            except Exception:
                pass
        self._osd_timer = self.root.after(OSD_FADE_MS, self._hide_osd)

    def _stop_player(self):
        """Stop VLC and return to browse state."""
        # Stop metadata polling
        self._meta_poll_active = False

        if self._osd_timer:
            self.root.after_cancel(self._osd_timer)
            self._osd_timer = None
        # Drop meta label reference
        if hasattr(self, '_osd_meta_label') and self._osd_meta_label is not None:
            try:
                self._osd_meta_label.destroy()
            except Exception:
                pass
            self._osd_meta_label = None

        if self._vlc:
            try:
                self._vlc.stop()
                self._vlc.cleanup()
            except Exception:
                pass
            self._vlc = None

        if self._player_frame:
            self._player_frame.destroy()
            self._player_frame = None

        self._state = "browse"
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._draw()

    def _channel_next(self):
        """Play next channel (player mode)."""
        if self._state != "playing" or not self._rows:
            return
        row = self._rows[self._row_index]
        if self._col_index < len(row["channels"]) - 1:
            self._col_index += 1
        elif self._row_index < len(self._rows) - 1:
            self._row_index += 1
            self._col_index = 0
        else:
            return
        self._stop_player()
        self._play_selected()

    def _channel_prev(self):
        """Play previous channel (player mode)."""
        if self._state != "playing" or not self._rows:
            return
        if self._col_index > 0:
            self._col_index -= 1
        elif self._row_index > 0:
            self._row_index -= 1
            self._col_index = max(0, len(self._rows[self._row_index]["channels"]) - 1)
        else:
            return
        self._stop_player()
        self._play_selected()

    # ---- Search -------------------------------------------------------------

    def _toggle_search(self):
        if self._state == "playing":
            return
        if self._search_active:
            self._close_search()
        else:
            self._open_search()

    def _open_search(self):
        self._search_active = True
        self._search_frame.pack(fill=tk.X, side=tk.TOP, before=self._canvas)
        self._search_entry.focus_set()

    def _close_search(self):
        self._search_active = False
        self._search_var.set("")
        self._search_frame.pack_forget()
        self._filtered_channels = None
        self._row_index = 0
        self._col_index = 0
        self._build_rows()
        self._draw()
        self.root.focus_set()

    def _on_search_changed(self, *args):
        query = self._search_var.get().strip().lower()
        if not query:
            self._filtered_channels = None
        else:
            self._filtered_channels = [
                ch for ch in self._all_channels
                if query in ch.get('name', '').lower()
                or query in ch.get('category', '').lower()
                or query in ch.get('country', '').lower()
            ]
        self._row_index = 0
        self._col_index = 0
        self._build_rows()
        self._draw()

    def _search_select(self):
        self._close_search()

    # ---- Favorites Toggle ---------------------------------------------------

    def _on_f_key(self, event=None):
        if self._state == "playing":
            return
        ch = self._get_focused_channel()
        if not ch or not self._favorites_manager:
            return
        url = ch.get('url', '')
        if not url:
            return
        self._favorites_manager.toggle_favorite(url)
        if url in self._favorite_urls:
            self._favorite_urls.discard(url)
            self._show_toast("Removed from favorites")
        else:
            self._favorite_urls.add(url)
            self._show_toast("Added to favorites")
        self._draw()

    # ---- Settings -----------------------------------------------------------

    def _open_settings(self):
        if self._state == "playing":
            return
        try:
            from ui.settings_dialog import show_settings_dialog
            show_settings_dialog(self)
        except Exception as e:
            self._show_toast(f"Settings unavailable: {e}")
            logger.error(f"Settings dialog error: {e}")

    def _open_submit_dialog(self):
        """Open the Submit Channel / contribute dialog (Issue #161)."""
        if self._state == "playing":
            return
        try:
            from ui.contribute_dialog import show_contribute_dialog
            show_contribute_dialog(self.root)
            self._show_toast("Thanks for contributing! Re-scan to see new channels")
        except Exception as e:
            self._show_toast(f"Submit unavailable: {e}")
            logger.error(f"Contribute dialog error: {e}")

    def _open_filter(self):
        """Open the channel filter dialog (Issue #160)."""
        if self._state == "playing":
            return
        try:
            from ui.filter_dialog import show_filter_dialog

            # Build sorted unique sets across all loaded channels
            langs, countries, cats = set(), set(), set()
            for ch in self._all_channels:
                lang = (ch.get('language') or '').strip()
                if lang:
                    langs.add(lang)
                country = (ch.get('country') or '').strip()
                if country:
                    countries.add(country)
                cat = (ch.get('category') or 'Other').strip()
                if cat:
                    cats.add(cat)

            def _on_apply(new_filters):
                self._active_filters = new_filters
                self._build_rows()
                self._draw()
                active_count = sum(len(v) for v in new_filters.values())
                if active_count:
                    self._show_toast(f"Filter applied ({active_count} criteria)")
                else:
                    self._show_toast("Filters cleared")

            show_filter_dialog(
                self.root,
                sorted(langs), sorted(countries), sorted(cats),
                self._active_filters,
                _on_apply,
            )
        except Exception as e:
            self._show_toast(f"Filter unavailable: {e}")
            logger.error(f"Filter dialog error: {e}")

    def _open_tour(self):
        """Show the first-run tooltip tour (Issue #162). Available from ? button."""
        if self._state == "playing":
            return
        try:
            from ui.tour_overlay import show_tour
            show_tour(self.root)
        except Exception as e:
            logger.error(f"Tour error: {e}")

    def _open_map(self):
        """Open the world map view of channels (Issue #167)."""
        if self._state == "playing":
            return
        try:
            from ui.map_window import MapWindow
            MapWindow(
                self.root,
                self._channel_manager,
                self._favorites_manager,
                on_play_channel=self._play_channel_from_map,
            )
        except Exception as e:
            self._show_toast(f"Map unavailable: {e}")
            logger.error(f"Map window error: {e}")

    def _play_channel_from_map(self, channel):
        """Callback for map view to start playback."""
        try:
            url = channel.get('url', '')
            if not url:
                return
            self._player_channel = channel
            if self._watch_history:
                try:
                    self._watch_history.record_play(channel)
                except Exception:
                    pass
            self._start_player(url, channel.get('name', 'Unknown'))
        except Exception as e:
            logger.error(f"Map play failed: {e}")

    # ---- Key Handlers -------------------------------------------------------

    def _on_escape(self, event=None):
        if self._search_active:
            self._close_search()
            return
        if self._state == "playing":
            self._stop_player()
            return
        self._on_close()

    def _on_backspace(self, event=None):
        if self._search_active:
            return
        if self._state == "playing":
            self._stop_player()

    def _on_space(self, event=None):
        if self._state == "playing" and self._vlc:
            self._vlc.pause()

    def _toggle_fullscreen(self):
        self._is_fullscreen = not self._is_fullscreen
        self.root.attributes("-fullscreen", self._is_fullscreen)

    def _toggle_mute(self):
        if self._vlc:
            muted = self._vlc.get_mute()
            self._vlc.set_mute(not muted)
            self._show_toast("\U0001f507 Muted" if not muted else "\U0001f50a Unmuted")

    def _volume_change(self, delta):
        if self._vlc and self._state == "playing":
            self._player_volume = max(0, min(100, self._player_volume + delta))
            self._vlc.set_volume(self._player_volume)
            self._show_toast(f"\U0001f50a Volume: {self._player_volume}%")

    # ---- Mouse Support ------------------------------------------------------

    def _on_canvas_click(self, event):
        if not self._rows or self._state != "browse":
            return
        hit = self._hit_test(event.x, event.y)
        if hit is None:
            return
        row_idx, col_idx = hit
        if self._row_index == row_idx and self._col_index == col_idx:
            self._play_selected()
        else:
            if row_idx != self._row_index:
                self._change_row(row_idx)
            self._col_index = col_idx
            self._clamp_col()
            self._ensure_col_visible()
            self._draw()

    def _on_resize(self, event=None):
        self.root.after(50, self._draw)

    # ---- Mouse wheel & hover -----------------------------------------------

    def _on_mouse_wheel(self, event):
        # Vertical wheel = move row up/down
        direction = -1 if event.delta > 0 else 1
        self._mouse_wheel_step(direction, vertical=True)

    def _on_shift_mouse_wheel(self, event):
        # Shift+wheel = horizontal scroll within current row
        direction = -1 if event.delta > 0 else 1
        self._mouse_wheel_step(direction, vertical=False)

    def _mouse_wheel_step(self, direction, vertical):
        if self._state != "browse" or not self._rows:
            return
        if vertical:
            new_row = max(0, min(len(self._rows) - 1, self._row_index + direction))
            if new_row != self._row_index:
                self._change_row(new_row)
        else:
            row_idx = self._row_index
            if row_idx >= len(self._row_pixel_targets):
                return
            cw = self._canvas.winfo_width() or 1280
            row_len = len(self._rows[row_idx]["channels"])
            max_offset = max(
                0,
                row_len * (CARD_WIDTH + CARD_GAP) - (cw - 64)
            )
            delta = direction * (CARD_WIDTH + CARD_GAP)
            self._row_pixel_targets[row_idx] = max(
                0.0, min(float(max_offset),
                         self._row_pixel_targets[row_idx] + delta)
            )

    def _on_canvas_motion(self, event):
        """Highlight the card under the cursor (mouse hover).

        Issue #157: Hover MUST NOT change rows — that causes the canvas
        to scroll vertically just from mouse motion. Only update the
        column focus within the currently-active row.
        """
        if self._state != "browse" or not self._rows:
            return
        hit = self._hit_test(event.x, event.y)
        if hit is None:
            return
        row_idx, col_idx = hit
        if (row_idx, col_idx) == self._hover_pos:
            return
        self._hover_pos = (row_idx, col_idx)
        # Only react to hovers within the active row (no auto-row-change).
        if row_idx != self._row_index:
            return
        if col_idx == self._col_index:
            return
        self._col_index = col_idx
        self._clamp_col()
        self._ensure_col_visible()
        self._draw()

    def _hit_test(self, mx, my):
        """Return (row_idx, col_idx) under (mx, my) or None."""
        if not self._rows:
            return None
        y_offset = 80 + int(self._vertical_offset)
        start_row = max(0, self._row_index - 1)
        end_row = min(len(self._rows), start_row + VISIBLE_ROWS)
        if end_row - start_row < VISIBLE_ROWS and start_row > 0:
            start_row = max(0, end_row - VISIBLE_ROWS)
        for row_idx in range(start_row, end_row):
            row = self._rows[row_idx]
            is_active = (row_idx == self._row_index)
            y_top = y_offset + ROW_LABEL_HEIGHT
            card_h = CARD_HEIGHT_FOCUS if is_active else CARD_HEIGHT
            if y_top <= my <= y_top + card_h:
                if row_idx < len(self._row_pixel_offsets):
                    x_start = 32 - self._row_pixel_offsets[row_idx]
                else:
                    x_start = 32
                for col_idx in range(len(row["channels"])):
                    x = x_start + col_idx * (CARD_WIDTH + CARD_GAP)
                    if x <= mx <= x + CARD_WIDTH:
                        return (row_idx, col_idx)
                return None
            y_offset += ROW_LABEL_HEIGHT + CARD_HEIGHT_FOCUS + 20
        return None

    # ---- Channel Number Jump ------------------------------------------------

    def _on_number_key(self, event):
        if self._state == "playing":
            return
        digit = event.char if event.char and event.char.isdigit() else ''
        if not digit:
            ks = event.keysym
            if ks.startswith("KP_") and ks[-1].isdigit():
                digit = ks[-1]
        if not digit:
            return

        if len(self._number_buffer) >= MAX_NUMBER_DIGITS:
            return

        self._number_buffer += digit
        self._show_number_overlay()

        if self._number_timer:
            self.root.after_cancel(self._number_timer)
        self._number_timer = self.root.after(NUMBER_TIMEOUT_MS, self._execute_number_jump)

    def _show_number_overlay(self):
        self._number_label.config(text=f"Ch. {self._number_buffer}_")
        self._number_label.place(relx=0.5, rely=0.12, anchor="center")

    def _execute_number_jump(self):
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

        for row_idx, row in enumerate(self._rows):
            for col_idx, ch in enumerate(row["channels"]):
                if self._channel_numbers.get(id(ch)) == target:
                    self._row_index = row_idx
                    self._col_index = col_idx
                    self._ensure_col_visible()
                    self._draw()
                    return

        self._show_toast(f"Channel {target} not found")

    # ---- Toast --------------------------------------------------------------

    def _show_toast(self, message, duration_ms=2000):
        self._toast_label.config(text=message)
        self._toast_label.place(relx=0.5, rely=0.88, anchor="center")
        if self._toast_timer:
            self.root.after_cancel(self._toast_timer)
        self._toast_timer = self.root.after(duration_ms, self._hide_toast)

    def _hide_toast(self):
        self._toast_label.place_forget()
        self._toast_timer = None

    # ---- Public Methods -----------------------------------------------------

    def _get_local_country(self) -> Optional[str]:
        """Detect the user's country from system locale (Issue #169).

        Returns a country name matching the channel ``country`` field
        format (e.g. 'United States'), or None on failure.
        """
        cached = getattr(self, '_local_country_cache', '__missing__')
        if cached != '__missing__':
            return cached
        result: Optional[str] = None
        try:
            import locale
            loc = locale.getdefaultlocale()[0]  # e.g. 'en_US'
            if loc and '_' in loc:
                cc = loc.split('_', 1)[1].split('.')[0].upper()
                # Map ISO-3166 alpha-2 to common channel-list country names
                cc_map = {
                    'US': 'United States', 'GB': 'United Kingdom',
                    'CA': 'Canada', 'AU': 'Australia', 'DE': 'Germany',
                    'FR': 'France', 'ES': 'Spain', 'IT': 'Italy',
                    'IL': 'Israel', 'IN': 'India', 'JP': 'Japan',
                    'BR': 'Brazil', 'MX': 'Mexico', 'NL': 'Netherlands',
                    'RU': 'Russia', 'CN': 'China', 'KR': 'South Korea',
                    'AR': 'Argentina', 'CL': 'Chile', 'CO': 'Colombia',
                    'PT': 'Portugal', 'PL': 'Poland', 'GR': 'Greece',
                    'TR': 'Turkey', 'EG': 'Egypt', 'ZA': 'South Africa',
                }
                result = cc_map.get(cc)
        except Exception:
            pass
        self._local_country_cache = result
        return result

    def refresh_channels(self, channels):
        """Refresh channel data (e.g., after scan completes)."""
        focused_ch = self._get_focused_channel()

        self._all_channels = channels
        self._build_rows()

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

        self._row_index = min(self._row_index, max(0, len(self._rows) - 1))
        self._clamp_col()
        self._draw()

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()

    def _on_close(self):
        """Clean shutdown."""
        logger.info("TVModeApp closing...")
        for timer in [self._clock_timer, self._number_timer,
                      self._toast_timer, self._scan_timer, self._osd_timer,
                      self._anim_id]:
            if timer:
                try:
                    self.root.after_cancel(timer)
                except Exception:
                    pass
        self._anim_id = None
        if self._state == "playing":
            try:
                self._stop_player()
            except Exception:
                pass
        try:
            self._channel_manager.save_channels()
        except Exception:
            pass
        self.root.destroy()


# Backwards compatibility alias (deprecated)
TVModeWindow = TVModeApp
