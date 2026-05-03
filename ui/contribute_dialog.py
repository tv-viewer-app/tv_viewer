"""Channel contribution dialog for crowdsourced channel sharing.

Allows users to submit new IPTV channels to the Supabase shared database.
Follows the same UI patterns as feedback_dialog.py and settings_dialog.py
(ttkbootstrap + plain tkinter, Fluent Design dark theme).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
import re

try:
    from ui.compat import ScrolledFrame
except ImportError:
    ScrolledFrame = None

from utils.logger import get_logger
from .constants import FluentColorsDark as FluentColors
import config

logger = get_logger(__name__)

# Valid URL pattern (must start with http:// or https://)
_URL_PATTERN = re.compile(r'^https?://.+')

# Categories for the dropdown
CONTRIBUTE_CATEGORIES = [
    "News", "Sports", "Entertainment", "Music", "Kids",
    "Documentary", "Movies", "Education", "Religious",
    "Weather", "General", "Other",
]


class ContributeDialog:
    """Dialog for contributing a new channel to the shared database."""

    def __init__(self, parent):
        """Initialize the contribute dialog.

        Args:
            parent: Parent tkinter window (root or Toplevel).
        """
        self.parent = parent
        self.dialog = None

    def show(self):
        """Create and display the dialog."""
        self.dialog = tk.Toplevel(self.parent)

        self.dialog.title("➕ Contribute Channel")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Size and centre on parent
        dw, dh = 500, 400
        self.dialog.update_idletasks()
        px = self.parent.winfo_rootx() + (self.parent.winfo_width() - dw) // 2
        py = self.parent.winfo_rooty() + (self.parent.winfo_height() - dh) // 2
        self.dialog.geometry(f"{dw}x{dh}+{max(0, px)}+{max(0, py)}")

        self._create_widgets()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self):
        """Build all dialog widgets."""
        C = FluentColors

        main = ttk.Frame(self.dialog, padding=20)
        main.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            main,
            text="➕ Add a Channel",
            font=("Segoe UI", 18, "bold"),
            foreground=C.ACCENT,
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            main,
            text="Share a working channel with the community",
            font=("Segoe UI", 10),
            foreground=C.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 14))

        # ── Form fields ──────────────────────────────────────────────
        form = ttk.Frame(main)
        form.pack(fill="x")
        form.grid_columnconfigure(1, weight=1)

        FONT = ("Segoe UI", 11)
        FONT_SMALL = ("Segoe UI", 10)
        row = 0

        # Channel Name (required)
        ttk.Label(form, text="Channel Name *", font=FONT).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 6))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(form, textvariable=self.name_var, font=FONT, width=36)
        name_entry.grid(row=row, column=1, sticky="ew", pady=(0, 6))
        name_entry.focus_set()
        row += 1

        # Stream URL (required)
        ttk.Label(form, text="Stream URL *", font=FONT).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 6))
        self.url_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.url_var, font=FONT, width=36).grid(
            row=row, column=1, sticky="ew", pady=(0, 6))
        row += 1

        # URL hint
        ttk.Label(
            form,
            text="Must start with http:// or https://",
            font=FONT_SMALL,
            foreground=C.TEXT_SECONDARY,
        ).grid(row=row, column=1, sticky="w", pady=(0, 8))
        row += 1

        # Category (dropdown)
        ttk.Label(form, text="Category", font=FONT).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 6))
        self.category_var = tk.StringVar(value="General")
        cat_combo = ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=CONTRIBUTE_CATEGORIES,
            state="readonly",
            font=FONT,
            width=20,
        )
        cat_combo.grid(row=row, column=1, sticky="w", pady=(0, 6))
        row += 1

        # Country (optional)
        ttk.Label(form, text="Country", font=FONT).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 6))
        self.country_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.country_var, font=FONT, width=36).grid(
            row=row, column=1, sticky="ew", pady=(0, 6))
        row += 1

        ttk.Label(
            form,
            text="Optional — e.g. US, UK, IL",
            font=FONT_SMALL,
            foreground=C.TEXT_SECONDARY,
        ).grid(row=row, column=1, sticky="w", pady=(0, 4))
        row += 1

        # ── Buttons ──────────────────────────────────────────────────
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(18, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            bootstyle="secondary",
            width=12,
        ).pack(side="right", padx=(6, 0))

        ttk.Button(
            btn_frame,
            text="➕ Add Channel",
            command=self._on_submit,
            bootstyle="success",
            width=14,
        ).pack(side="right")

        # Bind Enter to submit
        self.dialog.bind("<Return>", lambda e: self._on_submit())
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())

    # ------------------------------------------------------------------
    # Validation & submission
    # ------------------------------------------------------------------

    def _on_submit(self):
        """Validate inputs and submit the channel."""
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        category = self.category_var.get().strip() or "General"
        country = self.country_var.get().strip() or "Unknown"

        # --- Validation ---
        if not name:
            messagebox.showwarning(
                "Missing Name",
                "Please enter a channel name.",
                parent=self.dialog,
            )
            return

        if not url:
            messagebox.showwarning(
                "Missing URL",
                "Please enter a stream URL.",
                parent=self.dialog,
            )
            return

        if not _URL_PATTERN.match(url):
            messagebox.showwarning(
                "Invalid URL",
                "The stream URL must start with http:// or https://",
                parent=self.dialog,
            )
            return

        # Build channel dict matching supabase_channels.contribute_channels format
        channel = {
            "name": name,
            "url": url,
            "urls": [url],
            "category": category,
            "country": country,
        }

        # Disable the submit button to prevent double-clicks
        for widget in self.dialog.winfo_children():
            pass  # button is deep; just rely on grab_set

        # Run async contribution in a background thread
        self._submit_async(channel)

    def _submit_async(self, channel: dict):
        """Submit channel to Supabase in a background thread."""

        dialog_ref = self.dialog  # capture ref before thread runs

        def _run():
            contributed = 0
            error_msg = ""
            try:
                from utils.supabase_channels import contribute_channels, is_configured
                if not is_configured():
                    error_msg = (
                        "Channel sharing is not configured.\n"
                        "The channel could not be submitted at this time."
                    )
                else:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        contributed = loop.run_until_complete(
                            contribute_channels([channel], source="user-contributed")
                        )
                    finally:
                        loop.close()
            except Exception as exc:
                logger.warning(f"Channel contribution failed: {exc}")
                error_msg = (
                    "Could not submit the channel.\n"
                    "Please check your internet connection and try again."
                )

            # Schedule UI callback on the main thread
            try:
                dialog_ref.after(0, lambda: self._on_submit_done(contributed, error_msg))
            except Exception:
                pass  # dialog may have been closed

        threading.Thread(target=_run, daemon=True).start()

    def _on_submit_done(self, contributed: int, error_msg: str):
        """Handle the result of the async contribution (runs on main thread)."""
        if error_msg:
            messagebox.showerror("Submission Failed", error_msg, parent=self.dialog)
            return

        if contributed > 0:
            messagebox.showinfo(
                "Thank You! 🎉",
                f"Channel submitted successfully!\n\n"
                f"Your contribution helps the community.",
                parent=self.dialog,
            )
            logger.info(f"User contributed channel: {self.name_var.get()}")
            self.dialog.destroy()
        else:
            messagebox.showwarning(
                "Not Submitted",
                "The channel was not submitted.\n"
                "It may already exist in the database, or validation failed.",
                parent=self.dialog,
            )


def show_contribute_dialog(parent):
    """Show the channel contribution dialog.

    Args:
        parent: Parent tkinter window.
    """
    try:
        dlg = ContributeDialog(parent)
        dlg.show()
    except Exception as e:
        logger.error(f"Failed to open contribute dialog: {e}")
        messagebox.showerror(
            "Error",
            "Could not open the contribution dialog.\n"
            "Please try again later.",
        )
