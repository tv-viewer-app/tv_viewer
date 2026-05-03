"""First-run interactive tooltip tour (Issue #162).

Displays a sequence of coachmark cards explaining TV-mode key bindings.
Marks ``ui_tour_shown=True`` in ``~/.tv_viewer/ui_state.json`` so the
tour only runs once.  Available again from the Help menu via
:func:`show_tour`.
"""
from __future__ import annotations

import json
import os
import tkinter as tk
from typing import List, Tuple

_BG = "#15171c"
_FG = "#e6e6e6"
_FG_MUTED = "#9aa0a6"
_ACCENT = "#4da6ff"
_BG_CARD = "#1f222a"
_BORDER = "#2a2d35"

_STEPS: List[Tuple[str, str]] = [
    ("Navigate", "Use ↑ ↓ to switch rows, ← → inside a row.\nEnter plays the focused channel."),
    ("Search", "Press / or Ctrl+F to search by name."),
    ("Quick jump", "Type a channel number (0-9) to jump to it instantly."),
    ("Submit", "Found a channel that's missing? Press A or click 📡 Submit."),
    ("Filter", "Click 🔎 Filter to narrow channels by language, country or category."),
    ("Map", "Click 🗺 Map to browse channels by location."),
    ("Fullscreen", "F11 toggles fullscreen. Esc exits playback or fullscreen."),
]


def _ui_state_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".tv_viewer")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "ui_state.json")


def _load_state() -> dict:
    path = _ui_state_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(data: dict) -> None:
    try:
        with open(_ui_state_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def tour_already_shown() -> bool:
    return bool(_load_state().get("ui_tour_shown"))


def mark_tour_shown() -> None:
    data = _load_state()
    data["ui_tour_shown"] = True
    _save_state(data)


def show_tour(root: tk.Tk) -> None:
    """Show the coachmark tour. Calls :func:`mark_tour_shown` on completion."""
    state = {"step": 0}

    win = tk.Toplevel(root)
    win.title("Quick tour")
    win.configure(bg=_BG)
    win.transient(root)
    try:
        win.grab_set()
    except Exception:
        pass
    w, h = 480, 240
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
    win.resizable(False, False)

    title_lbl = tk.Label(win, text="", bg=_BG, fg=_FG,
                         font=("Segoe UI", 16, "bold"))
    title_lbl.pack(pady=(20, 8))
    body_lbl = tk.Label(win, text="", bg=_BG, fg=_FG_MUTED,
                        font=("Segoe UI", 11), wraplength=420, justify="center")
    body_lbl.pack(pady=(0, 12))
    progress_lbl = tk.Label(win, text="", bg=_BG, fg=_FG_MUTED,
                            font=("Segoe UI", 9))
    progress_lbl.pack()

    btns = tk.Frame(win, bg=_BG)
    btns.pack(pady=16)

    def _render():
        title, body = _STEPS[state["step"]]
        title_lbl.configure(text=title)
        body_lbl.configure(text=body)
        progress_lbl.configure(text=f"{state['step'] + 1} / {len(_STEPS)}")
        next_btn.configure(text="Got it" if state["step"] == len(_STEPS) - 1 else "Next  ›")
        back_btn.configure(state=tk.NORMAL if state["step"] > 0 else tk.DISABLED)

    def _close():
        mark_tour_shown()
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    def _next():
        if state["step"] < len(_STEPS) - 1:
            state["step"] += 1
            _render()
        else:
            _close()

    def _back():
        if state["step"] > 0:
            state["step"] -= 1
            _render()

    back_btn = tk.Button(
        btns, text="‹ Back", command=_back,
        bg=_BG_CARD, fg=_FG_MUTED, activebackground=_BORDER, activeforeground=_FG,
        font=("Segoe UI", 10), relief=tk.FLAT, padx=14, pady=6, bd=0,
        highlightthickness=0, cursor="hand2",
    )
    back_btn.pack(side=tk.LEFT, padx=6)
    skip_btn = tk.Button(
        btns, text="Skip", command=_close,
        bg=_BG, fg=_FG_MUTED, activebackground=_BG, activeforeground=_FG,
        font=("Segoe UI", 10), relief=tk.FLAT, padx=10, pady=6, bd=0,
        highlightthickness=0, cursor="hand2",
    )
    skip_btn.pack(side=tk.LEFT, padx=6)
    next_btn = tk.Button(
        btns, text="Next ›", command=_next,
        bg=_ACCENT, fg="#0b1220", activebackground="#3893e6", activeforeground="#0b1220",
        font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=18, pady=6, bd=0,
        highlightthickness=0, cursor="hand2",
    )
    next_btn.pack(side=tk.LEFT, padx=6)

    win.protocol("WM_DELETE_WINDOW", _close)
    _render()


def maybe_show_tour(root: tk.Tk) -> None:
    """Show the tour on first launch only."""
    if tour_already_shown():
        return
    # Delay so the main window is rendered first
    root.after(800, lambda: show_tour(root))
