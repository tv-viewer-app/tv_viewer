"""First-launch privacy / consent modal (Issue #170).

Three opt-in checkboxes (all default OFF):
    [ ] Share anonymous usage stats
    [ ] Use online channel database
    [ ] Allow geo-IP to find local channels

Saves to ``~/.tv_viewer/consent.json`` via :mod:`utils.consent`.

The dialog blocks until the user clicks Accept or Decline All.
"""
from __future__ import annotations

import tkinter as tk
import webbrowser
from typing import Dict, Optional

from utils.consent import load_consent, save_consent, apply_to_config

_BG = "#15171c"
_FG = "#e6e6e6"
_FG_MUTED = "#9aa0a6"
_ACCENT = "#4da6ff"
_BG_CARD = "#1f222a"
_BORDER = "#2a2d35"

PRIVACY_URL = "https://tv-viewer.app/privacy"

_OPTIONS = [
    ("analytics",
     "Share anonymous usage stats",
     "App version, feature usage, error reports. No channel names or URLs."),
    ("online_db",
     "Use online channel database",
     "Faster updates and contributes new channels you find back to everyone."),
    ("geo_ip",
     "Allow geo-IP for local channels",
     "Pins a 'Local (Country)' row at the top of Home using your public IP."),
]

_INFO_BANNER = (
    "Crowdsourced channel data is community-powered. If you turn analytics "
    "and online DB OFF, you won't receive database updates, new channels, or "
    "channel status updates from the community.\n\n"
    "You can change this any time in Settings → Privacy."
)


def show_privacy_dialog(root: tk.Tk) -> Dict[str, bool]:
    """Modal first-launch consent dialog. Returns chosen values."""
    initial = load_consent()
    vars_: Dict[str, tk.BooleanVar] = {
        key: tk.BooleanVar(root, value=bool(initial.get(key, False)))
        for key, _, _ in _OPTIONS
    }
    result: Dict[str, bool] = {key: False for key, _, _ in _OPTIONS}

    win = tk.Toplevel(root)
    win.title("Privacy & Data")
    win.configure(bg=_BG)
    win.transient(root)
    win.resizable(False, False)
    try:
        win.grab_set()
    except Exception:
        pass

    # Center on screen
    win.update_idletasks()
    w, h = 560, 560
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    tk.Label(
        win, text="Privacy & Data", bg=_BG, fg=_FG,
        font=("Segoe UI", 18, "bold"),
    ).pack(pady=(20, 4))
    tk.Label(
        win,
        text="Choose what data TV Viewer may use. All options are off by default.",
        bg=_BG, fg=_FG_MUTED, font=("Segoe UI", 10), wraplength=500, justify="center",
    ).pack(pady=(0, 12))

    # Info banner about the trade-off
    banner = tk.Frame(win, bg="#1a2332", highlightbackground=_ACCENT,
                      highlightthickness=1)
    banner.pack(fill=tk.X, padx=20, pady=(0, 12))
    tk.Label(
        banner, text=_INFO_BANNER, bg="#1a2332", fg=_FG,
        font=("Segoe UI", 9), wraplength=480, justify="left",
        padx=12, pady=10,
    ).pack(fill=tk.X)

    body = tk.Frame(win, bg=_BG)
    body.pack(fill=tk.BOTH, expand=True, padx=20)

    for key, label, hint in _OPTIONS:
        row = tk.Frame(body, bg=_BG_CARD, highlightbackground=_BORDER,
                       highlightthickness=1)
        row.pack(fill=tk.X, pady=4)
        cb = tk.Checkbutton(
            row, text=label, variable=vars_[key],
            bg=_BG_CARD, fg=_FG, selectcolor=_BG_CARD,
            activebackground=_BG_CARD, activeforeground=_FG,
            font=("Segoe UI", 11, "bold"), anchor="w",
            padx=12, pady=8,
        )
        cb.pack(fill=tk.X, anchor="w")
        tk.Label(
            row, text=hint, bg=_BG_CARD, fg=_FG_MUTED,
            font=("Segoe UI", 9), wraplength=480, justify="left", anchor="w",
            padx=40,
        ).pack(fill=tk.X, anchor="w", pady=(0, 8))

    # Privacy policy link
    link = tk.Label(
        win, text="Read the privacy policy ↗", bg=_BG, fg=_ACCENT,
        font=("Segoe UI", 9, "underline"), cursor="hand2",
    )
    link.pack(pady=(8, 0))
    link.bind("<Button-1>", lambda e: webbrowser.open(PRIVACY_URL))

    # Single Save button
    btns = tk.Frame(win, bg=_BG)
    btns.pack(pady=14)

    def _save():
        nonlocal result
        result = {k: bool(v.get()) for k, v in vars_.items()}
        save_consent(result)
        apply_to_config(result)
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    tk.Button(
        btns, text="Save",
        command=_save,
        bg=_ACCENT, fg="#0b1220", activebackground="#3893e6", activeforeground="#0b1220",
        font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=42, pady=10,
        bd=0, highlightthickness=0, cursor="hand2",
    ).pack()

    # Closing the window via X = save current selections (whatever they are)
    win.protocol("WM_DELETE_WINDOW", _save)
    win.wait_window()
    return result


def maybe_show_privacy_dialog(root: tk.Tk) -> Optional[Dict[str, bool]]:
    """Show dialog only if needed; otherwise apply stored consent silently.

    NOTE: We do NOT call ``apply_to_config`` when the user has not yet
    answered the dialog — that would clobber any ``TELEMETRY_ENABLED=true``
    environment variable set at import time in ``config.py``.  Defaults
    only get pushed into config once the user has explicitly answered.
    """
    from utils.consent import needs_prompt
    if needs_prompt():
        return show_privacy_dialog(root)
    stored = load_consent()
    apply_to_config(stored)
    return stored
