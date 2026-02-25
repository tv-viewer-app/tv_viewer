"""Channel Grid — responsive card grid with lazy loading for TV Viewer."""

import customtkinter as ctk
from ui.constants import FluentColors, FluentTypography, CardLayout
from ui.channel_card import ChannelCard
from utils.logger import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 50  # Load cards in batches to avoid UI freeze


class ChannelGrid(ctk.CTkFrame):
    """Responsive grid of ChannelCards with lazy loading and search filtering."""

    def __init__(self, parent, on_play=None, on_favorite_toggle=None,
                 favorites_manager=None):
        super().__init__(parent, fg_color=FluentColors.BG_SOLID, corner_radius=0)
        self._on_play = on_play
        self._on_favorite_toggle = on_favorite_toggle
        self._favorites_manager = favorites_manager
        self._all_channels = []
        self._filtered_channels = []
        self._visible_cards = []
        self._load_index = 0
        self._search_text = ""
        self._active_category = "All"
        self._hide_failed = True

        self._build()

    def _build(self):
        """Build the grid container."""
        # Section header
        self._header = ctk.CTkLabel(
            self, text="All Channels",
            font=ctk.CTkFont(family=FluentTypography.FONT_FAMILY,
                             size=FluentTypography.SUBTITLE, weight="bold"),
            text_color=FluentColors.TEXT_PRIMARY,
            anchor="w",
        )
        self._header.pack(fill="x", padx=16, pady=(12, 8))

        # Channel count
        self._count_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family=FluentTypography.FONT_FAMILY,
                             size=FluentTypography.CAPTION),
            text_color=FluentColors.TEXT_SECONDARY,
            anchor="w",
        )
        self._count_label.pack(fill="x", padx=16, pady=(0, 8))

        # Scrollable grid area
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=FluentColors.SURFACE_VARIANT,
        )
        self._scroll.pack(fill="both", expand=True, padx=8)

        # Grid container inside scroll
        self._grid = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._grid.pack(fill="both", expand=True)

        # Bind scroll to lazy loading
        self._scroll.bind("<Configure>", self._on_scroll_configure)

    def set_channels(self, channels):
        """Set the full channel list and refresh display."""
        self._all_channels = channels
        self._apply_filters()

    def set_search(self, text):
        """Update search filter."""
        self._search_text = text.lower().strip()
        self._apply_filters()

    def set_category(self, category):
        """Filter by category."""
        self._active_category = category
        self._header.configure(text=f"{'All Channels' if category == 'All' else category}")
        self._apply_filters()

    def set_hide_failed(self, hide):
        """Toggle hiding failed/unchecked channels."""
        self._hide_failed = hide
        self._apply_filters()

    def _apply_filters(self):
        """Apply all active filters and refresh the grid."""
        filtered = self._all_channels

        # Category filter
        if self._active_category and self._active_category != "All":
            filtered = [ch for ch in filtered
                        if ch.get('category', '') == self._active_category
                        or ch.get('country', '') == self._active_category]

        # Status filter
        if self._hide_failed:
            filtered = [ch for ch in filtered
                        if ch.get('status', 'unchecked') == 'working']

        # Search filter
        if self._search_text:
            search = self._search_text
            filtered = [ch for ch in filtered
                        if search in ch.get('name', '').lower()
                        or search in ch.get('category', '').lower()
                        or search in ch.get('country', '').lower()]

        self._filtered_channels = filtered
        self._count_label.configure(
            text=f"{len(filtered)} channels"
            + (f" (of {len(self._all_channels)})" if len(filtered) != len(self._all_channels) else "")
        )
        self._refresh_grid()

    def _refresh_grid(self):
        """Clear and rebuild the visible grid."""
        # Clear existing cards
        for card in self._visible_cards:
            card.destroy()
        self._visible_cards = []
        self._load_index = 0

        # Load first batch
        self._load_next_batch()

    def _load_next_batch(self):
        """Load the next batch of channel cards."""
        start = self._load_index
        end = min(start + BATCH_SIZE, len(self._filtered_channels))

        if start >= len(self._filtered_channels):
            return

        # Calculate columns based on grid width
        grid_width = self._grid.winfo_width()
        if grid_width < 100:
            grid_width = 900  # Default before first render
        cols = max(1, grid_width // (CardLayout.CARD_WIDTH + CardLayout.CARD_GAP))

        for i in range(start, end):
            ch = self._filtered_channels[i]
            row = i // cols
            col = i % cols

            is_fav = False
            if self._favorites_manager:
                is_fav = self._favorites_manager.is_favorite(ch.get('url', ''))

            card = ChannelCard(
                self._grid,
                channel=ch,
                is_favorite=is_fav,
                on_play=self._on_play,
                on_favorite_toggle=self._handle_favorite_toggle,
            )
            card.grid(row=row, column=col,
                      padx=CardLayout.CARD_GAP // 2,
                      pady=CardLayout.CARD_GAP // 2,
                      sticky="nsew")
            self._visible_cards.append(card)

        self._load_index = end

        # Configure grid columns for even spacing
        for c in range(cols):
            self._grid.grid_columnconfigure(c, weight=1)

    def _handle_favorite_toggle(self, channel):
        """Handle favorite toggle from a card."""
        if self._on_favorite_toggle:
            return self._on_favorite_toggle(channel)
        return False

    def _on_scroll_configure(self, event=None):
        """Load more cards when scrolled near bottom."""
        if self._load_index < len(self._filtered_channels):
            # Simple check: if we haven't loaded everything, load more
            self.after(100, self._load_next_batch)

    def get_visible_count(self):
        """Return count of visible cards."""
        return len(self._visible_cards)

    def get_filtered_count(self):
        """Return count of filtered channels."""
        return len(self._filtered_channels)
