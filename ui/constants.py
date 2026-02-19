"""Shared UI constants for TV Viewer - VLC-inspired Dark Theme."""


class FluentColors:
    """VLC-inspired dark color palette with orange accent."""
    # Primary accent colors (VLC orange)
    ACCENT = "#FF8800"
    ACCENT_DARK = "#E07700"
    ACCENT_LIGHT = "#FFB347"
    
    # Background colors (VLC dark theme)
    BG_SOLID = "#1E1E1E"          # Solid background
    BG_MICA = "#181818"           # Deepest background
    BG_ACRYLIC = "#252525"        # Elevated surface (sidebar, panels)
    BG_CARD = "#2D2D2D"           # Card/container background
    BG_LAYER = "#383838"          # Layered element background
    
    # Surface colors
    SURFACE = "#2D2D2D"
    SURFACE_VARIANT = "#3A3A3A"
    SURFACE_STROKE = "#484848"    # Border/divider color
    
    # Background aliases for backwards compatibility
    BG_DARK = "#1E1E1E"
    BG_ELEVATED = "#383838"
    
    # Primary color aliases for backwards compatibility
    PRIMARY = "#FF8800"
    PRIMARY_DARK = "#E07700"
    PRIMARY_LIGHT = "#FFB347"
    
    # Text colors (light on dark)
    TEXT_PRIMARY = "#F0F0F0"
    TEXT_SECONDARY = "#A0A0A0"
    TEXT_DISABLED = "#5C5C5C"
    TEXT_ACCENT = "#FFB347"
    
    # Status colors (vibrant on dark)
    SUCCESS = "#6CCB5F"           # Bright green
    ERROR = "#FF5555"             # Bright red
    WARNING = "#FFB347"           # Amber/orange
    INFO = "#60CDFF"              # Bright blue
    
    # Control colors (dark theme)
    CONTROL_DEFAULT = "#3A3A3A"
    CONTROL_HOVER = "#484848"
    CONTROL_PRESSED = "#2D2D2D"
    CONTROL_DISABLED = "#2D2D2D"
    
    # Border for controls
    CONTROL_BORDER = "#484848"
    CONTROL_BORDER_HOVER = "#FF8800"
    
    # Subtle colors for hover states
    SUBTLE_HOVER = "#3A3A3A"
    SUBTLE_PRESSED = "#484848"


# Alias for backwards compatibility
MaterialColors = FluentColors


class FluentTypography:
    """Windows 11 typography settings."""
    FONT_FAMILY = "Segoe UI Variable"
    FONT_FAMILY_FALLBACK = "Segoe UI"
    
    # Font sizes (Windows 11 type ramp)
    CAPTION = 12
    BODY = 14
    BODY_STRONG = 14
    SUBTITLE = 20
    TITLE = 28
    TITLE_LARGE = 40
    DISPLAY = 68


class FluentSpacing:
    """Windows 11 spacing constants."""
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
    
    # Corner radius (Windows 11 uses subtle rounding)
    CORNER_RADIUS_SMALL = 4
    CORNER_RADIUS_MEDIUM = 8
    CORNER_RADIUS_LARGE = 12


class FluentElevation:
    """Shadow/elevation levels for layering."""
    # Windows 11 uses subtle shadows
    LEVEL_0 = "none"
    LEVEL_1 = "0 2px 4px rgba(0, 0, 0, 0.14)"
    LEVEL_2 = "0 4px 8px rgba(0, 0, 0, 0.14)"
    LEVEL_3 = "0 8px 16px rgba(0, 0, 0, 0.14)"

