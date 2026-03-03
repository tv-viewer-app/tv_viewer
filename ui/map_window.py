"""World Map window — zoomable OpenStreetMap with animated channel markers."""

import math
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

try:
    from tkintermapview import TkinterMapView
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False
    logger.warning("tkintermapview not installed — Map feature unavailable")

# Country center coordinates {name: (lat, lon)}
COUNTRY_COORDS: Dict[str, Tuple[float, float]] = {
    'Afghanistan': (33.93, 67.71), 'Albania': (41.15, 20.17),
    'Algeria': (28.03, 1.66), 'Andorra': (42.55, 1.60),
    'Angola': (-11.20, 17.87), 'Argentina': (-38.42, -63.62),
    'Armenia': (40.07, 45.04), 'Australia': (-25.27, 133.78),
    'Austria': (47.52, 14.55), 'Azerbaijan': (40.14, 47.58),
    'Bahrain': (26.07, 50.55), 'Bangladesh': (23.68, 90.36),
    'Belarus': (53.71, 27.95), 'Belgium': (50.50, 4.47),
    'Bolivia': (-16.29, -63.59), 'Bosnia and Herzegovina': (43.92, 17.68),
    'Brazil': (-14.24, -51.93), 'Bulgaria': (42.73, 25.49),
    'Cambodia': (12.57, 104.99), 'Cameroon': (7.37, 12.35),
    'Canada': (56.13, -106.35), 'Chile': (-35.68, -71.54),
    'China': (35.86, 104.20), 'Colombia': (4.57, -74.30),
    'Costa Rica': (9.75, -83.75), 'Croatia': (45.10, 15.20),
    'Cuba': (21.52, -77.78), 'Cyprus': (35.13, 33.43),
    'Czech Republic': (49.82, 15.47), 'Czechia': (49.82, 15.47),
    'Denmark': (56.26, 9.50), 'Dominican Republic': (18.74, -70.16),
    'Ecuador': (-1.83, -78.18), 'Egypt': (26.82, 30.80),
    'El Salvador': (13.79, -88.90), 'Estonia': (58.60, 25.01),
    'Ethiopia': (9.15, 40.49), 'Finland': (61.92, 25.75),
    'France': (46.23, 2.21), 'Georgia': (42.32, 43.36),
    'Germany': (51.17, 10.45), 'Ghana': (7.95, -1.02),
    'Greece': (39.07, 21.82), 'Guatemala': (15.78, -90.23),
    'Honduras': (15.20, -86.24), 'Hong Kong': (22.40, 114.11),
    'Hungary': (47.16, 19.50), 'Iceland': (64.96, -19.02),
    'India': (20.59, 78.96), 'Indonesia': (-0.79, 113.92),
    'Iran': (32.43, 53.69), 'Iraq': (33.22, 43.68),
    'Ireland': (53.14, -7.69), 'Israel': (31.05, 34.85),
    'Italy': (41.87, 12.57), 'Jamaica': (18.11, -77.30),
    'Japan': (36.20, 138.25), 'Jordan': (30.59, 36.24),
    'Kazakhstan': (48.02, 66.92), 'Kenya': (-0.02, 37.91),
    'Kosovo': (42.60, 20.90), 'Kuwait': (29.31, 47.48),
    'Latvia': (56.88, 24.60), 'Lebanon': (33.85, 35.86),
    'Libya': (26.34, 17.23), 'Lithuania': (55.17, 23.88),
    'Luxembourg': (49.82, 6.13), 'Macedonia': (41.51, 21.75),
    'North Macedonia': (41.51, 21.75), 'Malaysia': (4.21, 101.98),
    'Mexico': (23.63, -102.55), 'Moldova': (47.41, 28.37),
    'Mongolia': (46.86, 103.85), 'Montenegro': (42.71, 19.37),
    'Morocco': (31.79, -7.09), 'Mozambique': (-18.67, 35.53),
    'Myanmar': (21.91, 95.96), 'Nepal': (28.39, 84.12),
    'Netherlands': (52.13, 5.29), 'New Zealand': (-40.90, 174.89),
    'Nicaragua': (12.87, -85.21), 'Nigeria': (9.08, 8.68),
    'Norway': (60.47, 8.47), 'Oman': (21.47, 55.98),
    'Pakistan': (30.38, 69.35), 'Palestine': (31.95, 35.23),
    'Panama': (8.54, -80.78), 'Paraguay': (-23.44, -58.44),
    'Peru': (-9.19, -75.02), 'Philippines': (12.88, 121.77),
    'Poland': (51.92, 19.15), 'Portugal': (39.40, -8.22),
    'Qatar': (25.35, 51.18), 'Romania': (45.94, 24.97),
    'Russia': (61.52, 105.32), 'Saudi Arabia': (23.89, 45.08),
    'Serbia': (44.02, 21.01), 'Singapore': (1.35, 103.82),
    'Slovakia': (48.67, 19.70), 'Slovenia': (46.15, 14.99),
    'South Africa': (-30.56, 22.94), 'South Korea': (35.91, 127.77),
    'Spain': (40.46, -3.75), 'Sri Lanka': (7.87, 80.77),
    'Sudan': (12.86, 30.22), 'Sweden': (60.13, 18.64),
    'Switzerland': (46.82, 8.23), 'Syria': (34.80, 38.99),
    'Taiwan': (23.70, 120.96), 'Thailand': (15.87, 100.99),
    'Tunisia': (33.89, 9.54), 'Turkey': (38.96, 35.24),
    'Turkmenistan': (38.97, 59.56), 'Ukraine': (48.38, 31.17),
    'United Arab Emirates': (23.42, 53.85),
    'United Kingdom': (55.38, -3.44),
    'United States': (37.09, -95.71),
    'Uruguay': (-32.52, -55.77), 'Uzbekistan': (41.38, 64.59),
    'Venezuela': (6.42, -66.59), 'Vietnam': (14.06, 108.28),
    'Yemen': (15.55, 48.52),
    # Aliases
    'UK': (55.38, -3.44), 'US': (37.09, -95.71),
    'USA': (37.09, -95.71), 'UAE': (23.42, 53.85),
    'Korea': (35.91, 127.77),
}


