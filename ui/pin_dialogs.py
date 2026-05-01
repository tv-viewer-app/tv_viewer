"""PIN entry and management dialogs for parental controls.

Extracted from MainWindow to reduce the size of main_window.py.
All references to `self` have been replaced with `parent_window` (the MainWindow instance).
"""

import tkinter as tk
from tkinter import ttk
from ui.compat import ScrolledFrame  # noqa: F401

from .constants import FluentColorsDark as FluentColors
from utils.logger import get_logger

logger = get_logger(__name__)


def show_pin_entry_dialog(parent_window, title="🔒 Enter PIN", message="Enter your 4-digit PIN:",
                          on_success=None, on_cancel=None, parent=None):
    """Show a modal PIN entry dialog with 4 auto-advancing digit fields.

    - Wrong PIN triggers a shake animation.
    - 3 failed attempts triggers a 30-second lockout.

    Args:
        parent_window: The MainWindow instance.
        title: Dialog title.
        message: Message to display.
        on_success: Callback on successful PIN entry.
        on_cancel: Callback on cancel.
        parent: Parent widget for the dialog (defaults to parent_window.root).
    """
    parent = parent or parent_window.root
    C = FluentColors

    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.resizable(False, False)
    dlg.grab_set()
    dw, dh = 320, 240
    rx = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
    ry = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
    dlg.geometry(f"{dw}x{dh}+{rx}+{ry}")

    msg_lbl = ttk.Label(dlg, text=message, font=("Segoe UI", 11),
                        wraplength=280, justify="center")
    msg_lbl.pack(padx=16, pady=(18, 8))

    error_lbl = ttk.Label(dlg, text="", font=("Segoe UI", 10),
                          foreground=C.ERROR)
    error_lbl.pack()

    pin_frame = ttk.Frame(dlg)
    pin_frame.pack(pady=10)

    entries = []
    pin_vars = []
    for i in range(4):
        var = tk.StringVar()
        pin_vars.append(var)
        e = ttk.Entry(pin_frame, textvariable=var, width=3, font=("Segoe UI", 20, "bold"),
                      justify="center")
        e.pack(side="left", padx=6)
        entries.append(e)

    def _on_key(idx, event):
        """Handle key press in a PIN digit field."""
        var = pin_vars[idx]
        entry = entries[idx]
        char = event.char

        # Handle Backspace — clear current or go back
        if event.keysym == "BackSpace":
            if var.get():
                var.set("")
            elif idx > 0:
                entries[idx - 1].focus_set()
                pin_vars[idx - 1].set("")
            return "break"

        # Only accept digits
        if char and char.isdigit():
            var.set(char)
            if idx < 3:
                entries[idx + 1].focus_set()
            else:
                # All 4 entered — auto-verify
                dlg.after(50, _verify)
            return "break"

        # Block non-digit characters
        if char:
            return "break"

    for idx, entry in enumerate(entries):
        entry.bind("<Key>", lambda e, i=idx: _on_key(i, e))

    entries[0].focus_set()

    _attempts = [0]

    def _shake():
        """Shake the dialog on wrong PIN."""
        orig_x = dlg.winfo_x()
        offsets = [10, -10, 8, -8, 5, -5, 2, -2, 0]
        for i, offset in enumerate(offsets):
            dlg.after(i * 40, lambda o=offset: dlg.geometry(f"+{orig_x + o}+{dlg.winfo_y()}"))

    def _verify():
        pin = "".join(v.get() for v in pin_vars)
        if len(pin) != 4:
            return

        if parent_window.parental_controls.is_locked_out():
            remaining = parent_window.parental_controls.lockout_remaining()
            error_lbl.configure(text=f"Too many attempts. Wait {remaining}s")
            for v in pin_vars:
                v.set("")
            entries[0].focus_set()
            _shake()
            return

        if parent_window.parental_controls.verify_pin(pin):
            dlg.destroy()
            if on_success:
                on_success()
        else:
            _attempts[0] += 1
            if parent_window.parental_controls.is_locked_out():
                remaining = parent_window.parental_controls.lockout_remaining()
                error_lbl.configure(text=f"Locked out for {remaining}s")
            else:
                error_lbl.configure(text="Wrong PIN. Try again.")
            for v in pin_vars:
                v.set("")
            entries[0].focus_set()
            _shake()

    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(pady=8)
    ttk.Button(btn_frame, text="Unlock", command=_verify,
               bootstyle="primary", width=10).pack(side="left", padx=4)

    def _cancel():
        dlg.destroy()
        if on_cancel:
            on_cancel()

    ttk.Button(btn_frame, text="Cancel", command=_cancel,
               bootstyle="secondary", width=10).pack(side="left", padx=4)
    dlg.protocol("WM_DELETE_WINDOW", _cancel)


