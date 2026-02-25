"""Channel Card widget for TV Viewer — visual channel display."""

import customtkinter as ctk
from ui.constants import (
    FluentColors, FluentTypography, FluentSpacing, CardLayout
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ChannelCard(ctk.CTkFrame):
    """Visual card representing a single TV channel."""

    def __init__(self, parent, channel, is_favorite=False,
                 on_play=None, on_favorite_toggle=None, on_right_click=None):
        super().__init__(
            parent,
            width=CardLayout.CARD_WIDTH,
            height=CardLayout.CARD_HEIGHT,
            fg_color=FluentColors.BG_CARD,
            corner_radius=CardLayout.CARD_CORNER_RADIUS,
            border_width=1,
            border_color=FluentColors.SURFACE_STROKE,
        )
        self._channel = channel
        self._is_favorite = is_favorite
        self._on_play = on_play
        self._on_favorite_toggle = on_favorite_toggle

        self.pack_propagate(False)
        self._build()

        # Bind interactions
        self.bind("<Button-1>", self._on_click)
        self.bind("<Double-Button-1>", self._on_double_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        if on_right_click:
            self.bind("<Button-3>", lambda e: on_right_click(channel, e))

    def _build(self):
        """Build card layout."""
        pad = CardLayout.CARD_PADDING
        name = self._channel.get('name', 'Unknown')
        category = self._channel.get('category', '')
        country = self._channel.get('country', '')
        status = self._channel.get('status', 'unchecked')

        # Top section: logo placeholder + status badge
        top = ctk.CTkFrame(self, fg_color="transparent", height=CardLayout.LOGO_SIZE + 8)
        top.pack(fill="x", padx=pad, pady=(pad, 4))
        top.pack_propagate(False)

        # Logo placeholder (colored circle with first letter)
        logo_text = name[0].upper() if name else "?"
        self._logo = ctk.CTkLabel(
            top, text=logo_text,
            width=CardLayout.LOGO_SIZE, height=CardLayout.LOGO_SIZE,
            fg_color=FluentColors.ACCENT,
            text_color="#FFFFFF",
            corner_radius=CardLayout.LOGO_SIZE // 2,
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self._logo.pack(side="left")

        # Status badge + favorite star
        badge_frame = ctk.CTkFrame(top, fg_color="transparent")
        badge_frame.pack(side="right", fill="y")

        if status == 'working':
            ctk.CTkLabel(
                badge_frame, text="🟢", font=ctk.CTkFont(size=10),
                text_color=FluentColors.LIVE_BADGE,
            ).pack(anchor="ne")

        # Favorite star button
        star = "★" if self._is_favorite else "☆"
        self._star_btn = ctk.CTkLabel(
            badge_frame, text=star,
            font=ctk.CTkFont(size=16),
            text_color=FluentColors.FAVORITE_STAR if self._is_favorite else FluentColors.TEXT_DISABLED,
            cursor="hand2",
        )
        self._star_btn.pack(anchor="ne", pady=(2, 0))
        self._star_btn.bind("<Button-1>", self._toggle_favorite)

        # Channel name
        self._name_label = ctk.CTkLabel(
            self, text=name,
            font=ctk.CTkFont(
                family=FluentTypography.FONT_FAMILY,
                size=13, weight="bold"
            ),
            text_color=FluentColors.TEXT_PRIMARY,
            anchor="w", wraplength=CardLayout.CARD_WIDTH - 2 * pad,
        )
        self._name_label.pack(fill="x", padx=pad)
        self._name_label.bind("<Button-1>", self._on_click)
        self._name_label.bind("<Double-Button-1>", self._on_double_click)

        # Subtitle: category + country
        subtitle_parts = []
        if category:
            subtitle_parts.append(category)
        if country:
            subtitle_parts.append(country)
        subtitle = " • ".join(subtitle_parts) if subtitle_parts else ""

        self._subtitle_label = ctk.CTkLabel(
            self, text=subtitle,
            font=ctk.CTkFont(
                family=FluentTypography.FONT_FAMILY,
                size=11
            ),
            text_color=FluentColors.TEXT_SECONDARY,
            anchor="w",
        )
        self._subtitle_label.pack(fill="x", padx=pad, pady=(0, pad))
        self._subtitle_label.bind("<Button-1>", self._on_click)
        self._subtitle_label.bind("<Double-Button-1>", self._on_double_click)

    def _on_click(self, event=None):
        """Single click — select."""
        pass  # Visual feedback handled by enter/leave

    def _on_double_click(self, event=None):
        """Double click — play."""
        if self._on_play:
            self._on_play(self._channel)

    def _on_enter(self, event=None):
        self.configure(
            fg_color=FluentColors.BG_CARD_HOVER,
            border_color=FluentColors.ACCENT,
        )

    def _on_leave(self, event=None):
        self.configure(
            fg_color=FluentColors.BG_CARD,
            border_color=FluentColors.SURFACE_STROKE,
        )

    def _toggle_favorite(self, event=None):
        if self._on_favorite_toggle:
            self._is_favorite = self._on_favorite_toggle(self._channel)
            star = "★" if self._is_favorite else "☆"
            color = FluentColors.FAVORITE_STAR if self._is_favorite else FluentColors.TEXT_DISABLED
            self._star_btn.configure(text=star, text_color=color)
        if event:
            return "break"  # Prevent propagation to card click

    def get_channel(self):
        """Return the channel dict."""
        return self._channel
