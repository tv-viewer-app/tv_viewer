"""Navigation Rail widget — collapsible sidebar for TV Viewer."""

import customtkinter as ctk
from ui.constants import (
    FluentColors, FluentTypography, FluentSpacing, NavRailLayout
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Category icons mapping
CATEGORY_ICONS = {
    'Favorites': '★',
    'Recent': '🕐',
    'All': '📺',
    'News': '📰',
    'Sports': '⚽',
    'Entertainment': '🎬',
    'Music': '🎵',
    'Kids': '🧸',
    'Movies': '🎥',
    'Documentary': '🔬',
    'Religious': '🕊',
    'Education': '📚',
    'Lifestyle': '🏠',
    'Radio': '📻',
    'Countries': '🌍',
    'Settings': '⚙',
}


class NavRailItem(ctk.CTkFrame):
    """Single navigation rail item (icon + optional label)."""

    def __init__(self, parent, icon, label, command=None, is_active=False, expanded=False):
        super().__init__(parent, fg_color="transparent", cursor="hand2")
        self._command = command
        self._label_text = label
        self._is_active = is_active

        height = NavRailLayout.ITEM_HEIGHT
        self.configure(height=height)

        # Icon label
        self._icon_label = ctk.CTkLabel(
            self, text=icon, width=NavRailLayout.WIDTH_COLLAPSED,
            height=height,
            font=ctk.CTkFont(size=NavRailLayout.ICON_SIZE),
            text_color=FluentColors.ACCENT if is_active else FluentColors.TEXT_PRIMARY,
        )
        self._icon_label.pack(side="left")

        # Text label (shown when expanded)
        self._text_label = ctk.CTkLabel(
            self, text=label, height=height,
            font=ctk.CTkFont(
                family=FluentTypography.FONT_FAMILY,
                size=FluentTypography.BODY,
                weight="bold" if is_active else "normal"
            ),
            text_color=FluentColors.ACCENT if is_active else FluentColors.TEXT_PRIMARY,
            anchor="w",
        )
        if expanded:
            self._text_label.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Bind click to entire frame
        for widget in [self, self._icon_label, self._text_label]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, event=None):
        if self._command:
            self._command()

    def _on_enter(self, event=None):
        self.configure(fg_color=FluentColors.BG_CARD_HOVER)

    def _on_leave(self, event=None):
        self.configure(fg_color="transparent")

    def set_active(self, active):
        self._is_active = active
        color = FluentColors.ACCENT if active else FluentColors.TEXT_PRIMARY
        weight = "bold" if active else "normal"
        self._icon_label.configure(text_color=color)
        self._text_label.configure(
            text_color=color,
            font=ctk.CTkFont(family=FluentTypography.FONT_FAMILY,
                             size=FluentTypography.BODY, weight=weight)
        )

    def set_expanded(self, expanded):
        if expanded:
            self._text_label.pack(side="left", fill="x", expand=True, padx=(0, 8))
        else:
            self._text_label.pack_forget()


class NavigationRail(ctk.CTkFrame):
    """Collapsible navigation rail (56px collapsed, 200px expanded)."""

    def __init__(self, parent, on_category_select=None, on_favorites_select=None,
                 on_recent_select=None, on_settings=None):
        super().__init__(
            parent,
            fg_color=FluentColors.BG_NAV_RAIL,
            width=NavRailLayout.WIDTH_COLLAPSED,
            corner_radius=0,
        )
        self._expanded = False
        self._on_category_select = on_category_select
        self._on_favorites_select = on_favorites_select
        self._on_recent_select = on_recent_select
        self._on_settings = on_settings
        self._items = {}
        self._active_item = None

        self.pack_propagate(False)
        self._build()

    def _build(self):
        """Build navigation items."""
        # Hamburger toggle
        self._toggle_btn = ctk.CTkButton(
            self, text="☰", width=NavRailLayout.WIDTH_COLLAPSED,
            height=NavRailLayout.ITEM_HEIGHT,
            fg_color="transparent", hover_color=FluentColors.BG_CARD_HOVER,
            text_color=FluentColors.TEXT_PRIMARY,
            font=ctk.CTkFont(size=20),
            command=self.toggle_expanded,
        )
        self._toggle_btn.pack(pady=(4, 8))

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=FluentColors.SURFACE_STROKE).pack(
            fill="x", padx=8, pady=4)

        # Fixed nav items
        self._add_item('Favorites', '★', self._on_favorites_select)
        self._add_item('Recent', '🕐', self._on_recent_select)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=FluentColors.SURFACE_STROKE).pack(
            fill="x", padx=8, pady=4)

        self._add_item('All', '📺', lambda: self._select_category('All'))

        # Scrollable category area
        self._category_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=FluentColors.SURFACE_VARIANT,
        )
        self._category_frame.pack(fill="both", expand=True, pady=4)

        # Bottom settings
        spacer = ctk.CTkFrame(self, fg_color="transparent", height=4)
        spacer.pack()
        ctk.CTkFrame(self, height=1, fg_color=FluentColors.SURFACE_STROKE).pack(
            fill="x", padx=8, pady=4)
        self._add_item('Settings', '⚙', self._on_settings)

    def _add_item(self, name, icon, command):
        """Add a navigation item."""
        item = NavRailItem(
            self if name not in ('Settings',) else self,
            icon=icon, label=name, command=command,
            expanded=self._expanded,
        )
        item.pack(fill="x")
        self._items[name] = item

    def _select_category(self, category):
        """Handle category selection."""
        # Update active state
        if self._active_item and self._active_item in self._items:
            self._items[self._active_item].set_active(False)
        self._active_item = category
        if category in self._items:
            self._items[category].set_active(True)
        if self._on_category_select:
            self._on_category_select(category)

    def set_categories(self, categories):
        """Update the category list with channel categories."""
        # Remove old category entries from _items (keep fixed items)
        fixed_items = {'Favorites', 'Recent', 'All', 'Settings'}
        stale_keys = [k for k in self._items if k not in fixed_items]
        for k in stale_keys:
            del self._items[k]

        # Clear existing category widgets
        for widget in self._category_frame.winfo_children():
            widget.destroy()

        for cat_name in sorted(categories):
            icon = CATEGORY_ICONS.get(cat_name, '📁')
            item = NavRailItem(
                self._category_frame,
                icon=icon, label=cat_name,
                command=lambda c=cat_name: self._select_category(c),
                expanded=self._expanded,
            )
            item.pack(fill="x")
            self._items[cat_name] = item

    def toggle_expanded(self):
        """Toggle between collapsed and expanded state."""
        self._expanded = not self._expanded
        width = NavRailLayout.WIDTH_EXPANDED if self._expanded else NavRailLayout.WIDTH_COLLAPSED
        self.configure(width=width)

        for item in self._items.values():
            item.set_expanded(self._expanded)

    def set_expanded(self, expanded):
        """Set expanded state directly."""
        if self._expanded != expanded:
            self.toggle_expanded()

    def set_active(self, name):
        """Set active navigation item."""
        if self._active_item and self._active_item in self._items:
            self._items[self._active_item].set_active(False)
        self._active_item = name
        if name in self._items:
            self._items[name].set_active(True)
