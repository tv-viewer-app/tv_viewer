"""
Tooltip utility for TV Viewer UI.

Provides tooltips for buttons and controls to improve discoverability.
"""

import tkinter as tk
from typing import Optional


class ToolTip:
    """
    Create a tooltip for a given widget.
    
    Usage:
        btn = ctk.CTkButton(...)
        ToolTip(btn, "Click to play/pause (Space)")
    """
    
    def __init__(self, widget, text: str, delay: int = 500):
        """
        Initialize tooltip.
        
        Args:
            widget: The widget to attach tooltip to
            text: Tooltip text to display
            delay: Delay in ms before showing tooltip
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None
        
        # Bind events
        self.widget.bind('<Enter>', self._on_enter)
        self.widget.bind('<Leave>', self._on_leave)
        self.widget.bind('<ButtonPress>', self._on_leave)
    
    def _on_enter(self, event=None):
        """Schedule tooltip to show."""
        self._cancel_scheduled()
        self._after_id = self.widget.after(self.delay, self._show_tooltip)
    
    def _on_leave(self, event=None):
        """Hide tooltip and cancel scheduled show."""
        self._cancel_scheduled()
        self._hide_tooltip()
    
    def _cancel_scheduled(self):
        """Cancel any scheduled tooltip show."""
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
    
    def _show_tooltip(self):
        """Show the tooltip."""
        if self.tooltip_window:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Style the tooltip - dark theme
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#2D2D2D",
            foreground="#FFFFFF",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=4
        )
        label.pack()
        
        # Auto-hide after 3 seconds
        self.widget.after(3000, self._hide_tooltip)
    
    def _hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def add_tooltip(widget, text: str, delay: int = 500) -> ToolTip:
    """
    Convenience function to add tooltip to a widget.
    
    Args:
        widget: Widget to add tooltip to
        text: Tooltip text
        delay: Delay before showing (ms)
    
    Returns:
        ToolTip instance
    """
    return ToolTip(widget, text, delay)