class MapWindow:
    """Toplevel window showing a zoomable world map of TV stream sources."""

    # Fluent Design colors
    _BG = "#1b1a1f"
    _SURFACE = "#252429"
    _CARD = "#2d2c31"
    _CARD_HOVER = "#383740"
    _ACCENT = "#0078D4"
    _ACCENT_HOVER = "#106EBE"
    _TEXT = "#ffffff"
    _TEXT_SEC = "#b3b3b3"
    _GREEN = "#13A10E"
    _RED = "#F04A58"
    _AMBER = "#FFB900"
    _BORDER = "#3b3a3f"

    # Cached fonts (created once, reused across all rows)
    _FONTS_INIT = False
    _F_TITLE = None
    _F_BODY = None
    _F_SMALL = None
    _F_DOT = None
    _F_STAR = None
    _F_PLAY = None

    @classmethod
    def _init_fonts(cls):
        if cls._FONTS_INIT:
            return
        cls._F_TITLE = ctk.CTkFont(size=16, weight="bold")
        cls._F_BODY = ctk.CTkFont(size=13)
        cls._F_SMALL = ctk.CTkFont(size=11)
        cls._F_TINY = ctk.CTkFont(size=10)
        cls._F_DOT = ctk.CTkFont(size=16)
        cls._F_STAR = ctk.CTkFont(size=18)
        cls._F_PLAY = ctk.CTkFont(size=15)
        cls._F_STAT_VAL = ctk.CTkFont(size=18, weight="bold")
        cls._F_STAT_LBL = ctk.CTkFont(size=10)
        cls._F_SEARCH = ctk.CTkFont(size=12)
        cls._F_SEARCH_ICON = ctk.CTkFont(size=13)
        cls._FONTS_INIT = True

    def __init__(self, parent, channel_manager, favorites_manager=None,
                 on_play_channel=None):
        if not MAP_AVAILABLE:
            from tkinter import messagebox
            messagebox.showwarning(
                "Map Unavailable",
                "Install tkintermapview:\n  pip install tkintermapview"
            )
            return

        MapWindow._init_fonts()

        self._parent = parent
        self._cm = channel_manager
        self._fav = favorites_manager
        self._on_play = on_play_channel

        self._markers = []
        self._show_favorites_only = tk.BooleanVar(value=False)
        self._hide_offline = tk.BooleanVar(value=False)
        self._search_var = tk.StringVar()
        self._search_debounce_id = None
        self._cached_grouped = {}

        # Pause background scanning while map is open to free network for tiles
        try:
            self._cm.stream_checker.pause()
        except Exception:
            pass

        try:
            self._build_window()
            self._win.protocol("WM_DELETE_WINDOW", self._on_close)
            self._win.after(300, self._place_markers)
            self._win.after(100, lambda: self._animate_open())
        except Exception:
            # Resume scanning if map init fails
            try:
                self._cm.stream_checker.resume()
            except Exception:
                pass
            raise

    def _on_close(self):
        """Resume scanning when map window closes."""
        try:
            self._cm.stream_checker.resume()
        except Exception:
            pass
        self._win.destroy()

    def _animate_open(self):
        """Fade-in effect on window open."""
        try:
            self._win.attributes('-alpha', 0.0)
            self._fade_in(0.0)
        except tk.TclError:
            pass

    def _fade_in(self, alpha):
        if alpha >= 1.0:
            self._win.attributes('-alpha', 1.0)
            return
        self._win.attributes('-alpha', alpha)
        self._win.after(20, lambda: self._fade_in(alpha + 0.08))

    def _build_window(self):
        self._win = ctk.CTkToplevel(self._parent)
        self._win.title("🗺️ TV Viewer — World Map")
        self._win.geometry("1200x750")
        self._win.minsize(800, 500)
        self._win.configure(fg_color=self._BG)

        # ── Top toolbar ──
        toolbar = ctk.CTkFrame(self._win, height=50, fg_color=self._SURFACE,
                               corner_radius=0)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkLabel(
            toolbar, text="🗺️  World Map",
            font=self._F_TITLE,
            text_color=self._TEXT,
        ).pack(side="left", padx=16)

        # Search box
        search_frame = ctk.CTkFrame(toolbar, fg_color=self._CARD,
                                     corner_radius=8, height=32)
        search_frame.pack(side="left", padx=16, pady=9)
        ctk.CTkLabel(search_frame, text="🔍", width=28,
                     font=self._F_SEARCH_ICON).pack(side="left", padx=(8, 0))
        self._search_entry = ctk.CTkEntry(
            search_frame, textvariable=self._search_var,
            placeholder_text="Search country...",
            fg_color="transparent", border_width=0, width=160, height=28,
            font=self._F_SEARCH,
        )
        self._search_entry.pack(side="left", padx=(0, 8))
        self._search_var.trace_add("write", lambda *_: self._on_search())

        # Filter toggles with animated state
        self._fav_btn = ctk.CTkButton(
            toolbar, text="★ Favorites",
            fg_color="transparent", hover_color=self._CARD_HOVER,
            text_color=self._TEXT_SEC, font=self._F_SEARCH,
            width=100, height=32, corner_radius=16,
            border_width=1, border_color=self._BORDER,
            command=self._toggle_favorites,
        )
        self._fav_btn.pack(side="left", padx=4)

        self._offline_btn = ctk.CTkButton(
            toolbar, text="📡 Hide offline",
            fg_color="transparent", hover_color=self._CARD_HOVER,
            text_color=self._TEXT_SEC, font=self._F_SEARCH,
            width=120, height=32, corner_radius=16,
            border_width=1, border_color=self._BORDER,
            command=self._toggle_offline,
        )
        self._offline_btn.pack(side="left", padx=4)

        # Stats panel (right side of toolbar)
        self._stats_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        self._stats_frame.pack(side="right", padx=16)

        self._stat_countries = self._make_stat_badge(self._stats_frame, "0", "countries")
        self._stat_channels = self._make_stat_badge(self._stats_frame, "0", "channels")
        self._stat_working = self._make_stat_badge(self._stats_frame, "0", "working", self._GREEN)

        # ── Map widget — CartoDB Dark tiles (fast, matches dark theme) ──
        import os, tempfile
        _tile_cache = os.path.join(tempfile.gettempdir(), "tv_viewer_tiles.db")
        self._map = TkinterMapView(
            self._win, corner_radius=0,
            database_path=_tile_cache, max_zoom=17,
        )
        self._map.set_tile_server(
            "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            max_zoom=17,
        )
        self._map.pack(fill="both", expand=True)
        self._map.set_position(30, 20)
        self._map.set_zoom(3)

    def _make_stat_badge(self, parent, value, label, color=None):
        """Create an animated stat counter badge."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=8)
        val_label = ctk.CTkLabel(
            frame, text=value,
            font=self._F_STAT_VAL,
            text_color=color or self._ACCENT,
        )
        val_label.pack()
        ctk.CTkLabel(
            frame, text=label,
            font=self._F_STAT_LBL,
            text_color=self._TEXT_SEC,
        ).pack()
        return val_label

    # ── Filter toggle animations ──

    def _toggle_favorites(self):
        new_val = not self._show_favorites_only.get()
        self._show_favorites_only.set(new_val)
        if new_val:
            self._fav_btn.configure(
                fg_color=self._AMBER, text_color="#000",
                border_color=self._AMBER, text="★ Favorites ✓"
            )
        else:
            self._fav_btn.configure(
                fg_color="transparent", text_color=self._TEXT_SEC,
                border_color=self._BORDER, text="★ Favorites"
            )
        self._refresh_markers()

    def _toggle_offline(self):
        new_val = not self._hide_offline.get()
        self._hide_offline.set(new_val)
        if new_val:
            self._offline_btn.configure(
                fg_color=self._GREEN, text_color="#fff",
                border_color=self._GREEN, text="📡 Working only ✓"
            )
        else:
            self._offline_btn.configure(
                fg_color="transparent", text_color=self._TEXT_SEC,
                border_color=self._BORDER, text="📡 Hide offline"
            )
        self._refresh_markers()

    def _on_search(self):
        """Debounced search — waits 300ms after last keystroke."""
        if self._search_debounce_id:
            self._win.after_cancel(self._search_debounce_id)
        self._search_debounce_id = self._win.after(300, self._refresh_markers)

    # ── Marker management ──

    def _get_filtered_channels(self) -> List[dict]:
        channels = list(self._cm.channels)
        if self._show_favorites_only.get() and self._fav:
            channels = [c for c in channels if self._fav.is_favorite(c.get('url', ''))]
        if self._hide_offline.get():
            channels = [c for c in channels if c.get('status') != 'offline']
        return channels

    def _group_by_country(self, channels) -> Dict[str, List[dict]]:
        search = self._search_var.get().lower().strip()
        grouped: Dict[str, List[dict]] = {}
        for ch in channels:
            country = ch.get('country', '') or ''
            if not country:
                continue
            if search and search not in country.lower():
                continue
            grouped.setdefault(country, []).append(ch)
        return grouped

    def _clear_markers(self):
        for m in self._markers:
            try:
                m.delete()
            except Exception:
                pass
        self._markers.clear()

    def _refresh_markers(self):
        self._clear_markers()
        self._place_markers()

    def _place_markers(self):
        channels = self._get_filtered_channels()
        grouped = self._group_by_country(channels)

        total_placed = 0
        total_working = 0
        for country, ch_list in grouped.items():
            coords = COUNTRY_COORDS.get(country)
            if not coords:
                continue

            lat, lon = coords
            count = len(ch_list)
            working = sum(1 for c in ch_list if c.get('status') != 'offline')
            total_placed += count
            total_working += working

            short = country[:3].upper()
            label = f"{short} ({count})"

            marker = self._map.set_marker(
                lat, lon, text=label,
                command=lambda e=None, c=country, chs=ch_list: self._on_marker_click(c, chs),
            )
            self._markers.append(marker)

        # Animate stats counters
        self._animate_counter(self._stat_countries, len(grouped))
        self._animate_counter(self._stat_channels, total_placed)
        self._animate_counter(self._stat_working, total_working)

    def _animate_counter(self, label, target, current=0, step=0):
        """Smooth count-up animation for stat badges."""
        if step > 15 or current >= target:
            label.configure(text=str(target))
            return
        # Ease-out: big jumps first, smaller toward the end
        progress = (step + 1) / 16
        value = int(target * progress)
        label.configure(text=str(value))
        self._win.after(30, lambda: self._animate_counter(label, target, value, step + 1))

    # ── Country popup ──

    def _on_marker_click(self, country: str, channels: List[dict]):
        popup = ctk.CTkToplevel(self._win)
        popup.title(f"📺 {country}")
        popup.geometry("520x560")
        popup.transient(self._win)
        popup.configure(fg_color=self._BG)

        # ── Header with health bar ──
        header = ctk.CTkFrame(popup, fg_color=self._SURFACE, height=70,
                              corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        working = sum(1 for c in channels if c.get('status') != 'offline')
        ratio = working / len(channels) if channels else 0

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=16, pady=8)
        ctk.CTkLabel(
            left, text=f"🌍 {country}",
            font=self._F_TITLE, text_color=self._TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text=f"{len(channels)} channels  •  {working} working  •  {len(channels) - working} offline",
            font=self._F_SMALL, text_color=self._TEXT_SEC,
        ).pack(anchor="w")

        # Health bar
        bar_bg = ctk.CTkFrame(header, fg_color=self._CARD, height=6,
                              corner_radius=3, width=120)
        bar_bg.pack(side="right", padx=16)
        bar_bg.pack_propagate(False)
        bar_color = self._GREEN if ratio > 0.7 else self._AMBER if ratio > 0.3 else self._RED
        self._bar_fill = ctk.CTkFrame(bar_bg, fg_color=bar_color, height=6,
                                       corner_radius=3, width=max(1, int(120 * ratio)))
        self._bar_fill.place(x=0, y=0, relheight=1)

        # ── Channel list — small batches for instant popup ──
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent",
                                         scrollbar_button_color=self._CARD)
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # Sort: working channels first for user convenience
        sorted_channels = sorted(channels, key=lambda c: (0 if c.get('status') != 'offline' else 1))

        self._popup_channels = sorted_channels
        self._popup_scroll = scroll
        self._popup_ref = popup
        self._popup_loaded = 0
        self._load_channel_batch()

        # Grab focus after first batch renders
        popup.after(50, lambda: popup.grab_set() if popup.winfo_exists() else None)

    def _popup_fade_in(self, popup, alpha):
        if alpha >= 1.0:
            try:
                popup.attributes('-alpha', 1.0)
            except tk.TclError:
                pass
            return
        try:
            popup.attributes('-alpha', alpha)
            popup.after(15, lambda: self._popup_fade_in(popup, alpha + 0.1))
        except tk.TclError:
            pass

    def _load_channel_batch(self):
        """Load next batch of channel rows into the popup (non-blocking)."""
        BATCH_SIZE = 30
        try:
            popup = self._popup_ref
            scroll = self._popup_scroll
            channels = self._popup_channels
            if not popup.winfo_exists():
                return
        except (tk.TclError, AttributeError):
            return

        end = min(self._popup_loaded + BATCH_SIZE, len(channels))
        for i in range(self._popup_loaded, end):
            row = self._create_channel_row(scroll, channels[i], popup)
            row.pack(fill="x", pady=2, padx=2)
        self._popup_loaded = end

        if self._popup_loaded < len(channels):
            popup.after(10, self._load_channel_batch)

    def _animate_bar(self, bar, target_w, current_w=1):
        """Smooth grow animation for health bar."""
        if current_w >= target_w:
            bar.configure(width=max(target_w, 1))
            return
        step = max(1, (target_w - current_w) // 4)
        new_w = min(current_w + step, target_w)
        bar.configure(width=new_w)
        bar.place(x=0, y=0, relheight=1, width=new_w)
        try:
            bar.winfo_toplevel().after(20, lambda: self._animate_bar(bar, target_w, new_w))
        except tk.TclError:
            pass

    def _create_channel_row(self, parent, ch: dict, popup):
        """Create a channel row with hover animation."""
        is_working = ch.get('status') != 'offline'
        is_fav = self._fav.is_favorite(ch.get('url', '')) if self._fav else False

        row = ctk.CTkFrame(parent, fg_color=self._CARD, corner_radius=8,
                           height=52)
        row.pack_propagate(False)

        # Hover animation
        def on_enter(e):
            row.configure(fg_color=self._CARD_HOVER)
        def on_leave(e):
            row.configure(fg_color=self._CARD)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        # Status dot with pulse for working channels
        dot_color = self._GREEN if is_working else self._RED
        dot = ctk.CTkLabel(row, text="●", text_color=dot_color,
                           font=ctk.CTkFont(size=16), width=28)
        dot.pack(side="left", padx=(10, 4))

        # Favorite star toggle
        star_text = "★" if is_fav else "☆"
        star_color = self._AMBER if is_fav else "#555"
        star = ctk.CTkLabel(row, text=star_text, text_color=star_color,
                            font=ctk.CTkFont(size=18), width=28, cursor="hand2")
        star.pack(side="left", padx=(0, 4))

        def toggle_star(e, url=ch.get('url', ''), lbl=star):
            if not self._fav:
                return
            if self._fav.is_favorite(url):
                self._fav.remove_favorite(url)
                lbl.configure(text="☆", text_color="#555")
            else:
                self._fav.add_favorite(url)
                lbl.configure(text="★", text_color=self._AMBER)
                # Bounce animation
                self._bounce_widget(lbl)

        star.bind("<Button-1>", toggle_star)

        # Channel name
        name = ch.get('name', 'Unknown')
        ctk.CTkLabel(
            row, text=name, font=ctk.CTkFont(size=13),
            text_color=self._TEXT, anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=6)

        # Category pill
        cat = ch.get('category', '')
        if cat:
            pill = ctk.CTkLabel(
                row, text=cat, font=ctk.CTkFont(size=10),
                text_color=self._TEXT_SEC, fg_color=self._SURFACE,
                corner_radius=10, width=60, height=20,
            )
            pill.pack(side="left", padx=4)

        # Play button with hover scale effect
        play_btn = ctk.CTkButton(
            row, text="▶", width=40, height=32,
            fg_color=self._ACCENT, hover_color=self._ACCENT_HOVER,
            font=ctk.CTkFont(size=15), corner_radius=8,
            command=lambda c=ch, p=popup: self._play(c, p),
        )
        play_btn.pack(side="right", padx=10)

        return row

    def _bounce_widget(self, widget):
        """Quick scale-bounce animation on a label."""
        original_size = 18
        sizes = [22, 20, 18]
        def step(i=0):
            if i >= len(sizes):
                return
            try:
                widget.configure(font=ctk.CTkFont(size=sizes[i]))
                widget.after(60, lambda: step(i + 1))
            except tk.TclError:
                pass
        step()

    def _play(self, channel: dict, popup):
        popup.destroy()
        if self._on_play:
            self._on_play(channel)
