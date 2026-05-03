"""Channel filter dialog (Issue #160).

Modal dialog with three multi-select listboxes for Language / Country /
Category.  Selections are AND'd across dimensions, OR'd within a single
dimension.  Stored on the calling :class:`TVModeApp` as
``_active_filters`` and persisted to ``~/.tv_viewer/ui_state.json``.
"""
from __future__ import annotations

import json
import os
import tkinter as tk
from typing import Callable, Dict, Iterable, List, Set

_BG = "#15171c"
_FG = "#e6e6e6"
_FG_MUTED = "#9aa0a6"
_ACCENT = "#4da6ff"
_BG_CARD = "#1f222a"
_BORDER = "#2a2d35"


def _ui_state_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".tv_viewer")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "ui_state.json")


def load_filters() -> Dict[str, Set[str]]:
    """Return persisted filter selections (sets per dimension)."""
    out = {"language": set(), "country": set(), "category": set()}
    path = _ui_state_path()
    if not os.path.exists(path):
        return out
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in out:
            v = data.get(f"filters.{k}")
            if isinstance(v, list):
                out[k] = set(str(x) for x in v)
    except Exception:
        pass
    return out


def save_filters(filters: Dict[str, Iterable[str]]) -> None:
    path = _ui_state_path()
    data: Dict = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    for k, v in filters.items():
        data[f"filters.{k}"] = sorted(set(v))
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def channel_passes(channel: Dict, filters: Dict[str, Set[str]]) -> bool:
    """True if the channel passes all active filter dimensions."""
    if filters.get("language"):
        lang = (channel.get("language") or "").strip()
        if lang and lang not in filters["language"]:
            return False
    if filters.get("country"):
        country = (channel.get("country") or "").strip()
        if country and country not in filters["country"]:
            return False
    if filters.get("category"):
        cat = (channel.get("category") or "Other").strip()
        if cat not in filters["category"]:
            return False
    return True


def show_filter_dialog(
    root: tk.Tk,
    languages: List[str],
    countries: List[str],
    categories: List[str],
    current: Dict[str, Set[str]],
    on_apply: Callable[[Dict[str, Set[str]]], None],
) -> None:
    win = tk.Toplevel(root)
    win.title("Filter channels")
    win.configure(bg=_BG)
    win.transient(root)
    try:
        win.grab_set()
    except Exception:
        pass
    win.update_idletasks()
    w, h = 720, 480
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    tk.Label(
        win, text="Filter channels", bg=_BG, fg=_FG,
        font=("Segoe UI", 16, "bold"),
    ).pack(pady=(16, 4))
    tk.Label(
        win,
        text="Pick one or more in each list (Ctrl-click). Empty list = no filter.",
        bg=_BG, fg=_FG_MUTED, font=("Segoe UI", 9),
    ).pack(pady=(0, 12))

    body = tk.Frame(win, bg=_BG)
    body.pack(fill=tk.BOTH, expand=True, padx=16)

    listboxes: Dict[str, tk.Listbox] = {}
    for col, (key, items) in enumerate(
        (("language", languages), ("country", countries), ("category", categories))
    ):
        col_frame = tk.Frame(body, bg=_BG)
        col_frame.grid(row=0, column=col, padx=6, sticky="nsew")
        body.grid_columnconfigure(col, weight=1)
        tk.Label(
            col_frame, text=key.capitalize(), bg=_BG, fg=_FG,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        lb = tk.Listbox(
            col_frame, selectmode=tk.MULTIPLE,
            bg=_BG_CARD, fg=_FG, selectbackground=_ACCENT, selectforeground="#0b1220",
            highlightbackground=_BORDER, highlightthickness=1, bd=0,
            font=("Segoe UI", 10), exportselection=False, height=18,
        )
        for item in items:
            if not item:
                continue
            lb.insert(tk.END, item)
        # Restore current selection
        sel = current.get(key, set())
        for i in range(lb.size()):
            if lb.get(i) in sel:
                lb.selection_set(i)
        lb.pack(fill=tk.BOTH, expand=True)
        listboxes[key] = lb

    btns = tk.Frame(win, bg=_BG)
    btns.pack(pady=16)

    def _selected(key: str) -> Set[str]:
        lb = listboxes[key]
        return {lb.get(i) for i in lb.curselection()}

    def _apply():
        out = {key: _selected(key) for key in listboxes}
        save_filters(out)
        on_apply(out)
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    def _clear():
        for lb in listboxes.values():
            lb.selection_clear(0, tk.END)

    tk.Button(
        btns, text="Clear all", command=_clear,
        bg=_BG_CARD, fg=_FG_MUTED, activebackground=_BORDER, activeforeground=_FG,
        font=("Segoe UI", 10), relief=tk.FLAT, padx=14, pady=6, bd=0,
        highlightthickness=0, cursor="hand2",
    ).pack(side=tk.LEFT, padx=6)
    tk.Button(
        btns, text="Cancel", command=win.destroy,
        bg=_BG_CARD, fg=_FG_MUTED, activebackground=_BORDER, activeforeground=_FG,
        font=("Segoe UI", 10), relief=tk.FLAT, padx=14, pady=6, bd=0,
        highlightthickness=0, cursor="hand2",
    ).pack(side=tk.LEFT, padx=6)
    tk.Button(
        btns, text="Apply", command=_apply,
        bg=_ACCENT, fg="#0b1220", activebackground="#3893e6", activeforeground="#0b1220",
        font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=18, pady=6, bd=0,
        highlightthickness=0, cursor="hand2",
    ).pack(side=tk.LEFT, padx=6)
