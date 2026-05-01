"""Compatibility layer — provides ttkbootstrap-like API using plain tkinter/ttk.

This module eliminates the hard dependency on ttkbootstrap by providing
fallback implementations. If ttkbootstrap is installed it will be used;
otherwise plain tkinter/ttk handles everything.

When ttkbootstrap is NOT available, ttk widget constructors are patched to
silently ignore the 'bootstyle' keyword argument so existing code doesn't break.
"""

import tkinter as tk
from tkinter import ttk

# ─── Try to import ttkbootstrap, fallback gracefully ────────────────────────
_USE_BOOTSTRAP = False
try:
    import ttkbootstrap as _ttk_bs
    from ttkbootstrap.constants import *  # noqa: F401,F403
    _USE_BOOTSTRAP = True
except (ImportError, Exception):
    _ttk_bs = None
    # Patch ttk widgets to silently ignore 'bootstyle' kwarg
    _original_inits = {}
    _widgets_to_patch = [
        'Button', 'Label', 'Entry', 'Checkbutton', 'Radiobutton',
        'Frame', 'LabelFrame', 'Progressbar', 'Scale', 'Scrollbar',
        'Combobox', 'Notebook', 'Separator', 'Treeview', 'Menubutton',
        'Spinbox', 'OptionMenu',
    ]
    for _widget_name in _widgets_to_patch:
        _cls = getattr(ttk, _widget_name, None)
        if _cls is None:
            continue
        _orig_init = _cls.__init__

        def _make_patched(orig):
            def _patched_init(self, *args, **kwargs):
                kwargs.pop('bootstyle', None)
                return orig(self, *args, **kwargs)
            return _patched_init

        _cls.__init__ = _make_patched(_orig_init)


# ─── Window ─────────────────────────────────────────────────────────────────

def create_window(title: str = "", geometry: str = "", themename: str = "darkly"):
    """Create the main application window.
    
    Uses ttkbootstrap.Window if available, otherwise plain tk.Tk with dark styling.
    """
    if _USE_BOOTSTRAP:
        root = _ttk_bs.Window(themename=themename)
    else:
        root = tk.Tk()
        _apply_dark_theme(root)
    if title:
        root.title(title)
    if geometry:
        root.geometry(geometry)
    return root


def get_style(root=None):
    """Get a ttk.Style instance (ttkbootstrap or plain)."""
    if _USE_BOOTSTRAP:
        return _ttk_bs.Style()
    return ttk.Style(root)


# ─── ScrolledFrame ──────────────────────────────────────────────────────────

class ScrolledFrame(ttk.Frame):
    """A scrollable frame widget — lightweight fallback for ttkbootstrap's ScrolledFrame."""

    def __init__(self, parent, autohide=True, **kwargs):
        if _USE_BOOTSTRAP:
            # Delegate to ttkbootstrap's implementation
            from ttkbootstrap.widgets.scrolled import ScrolledFrame as _BSFrame
            self._bs_frame = _BSFrame(parent, autohide=autohide, **kwargs)
            # Proxy pack/grid/place to the bootstrap frame
            self.pack = self._bs_frame.pack
            self.grid = self._bs_frame.grid
            self.place = self._bs_frame.place
            self.pack_forget = self._bs_frame.pack_forget
            self.grid_forget = self._bs_frame.grid_forget
            self.destroy = self._bs_frame.destroy
            # The inner container where children go
            self._container = self._bs_frame
            super().__init__(parent)
            # Hide the ttk.Frame we inherited (we just use it for type compat)
            return

        # Plain tkinter fallback
        super().__init__(parent, **kwargs)
        self._bs_frame = None

        self._canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._inner = ttk.Frame(self._canvas)

        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        if not autohide:
            self._scrollbar.pack(side="right", fill="y")
        else:
            # Show scrollbar only when needed
            self._autohide = True
            self._scrollbar_visible = False

        # Mouse wheel scrolling
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

        self._container = self._inner

    def _on_inner_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        if hasattr(self, '_autohide') and self._autohide:
            if self._inner.winfo_reqheight() > self._canvas.winfo_height():
                if not self._scrollbar_visible:
                    self._scrollbar.pack(side="right", fill="y")
                    self._scrollbar_visible = True
            else:
                if self._scrollbar_visible:
                    self._scrollbar.pack_forget()
                    self._scrollbar_visible = False

    def _on_canvas_configure(self, event=None):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _bind_mousewheel(self, event=None):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event=None):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def winfo_children(self):
        """Return children of the inner scrollable frame."""
        if self._bs_frame and _USE_BOOTSTRAP:
            return self._bs_frame.winfo_children()
        return self._inner.winfo_children()

    def __getattr__(self, name):
        """Proxy attribute access to the inner container for child widget packing."""
        if name.startswith('_'):
            raise AttributeError(name)
        if self._bs_frame and _USE_BOOTSTRAP:
            return getattr(self._bs_frame, name)
        return getattr(self._inner, name)


