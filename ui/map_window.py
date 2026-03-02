"""World Map window — zoomable OpenStreetMap with channel markers."""

import math
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import tkintermapview
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

    def __init__(self, parent, channel_manager, favorites_manager=None,
                 on_play_channel=None):
        """
        Args:
            parent: Parent tkinter widget.
            channel_manager: ChannelManager instance with loaded channels.
            favorites_manager: FavoritesManager instance (optional).
            on_play_channel: Callback(channel_dict) to play a channel.
        """
        if not MAP_AVAILABLE:
            from tkinter import messagebox
            messagebox.showwarning(
                "Map Unavailable",
                "Install tkintermapview:\n  pip install tkintermapview"
            )
            return

        self._parent = parent
        self._cm = channel_manager
        self._fav = favorites_manager
        self._on_play = on_play_channel

        self._markers = []
        self._show_favorites_only = tk.BooleanVar(value=False)
        self._hide_offline = tk.BooleanVar(value=False)

        self._build_window()
        self._place_markers()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_window(self):
        self._win = ctk.CTkToplevel(self._parent)
        self._win.title("🗺️ TV Viewer — World Map")
        self._win.geometry("1100x700")
        self._win.minsize(700, 450)

        # Toolbar
        toolbar = ctk.CTkFrame(self._win, height=40, fg_color="#1e1e2e")
        toolbar.pack(fill="x")

        ctk.CTkLabel(
            toolbar, text="🗺️  World Map", font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=12)

        # Filters
        ctk.CTkCheckBox(
            toolbar, text="★ Favorites only",
            variable=self._show_favorites_only,
            command=self._refresh_markers,
            fg_color="#FFB900", hover_color="#E6A800",
            text_color="white", font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(20, 8))

        ctk.CTkCheckBox(
            toolbar, text="Hide offline",
            variable=self._hide_offline,
            command=self._refresh_markers,
            fg_color="#13A10E", hover_color="#0F8A0A",
            text_color="white", font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=8)

        # Channel count label
        self._count_label = ctk.CTkLabel(
            toolbar, text="", font=ctk.CTkFont(size=12),
            text_color="#888",
        )
        self._count_label.pack(side="right", padx=12)

        # Map widget
        self._map = TkinterMapView(
            self._win, corner_radius=0,
        )
        self._map.pack(fill="both", expand=True)
        self._map.set_position(30, 20)
        self._map.set_zoom(3)

    # ------------------------------------------------------------------
    # Marker management
    # ------------------------------------------------------------------

    def _get_filtered_channels(self) -> List[dict]:
        """Return channels after applying current filters."""
        channels = list(self._cm.channels)
        if self._show_favorites_only.get() and self._fav:
            channels = [c for c in channels if self._fav.is_favorite(c.get('url', ''))]
        if self._hide_offline.get():
            channels = [c for c in channels if c.get('status') != 'offline']
        return channels

    def _group_by_country(self, channels) -> Dict[str, List[dict]]:
        grouped: Dict[str, List[dict]] = {}
        for ch in channels:
            country = ch.get('country', '') or ''
            if not country:
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
        for country, ch_list in grouped.items():
            coords = COUNTRY_COORDS.get(country)
            if not coords:
                continue

            lat, lon = coords
            count = len(ch_list)
            working = sum(1 for c in ch_list if c.get('status') != 'offline')

            # Marker text: "🇬🇧 42" style — use country name + count
            short = country[:3].upper()
            label = f"{short} ({count})"

            marker = self._map.set_marker(
                lat, lon,
                text=label,
                command=lambda e=None, c=country, chs=ch_list: self._on_marker_click(c, chs),
            )
            self._markers.append(marker)
            total_placed += count

        self._count_label.configure(
            text=f"{total_placed} channels in {len(grouped)} countries"
        )

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def _on_marker_click(self, country: str, channels: List[dict]):
        """Show a popup list of channels for the clicked country."""
        popup = ctk.CTkToplevel(self._win)
        popup.title(f"📺 {country} — {len(channels)} channels")
        popup.geometry("480x500")
        popup.transient(self._win)
        popup.grab_set()

        # Header
        header = ctk.CTkFrame(popup, fg_color="#1e1e2e", height=44)
        header.pack(fill="x")
        working = sum(1 for c in channels if c.get('status') != 'offline')
        ctk.CTkLabel(
            header,
            text=f"🌍 {country}  —  {len(channels)} channels  ({working} working)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=12, pady=8)

        # Scrollable channel list
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        for ch in channels:
            self._add_channel_row(scroll, ch, popup)

    def _add_channel_row(self, parent, ch: dict, popup):
        """Add a single channel row to the popup list."""
        is_working = ch.get('status') != 'offline'
        is_fav = self._fav.is_favorite(ch.get('url', '')) if self._fav else False

        row = ctk.CTkFrame(parent, fg_color="#2a2a3a", corner_radius=6, height=44)
        row.pack(fill="x", pady=2, padx=2)
        row.pack_propagate(False)

        # Status indicator
        status_color = "#13A10E" if is_working else "#F04A58"
        ctk.CTkLabel(
            row, text="●", text_color=status_color,
            font=ctk.CTkFont(size=14), width=24,
        ).pack(side="left", padx=(8, 4))

        # Favorite star
        star = "★" if is_fav else "☆"
        star_color = "#FFB900" if is_fav else "#555"
        star_label = ctk.CTkLabel(
            row, text=star, text_color=star_color,
            font=ctk.CTkFont(size=16), width=24, cursor="hand2",
        )
        star_label.pack(side="left", padx=(0, 4))
        if self._fav:
            star_label.bind("<Button-1>", lambda e, url=ch.get('url', ''): self._toggle_fav(url, star_label))

        # Channel name
        name = ch.get('name', 'Unknown')
        ctk.CTkLabel(
            row, text=name, font=ctk.CTkFont(size=13),
            text_color="white", anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=4)

        # Category badge
        cat = ch.get('category', '')
        if cat:
            ctk.CTkLabel(
                row, text=cat, font=ctk.CTkFont(size=10),
                text_color="#888", width=70, anchor="e",
            ).pack(side="left", padx=4)

        # Play button
        play_btn = ctk.CTkButton(
            row, text="▶", width=36, height=28,
            fg_color="#0078D4", hover_color="#106EBE",
            font=ctk.CTkFont(size=14),
            command=lambda c=ch, p=popup: self._play(c, p),
        )
        play_btn.pack(side="right", padx=8)

    def _toggle_fav(self, url: str, label):
        if not self._fav:
            return
        if self._fav.is_favorite(url):
            self._fav.remove_favorite(url)
            label.configure(text="☆", text_color="#555")
        else:
            self._fav.add_favorite(url)
            label.configure(text="★", text_color="#FFB900")

    def _play(self, channel: dict, popup):
        popup.destroy()
        if self._on_play:
            self._on_play(channel)
