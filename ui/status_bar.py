"""Status Bar widget for TV Viewer."""

import customtkinter as ctk
from ui.constants import (
    FluentColors, FluentTypography, StatusBarLayout
)


class StatusBar(ctk.CTkFrame):
    """Bottom status bar showing channel count, scan progress, and app version."""

    def __init__(self, parent, version=""):
        super().__init__(
            parent,
            height=StatusBarLayout.HEIGHT,
            fg_color=FluentColors.BG_MICA,
            corner_radius=0,
        )
        self.pack_propagate(False)
        self._build(version)

    def _build(self, version):
        font = ctk.CTkFont(family=FluentTypography.FONT_FAMILY,
                           size=FluentTypography.CAPTION)

        # Left: channel count
        self._status_label = ctk.CTkLabel(
            self, text="Loading channels...",
            font=font, text_color=FluentColors.TEXT_SECONDARY,
            anchor="w",
        )
        self._status_label.pack(side="left", padx=12)

        # Right: version
        ctk.CTkLabel(
            self, text=f"v{version}" if version else "",
            font=font, text_color=FluentColors.TEXT_DISABLED,
            anchor="e",
        ).pack(side="right", padx=12)

        # Center: scan progress (hidden by default)
        self._progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._progress_label = ctk.CTkLabel(
            self._progress_frame, text="",
            font=font, text_color=FluentColors.TEXT_SECONDARY,
        )
        self._progress_label.pack(side="left", padx=(0, 8))
        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame, width=120, height=4,
            fg_color=FluentColors.SURFACE_VARIANT,
            progress_color=FluentColors.ACCENT,
        )
        self._progress_bar.pack(side="left")
        self._progress_bar.set(0)

    def set_channel_count(self, working, total):
        """Update channel count display."""
        self._status_label.configure(
            text=f"✓ {working:,} working channels" +
                 (f" of {total:,}" if total != working else "")
        )

    def show_scan_progress(self, current, total, working=0):
        """Show scan progress."""
        self._progress_frame.pack(side="left", padx=20)
        pct = current / total if total > 0 else 0
        self._progress_bar.set(pct)
        self._progress_label.configure(
            text=f"Scanning {current:,}/{total:,} ({int(pct * 100)}%)"
        )

    def hide_scan_progress(self):
        """Hide scan progress bar."""
        self._progress_frame.pack_forget()

    def set_status(self, text):
        """Set custom status text."""
        self._status_label.configure(text=text)
