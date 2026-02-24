"""Shared UI constants for TV Viewer - Fluent Design with Ubuntu/GNOME support."""

import platform


class FluentColors:
    """Fluent Design color palette with light and dark theme support."""
    # Primary accent colors
    ACCENT = "#0078D4"
    ACCENT_DARK = "#106EBE"
    ACCENT_LIGHT = "#60CDFF"
    
    # Background colors (Light theme)
    BG_SOLID = "#F3F3F3"
    BG_MICA = "#F9F9F9"
    BG_ACRYLIC = "#FCFCFC"
    BG_CARD = "#FFFFFF"
    BG_LAYER = "#F5F5F5"
    
    # Surface colors
    SURFACE = "#FFFFFF"
    SURFACE_VARIANT = "#E8E8E8"
    SURFACE_STROKE = "#E0E0E0"
    
    # Background aliases for backwards compatibility
    BG_DARK = "#F3F3F3"
    BG_ELEVATED = "#FFFFFF"
    
    # Primary color aliases for backwards compatibility
    PRIMARY = "#0078D4"
    PRIMARY_DARK = "#106EBE"
    PRIMARY_LIGHT = "#60CDFF"
    
    # Text colors (Light theme)
    TEXT_PRIMARY = "#1A1A1A"
    TEXT_SECONDARY = "#5C5C5C"
    TEXT_DISABLED = "#A0A0A0"
    TEXT_ACCENT = "#0078D4"
    
    # Status colors
    SUCCESS = "#107C10"
    ERROR = "#C42B1C"
    WARNING = "#9D5D00"
    INFO = "#0078D4"
    
    # Control colors (light theme)
    CONTROL_DEFAULT = "#FFFFFF"
    CONTROL_HOVER = "#F5F5F5"
    CONTROL_PRESSED = "#E8E8E8"
    CONTROL_DISABLED = "#F0F0F0"
    
    # Border for controls
    CONTROL_BORDER = "#D1D1D1"
    CONTROL_BORDER_HOVER = "#0078D4"
    
    # Subtle colors for hover states
    SUBTLE_HOVER = "rgba(0, 0, 0, 0.04)"
    SUBTLE_PRESSED = "rgba(0, 0, 0, 0.08)"

    # --- New: Card and Nav Rail colors ---
    BG_CARD_HOVER = "#F0F0F0"
    BG_NAV_RAIL = "#EBEBEB"
    LIVE_BADGE = "#107C10"
    FAVORITE_STAR = "#FFB900"


class FluentColorsDark:
    """Dark theme palette — mirrors FluentColors structure."""
    ACCENT = "#4CC2FF"
    ACCENT_DARK = "#0078D4"
    ACCENT_LIGHT = "#60CDFF"

    BG_SOLID = "#1E1E1E"
    BG_MICA = "#1F1F1F"
    BG_ACRYLIC = "#2C2C2C"
    BG_CARD = "#2D2D2D"
    BG_LAYER = "#383838"

    SURFACE = "#2D2D2D"
    SURFACE_VARIANT = "#383838"
    SURFACE_STROKE = "#3D3D3D"

    BG_DARK = "#1E1E1E"
    BG_ELEVATED = "#383838"
    PRIMARY = "#4CC2FF"
    PRIMARY_DARK = "#0078D4"
    PRIMARY_LIGHT = "#60CDFF"

    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#9D9D9D"
    TEXT_DISABLED = "#5C5C5C"
    TEXT_ACCENT = "#60CDFF"

    SUCCESS = "#6CCB5F"
    ERROR = "#FF6B6B"
    WARNING = "#FCE100"
    INFO = "#60CDFF"

    CONTROL_DEFAULT = "#454545"
    CONTROL_HOVER = "#505050"
    CONTROL_PRESSED = "#3A3A3A"
    CONTROL_DISABLED = "#2D2D2D"
    CONTROL_BORDER = "#3D3D3D"
    CONTROL_BORDER_HOVER = "#60CDFF"

    SUBTLE_HOVER = "rgba(255, 255, 255, 0.06)"
    SUBTLE_PRESSED = "rgba(255, 255, 255, 0.09)"

    BG_CARD_HOVER = "#383838"
    BG_NAV_RAIL = "#252525"
    LIVE_BADGE = "#6CCB5F"
    FAVORITE_STAR = "#FFB900"


# Alias for backwards compatibility
MaterialColors = FluentColors


def _detect_font():
    """Return best font family for current platform."""
    if platform.system() == "Windows":
        return "Segoe UI Variable", "Segoe UI"
    else:
        return "Ubuntu", "Cantarell"


class FluentTypography:
    """Typography settings with platform-appropriate fonts."""
    FONT_FAMILY, FONT_FAMILY_FALLBACK = _detect_font()
    
    # Font sizes (type ramp)
    CAPTION = 12
    BODY = 14
    BODY_STRONG = 14
    SUBTITLE = 20
    TITLE = 28
    TITLE_LARGE = 40
    DISPLAY = 68


class FluentSpacing:
    """Spacing constants."""
    # Padding
    PADDING_SMALL = 4
    PADDING_MEDIUM = 8
    PADDING_LARGE = 12
    PADDING_XLARGE = 16
    
    # Margins
    MARGIN_SMALL = 4
    MARGIN_MEDIUM = 8
    MARGIN_LARGE = 16
    MARGIN_XLARGE = 24
    
    # Corner radius
    CORNER_RADIUS_SMALL = 4
    CORNER_RADIUS_MEDIUM = 8
    CORNER_RADIUS_LARGE = 12


class FluentElevation:
    """Shadow/elevation levels for layering."""
    LEVEL_0 = "none"
    LEVEL_1 = "0 2px 4px rgba(0, 0, 0, 0.14)"
    LEVEL_2 = "0 4px 8px rgba(0, 0, 0, 0.14)"
    LEVEL_3 = "0 8px 16px rgba(0, 0, 0, 0.14)"


class CardLayout:
    """Channel card and grid dimensions."""
    CARD_WIDTH = 180
    CARD_HEIGHT = 140
    CARD_GAP = 8
    CARD_PADDING = 12
    LOGO_SIZE = 64
    CARD_CORNER_RADIUS = 8

    # Responsive card widths
    CARD_WIDTH_COMPACT = 160
    CARD_WIDTH_WIDE = 220


class NavRailLayout:
    """Navigation rail dimensions."""
    WIDTH_COLLAPSED = 56
    WIDTH_EXPANDED = 200
    ITEM_HEIGHT = 40
    ICON_SIZE = 20
    AUTO_EXPAND_BREAKPOINT = 1800


class TopBarLayout:
    """Top bar dimensions."""
    HEIGHT = 48
    SEARCH_MIN_WIDTH = 200
    BUTTON_SIZE = 36


class StatusBarLayout:
    """Status bar dimensions."""
    HEIGHT = 24


class WindowLayout:
    """Main window dimensions and breakpoints."""
    MIN_WIDTH = 960
    MIN_HEIGHT = 540
    DEFAULT_WIDTH = 1200
    DEFAULT_HEIGHT = 700
    
    # Responsive breakpoints
    BREAKPOINT_COMPACT = 1100
    BREAKPOINT_STANDARD = 1600
    BREAKPOINT_WIDE = 1800


