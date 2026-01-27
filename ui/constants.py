"""Shared UI constants for TV Viewer - Windows 11 Fluent Design."""


class FluentColors:
    """Windows 11 Fluent Design color palette."""
    # Primary accent colors (Windows 11 default blue)
    ACCENT = "#0078D4"
    ACCENT_DARK = "#106EBE"
    ACCENT_LIGHT = "#60CDFF"
    
    # Background colors (Windows 11 dark theme)
    BG_SOLID = "#202020"          # Solid background
    BG_MICA = "#1F1F1F"           # Mica-like background  
    BG_ACRYLIC = "#2C2C2C"        # Acrylic-like elevated surface
    BG_CARD = "#2D2D2D"           # Card/container background
    BG_LAYER = "#383838"          # Layered element background
    
    # Surface colors
    SURFACE = "#2D2D2D"
    SURFACE_VARIANT = "#383838"   # Alias for backwards compatibility
    SURFACE_STROKE = "#3D3D3D"    # Border/divider color
    
    # Background aliases for backwards compatibility
    BG_DARK = "#202020"
    BG_ELEVATED = "#383838"
    
    # Primary color aliases for backwards compatibility
    PRIMARY = "#0078D4"
    PRIMARY_DARK = "#106EBE"
    PRIMARY_LIGHT = "#60CDFF"
    
    # Text colors (Windows 11 dark theme)
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#9D9D9D"
    TEXT_DISABLED = "#5C5C5C"     # Fixed contrast (was #6B6B6B)
    TEXT_ACCENT = "#60CDFF"
    
    # Status colors (Windows 11 style)
    SUCCESS = "#6CCB5F"           # Green
    ERROR = "#FF6B6B"             # Red (softer than Material)
    WARNING = "#FCE100"           # Yellow
    INFO = "#60CDFF"              # Light blue
    
    # Control colors
    CONTROL_DEFAULT = "#454545"   # Button default
    CONTROL_HOVER = "#505050"     # Button hover
    CONTROL_PRESSED = "#3A3A3A"   # Button pressed
    CONTROL_DISABLED = "#2D2D2D"  # Button disabled
    
    # Subtle colors for hover states
    SUBTLE_HOVER = "rgba(255, 255, 255, 0.08)"
    SUBTLE_PRESSED = "rgba(255, 255, 255, 0.04)"


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

