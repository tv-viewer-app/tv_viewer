"""Shared UI constants for TV Viewer - Windows 11 Fluent Design (Light Theme)."""


class FluentColors:
    """Windows 11 Fluent Design LIGHT color palette."""
    # Primary accent colors (Windows 11 default blue)
    ACCENT = "#0078D4"
    ACCENT_DARK = "#106EBE"
    ACCENT_LIGHT = "#60CDFF"
    
    # Background colors (Windows 11 LIGHT theme)
    BG_SOLID = "#F3F3F3"          # Solid background (was #202020)
    BG_MICA = "#F9F9F9"           # Mica-like background (was #1F1F1F)
    BG_ACRYLIC = "#FCFCFC"        # Acrylic-like elevated surface (was #2C2C2C)
    BG_CARD = "#FFFFFF"           # Card/container background (was #2D2D2D)
    BG_LAYER = "#F5F5F5"          # Layered element background (was #383838)
    
    # Surface colors
    SURFACE = "#FFFFFF"           # (was #2D2D2D)
    SURFACE_VARIANT = "#E8E8E8"   # (was #383838)
    SURFACE_STROKE = "#E0E0E0"    # Border/divider color (was #3D3D3D)
    
    # Background aliases for backwards compatibility
    BG_DARK = "#F3F3F3"           # (was #202020)
    BG_ELEVATED = "#FFFFFF"       # (was #383838)
    
    # Primary color aliases for backwards compatibility
    PRIMARY = "#0078D4"
    PRIMARY_DARK = "#106EBE"
    PRIMARY_LIGHT = "#60CDFF"
    
    # Text colors (Windows 11 LIGHT theme)
    TEXT_PRIMARY = "#1A1A1A"      # Dark text (was #FFFFFF)
    TEXT_SECONDARY = "#5C5C5C"    # Gray text (was #9D9D9D)
    TEXT_DISABLED = "#A0A0A0"     # Disabled text (was #5C5C5C)
    TEXT_ACCENT = "#0078D4"       # Accent text (was #60CDFF)
    
    # Status colors (Windows 11 style - slightly darker for light bg)
    SUCCESS = "#107C10"           # Green (was #6CCB5F)
    ERROR = "#C42B1C"             # Red (was #FF6B6B)
    WARNING = "#9D5D00"           # Orange/amber (was #FCE100)
    INFO = "#0078D4"              # Blue (was #60CDFF)
    
    # Control colors (light theme)
    CONTROL_DEFAULT = "#FFFFFF"   # Button default (was #454545)
    CONTROL_HOVER = "#F5F5F5"     # Button hover (was #505050)
    CONTROL_PRESSED = "#E8E8E8"   # Button pressed (was #3A3A3A)
    CONTROL_DISABLED = "#F0F0F0"  # Button disabled (was #2D2D2D)
    
    # Border for controls (needed in light theme)
    CONTROL_BORDER = "#D1D1D1"
    CONTROL_BORDER_HOVER = "#0078D4"
    
    # Subtle colors for hover states
    SUBTLE_HOVER = "rgba(0, 0, 0, 0.04)"
    SUBTLE_PRESSED = "rgba(0, 0, 0, 0.08)"


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
