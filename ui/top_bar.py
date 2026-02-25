"""Top Bar widget — search, filters, settings for TV Viewer."""

import customtkinter as ctk
from ui.constants import (
    FluentColors, FluentTypography, FluentSpacing, TopBarLayout
)
from utils.logger import get_logger

logger = get_logger(__name__)


class TopBar(ctk.CTkFrame):
    """Top application bar with search, filters, and controls."""

    def __init__(self, parent, on_search=None, on_filter=None,
                 on_settings=None, on_theme_toggle=None, on_view_toggle=None):
        super().__init__(
            parent,
            height=TopBarLayout.HEIGHT,
            fg_color=FluentColors.BG_MICA,
            corner_radius=0,
        )
        self._on_search = on_search
        self._on_filter = on_filter
        self._on_settings = on_settings
        self._on_theme_toggle = on_theme_toggle
        self._on_view_toggle = on_view_toggle
        self._view_mode = "cards"  # "cards" or "table"

        self.pack_propagate(False)
        self._build()

    def _build(self):
        """Build top bar layout."""
        pad = 8

        # Search entry
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)
        self._search = ctk.CTkEntry(
            self,
            placeholder_text="🔍  Search channels...",
            textvariable=self._search_var,
            height=32,
            font=ctk.CTkFont(family=FluentTypography.FONT_FAMILY,
                             size=FluentTypography.BODY),
            border_color=FluentColors.CONTROL_BORDER,
            fg_color=FluentColors.BG_CARD,
        )
        self._search.pack(side="left", fill="x", expand=True, padx=pad, pady=pad)

        # Right-side buttons
        btn_kwargs = dict(
            width=TopBarLayout.BUTTON_SIZE,
            height=TopBarLayout.BUTTON_SIZE,
            fg_color="transparent",
            hover_color=FluentColors.BG_CARD_HOVER,
            text_color=FluentColors.TEXT_PRIMARY,
            corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
        )

        # View toggle (cards/table)
        self._view_btn = ctk.CTkButton(
            self, text="☷",
            font=ctk.CTkFont(size=18),
            command=self._toggle_view,
            **btn_kwargs,
        )
        self._view_btn.pack(side="right", padx=(0, pad))

        # Theme toggle
        if self._on_theme_toggle:
            self._theme_btn = ctk.CTkButton(
                self, text="🌙",
                font=ctk.CTkFont(size=16),
                command=self._on_theme_toggle,
                **btn_kwargs,
            )
            self._theme_btn.pack(side="right", padx=(0, 2))

        # Filter button
        self._filter_btn = ctk.CTkButton(
            self, text="☰ Filters",
            font=ctk.CTkFont(family=FluentTypography.FONT_FAMILY,
                             size=FluentTypography.BODY),
            width=90, height=TopBarLayout.BUTTON_SIZE,
            fg_color="transparent",
            hover_color=FluentColors.BG_CARD_HOVER,
            text_color=FluentColors.TEXT_PRIMARY,
            border_width=1,
            border_color=FluentColors.CONTROL_BORDER,
            corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
            command=self._on_filter,
        )
        self._filter_btn.pack(side="right", padx=(0, 4))

    def _on_search_change(self, *args):
        """Called when search text changes."""
        if self._on_search:
            self._on_search(self._search_var.get())

    def _toggle_view(self):
        """Toggle between card and table view."""
        self._view_mode = "table" if self._view_mode == "cards" else "cards"
        icon = "☰" if self._view_mode == "table" else "☷"
        self._view_btn.configure(text=icon)
        if self._on_view_toggle:
            self._on_view_toggle(self._view_mode)

    def get_search_text(self):
        """Return current search text."""
        return self._search_var.get()

    def clear_search(self):
        """Clear the search field."""
        self._search_var.set("")

    def get_view_mode(self):
        """Return current view mode ('cards' or 'table')."""
        return self._view_mode
