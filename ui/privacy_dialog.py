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
    w, h = 540, 460
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    tk.Label(
        win, text="Welcome to TV Viewer", bg=_BG, fg=_FG,
        font=("Segoe UI", 18, "bold"),
    ).pack(pady=(20, 4))
    tk.Label(
        win,
        text="Choose what data TV Viewer may use. All options are off by default.",
        bg=_BG, fg=_FG_MUTED, font=("Segoe UI", 10), wraplength=480, justify="center",
    ).pack(pady=(0, 16))

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
            font=("Segoe UI", 9), wraplength=460, justify="left", anchor="w",
            padx=40, pady=(0, 8),
        ).pack(fill=tk.X, anchor="w")

    # Privacy policy link
    link = tk.Label(
        win, text="Read the privacy policy ↗", bg=_BG, fg=_ACCENT,
        font=("Segoe UI", 9, "underline"), cursor="hand2",
    )
    link.pack(pady=(8, 0))
    link.bind("<Button-1>", lambda e: webbrowser.open(PRIVACY_URL))

    # Buttons
    btns = tk.Frame(win, bg=_BG)
    btns.pack(pady=16)

    def _finish(accept: bool):
        nonlocal result
        if accept:
            result = {k: bool(v.get()) for k, v in vars_.items()}
        else:
            result = {k: False for k in vars_}
        save_consent(result)
        apply_to_config(result)
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    tk.Button(
        btns, text="Decline all",
        command=lambda: _finish(False),
        bg=_BG_CARD, fg=_FG_MUTED, activebackground=_BORDER, activeforeground=_FG,
        font=("Segoe UI", 10), relief=tk.FLAT, padx=18, pady=8,
        bd=0, highlightthickness=0, cursor="hand2",
    ).pack(side=tk.LEFT, padx=8)
    tk.Button(
        btns, text="Accept selected",
        command=lambda: _finish(True),
        bg=_ACCENT, fg="#0b1220", activebackground="#3893e6", activeforeground="#0b1220",
        font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=18, pady=8,
        bd=0, highlightthickness=0, cursor="hand2",
    ).pack(side=tk.LEFT, padx=8)

    win.protocol("WM_DELETE_WINDOW", lambda: _finish(False))
    win.wait_window()
    return result


def maybe_show_privacy_dialog(root: tk.Tk) -> Optional[Dict[str, bool]]:
    """Show dialog only if needed; otherwise apply stored consent silently."""
    from utils.consent import needs_prompt
    stored = load_consent()
    apply_to_config(stored)
    if needs_prompt():
        return show_privacy_dialog(root)
    return stored