# ─── Dark Theme Application ────────────────────────────────────────────────

def _apply_dark_theme(root):
    """Apply a dark theme to plain tkinter/ttk that looks reasonable."""
    root.configure(bg="#1a1a2e")

    style = ttk.Style(root)

    # Try to use 'clam' as base (looks best for custom colors)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Dark color definitions
    bg = "#1a1a2e"
    bg2 = "#222240"
    bg3 = "#2a2a48"
    fg = "#e0e0e0"
    fg2 = "#a0a0b0"
    accent = "#4CC2FF"
    select_bg = "#3a3a5e"

    style.configure(".", background=bg, foreground=fg, fieldbackground=bg2,
                    bordercolor=bg3, darkcolor=bg2, lightcolor=bg3,
                    insertcolor=fg, selectbackground=select_bg, selectforeground=fg)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background=bg2, foreground=fg, padding=(8, 4))
    style.map("TButton",
              background=[("active", bg3), ("pressed", accent)],
              foreground=[("active", fg)])
    style.configure("TEntry", fieldbackground=bg2, foreground=fg)
    style.configure("TCheckbutton", background=bg, foreground=fg)
    style.map("TCheckbutton", background=[("active", bg)])
    style.configure("TRadiobutton", background=bg, foreground=fg)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    style.configure("TNotebook", background=bg)
    style.configure("TNotebook.Tab", background=bg2, foreground=fg, padding=(10, 4))
    style.map("TNotebook.Tab",
              background=[("selected", bg3)],
              foreground=[("selected", accent)])
    style.configure("Treeview", background=bg2, foreground=fg,
                    fieldbackground=bg2, rowheight=28)
    style.map("Treeview", background=[("selected", select_bg)])
    style.configure("Treeview.Heading", background=bg3, foreground=fg)
    style.configure("TProgressbar", background=accent, troughcolor=bg2)
    style.configure("TScale", background=bg, troughcolor=bg2)
    style.configure("TScrollbar", background=bg2, troughcolor=bg)
    style.configure("TSeparator", background=bg3)
    style.configure("TCombobox", fieldbackground=bg2, foreground=fg)


# ─── Bootstyle-aware widget wrappers ───────────────────────────────────────

def Button(parent, bootstyle=None, **kwargs):
    """Create a ttk.Button, ignoring bootstyle if ttkbootstrap not available."""
    if _USE_BOOTSTRAP and bootstyle:
        return ttk.Button(parent, bootstyle=bootstyle, **kwargs)
    return ttk.Button(parent, **kwargs)


def Checkbutton(parent, bootstyle=None, **kwargs):
    """Create a ttk.Checkbutton, ignoring bootstyle if ttkbootstrap not available."""
    if _USE_BOOTSTRAP and bootstyle:
        return ttk.Checkbutton(parent, bootstyle=bootstyle, **kwargs)
    return ttk.Checkbutton(parent, **kwargs)


def Label(parent, bootstyle=None, **kwargs):
    """Create a ttk.Label, ignoring bootstyle if ttkbootstrap not available."""
    if _USE_BOOTSTRAP and bootstyle:
        return ttk.Label(parent, bootstyle=bootstyle, **kwargs)
    return ttk.Label(parent, **kwargs)


def Entry(parent, bootstyle=None, **kwargs):
    """Create a ttk.Entry, ignoring bootstyle if ttkbootstrap not available."""
    if _USE_BOOTSTRAP and bootstyle:
        return ttk.Entry(parent, bootstyle=bootstyle, **kwargs)
    return ttk.Entry(parent, **kwargs)


def Progressbar(parent, bootstyle=None, **kwargs):
    """Create a ttk.Progressbar, ignoring bootstyle if ttkbootstrap not available."""
    if _USE_BOOTSTRAP and bootstyle:
        return ttk.Progressbar(parent, bootstyle=bootstyle, **kwargs)
    return ttk.Progressbar(parent, **kwargs)