def show_set_pin_dialog(parent_window, parent=None, on_success=None, on_cancel=None):
    """Show a dialog to set a new 4-digit PIN (first time setup).

    Args:
        parent_window: The MainWindow instance.
        parent: Parent widget for the dialog (defaults to parent_window.root).
        on_success: Callback on successful PIN setup.
        on_cancel: Callback on cancel.
    """
    parent = parent or parent_window.root
    C = FluentColors

    dlg = tk.Toplevel(parent)
    dlg.title("🔒 Set Parental PIN")
    dlg.resizable(False, False)
    dlg.grab_set()
    dw, dh = 320, 280
    rx = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
    ry = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
    dlg.geometry(f"{dw}x{dh}+{rx}+{ry}")

    ttk.Label(dlg, text="Create a 4-digit PIN:", font=("Segoe UI", 11),
              justify="center").pack(padx=16, pady=(18, 4))
    error_lbl = ttk.Label(dlg, text="", font=("Segoe UI", 10),
                          foreground=C.ERROR)
    error_lbl.pack()

    # PIN row
    pin_frame = ttk.Frame(dlg)
    pin_frame.pack(pady=6)
    pin_vars = []
    pin_entries = []
    for _ in range(4):
        var = tk.StringVar()
        pin_vars.append(var)
        e = ttk.Entry(pin_frame, textvariable=var, width=3, font=("Segoe UI", 20, "bold"),
                      justify="center")
        e.pack(side="left", padx=6)
        pin_entries.append(e)

    # Confirm row
    ttk.Label(dlg, text="Confirm PIN:", font=("Segoe UI", 11),
              justify="center").pack(padx=16, pady=(8, 4))
    conf_frame = ttk.Frame(dlg)
    conf_frame.pack(pady=6)
    conf_vars = []
    conf_entries = []
    for _ in range(4):
        var = tk.StringVar()
        conf_vars.append(var)
        e = ttk.Entry(conf_frame, textvariable=var, width=3, font=("Segoe UI", 20, "bold"),
                      justify="center")
        e.pack(side="left", padx=6)
        conf_entries.append(e)

    all_entries = pin_entries + conf_entries
    all_vars = pin_vars + conf_vars

    def _on_key(idx, event):
        var = all_vars[idx]
        char = event.char
        if event.keysym == "BackSpace":
            if var.get():
                var.set("")
            elif idx > 0:
                all_entries[idx - 1].focus_set()
                all_vars[idx - 1].set("")
            return "break"
        if char and char.isdigit():
            var.set(char)
            if idx < len(all_entries) - 1:
                all_entries[idx + 1].focus_set()
            return "break"
        if char:
            return "break"

    for idx, entry in enumerate(all_entries):
        entry.bind("<Key>", lambda e, i=idx: _on_key(i, e))
    pin_entries[0].focus_set()

    def _confirm():
        pin = "".join(v.get() for v in pin_vars)
        confirm = "".join(v.get() for v in conf_vars)
        if len(pin) != 4 or not pin.isdigit():
            error_lbl.configure(text="Enter 4 digits")
            return
        if pin != confirm:
            error_lbl.configure(text="PINs don't match")
            for v in conf_vars:
                v.set("")
            conf_entries[0].focus_set()
            return
        parent_window.parental_controls.setup_pin(pin)
        dlg.destroy()
        if on_success:
            on_success()

    def _cancel():
        dlg.destroy()
        if on_cancel:
            on_cancel()

    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(pady=8)
    ttk.Button(btn_frame, text="Set PIN", command=_confirm,
               bootstyle="primary", width=10).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Cancel", command=_cancel,
               bootstyle="secondary", width=10).pack(side="left", padx=4)
    dlg.protocol("WM_DELETE_WINDOW", _cancel)


def show_change_pin_dialog(parent_window, parent=None):
    """Show dialog to change PIN (old PIN → new PIN → confirm).

    Args:
        parent_window: The MainWindow instance.
        parent: Parent widget for the dialog (defaults to parent_window.root).
    """
    parent = parent or parent_window.root

    def _after_old_pin_verified():
        parent_window._show_set_pin_dialog(parent=parent)

    parent_window._show_pin_entry_dialog(
        title="🔒 Change PIN",
        message="Enter your current PIN first:",
        on_success=_after_old_pin_verified,
        parent=parent,
    )
