"""First-run consent and age verification dialog for TV Viewer.

Matches the Flutter app's ConsentDialog. Shows on first launch to inform
users about content sources, verify age, and offer analytics opt-in.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser

from .constants import FluentColorsDark as FluentColors


PRIVACY_POLICY_URL = "https://tv-viewer-app.github.io/tv_viewer/#privacy"

CONTENT_NOTICE = (
    "This app streams live TV from publicly available internet sources "
    "(IPTV). The developers do not host, control, or verify the content "
    "of these streams.\n\n"
    "By continuing, you acknowledge that:\n\n"
    "• Content is provided by third-party sources and may include "
    "material unsuitable for minors.\n"
    "• You are solely responsible for the content you choose to watch.\n"
    "• The developers are not liable for any content accessed through "
    "this application.\n"
    "• You agree to comply with the laws of your jurisdiction regarding "
    "online content consumption."
)


def show_consent_dialog(parent) -> dict:
    """Show first-run consent and age verification dialog.

    Args:
        parent: The parent Tk window (can be a withdrawn root).

    Returns:
        dict with keys:
            'accepted' (bool): True if user clicked Continue with age confirmed.
            'analytics' (bool): True if user opted in to analytics.
        If the user exits/declines, returns {'accepted': False, 'analytics': False}.
    """
    result = {'accepted': False, 'analytics': False}

    dlg = tk.Toplevel(parent)
    dlg.title("Welcome — Content Notice")
    dlg.geometry("520x560")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    dlg.protocol("WM_DELETE_WINDOW", lambda: _on_exit())

    # Center on parent
    dlg.update_idletasks()
    px = parent.winfo_x() + (parent.winfo_width() - 520) // 2
    py = parent.winfo_y() + (parent.winfo_height() - 560) // 2
    dlg.geometry(f"+{max(0, px)}+{max(0, py)}")

    # ── Content ──────────────────────────────────────────────────────
    frame = ttk.Frame(dlg, padding=24)
    frame.pack(fill="both", expand=True)

    # Title
    ttk.Label(
        frame,
        text="📺 Content Notice",
        font=("Segoe UI", 18, "bold"),
        foreground=FluentColors.ACCENT,
    ).pack(anchor="w", pady=(0, 12))

    # Notice text in a scrollable Text widget (read-only)
    notice_text = tk.Text(
        frame,
        wrap="word",
        font=("Segoe UI", 10),
        height=12,
        relief="flat",
        background=FluentColors.BG_CARD,
        foreground=FluentColors.TEXT_PRIMARY,
        padx=10,
        pady=8,
        cursor="arrow",
    )
    notice_text.insert("1.0", CONTENT_NOTICE)
    notice_text.configure(state="disabled")
    notice_text.pack(fill="x", pady=(0, 12))

    # Privacy policy link
    link_frame = ttk.Frame(frame)
    link_frame.pack(fill="x", pady=(0, 12))
    ttk.Label(link_frame, text="📄", font=("Segoe UI", 10)).pack(side="left")
    privacy_link = ttk.Label(
        link_frame,
        text="Privacy Policy",
        font=("Segoe UI", 10, "underline"),
        foreground=FluentColors.ACCENT,
        cursor="hand2",
    )
    privacy_link.pack(side="left", padx=(4, 0))
    privacy_link.bind("<Button-1>", lambda e: webbrowser.open(PRIVACY_POLICY_URL))

    # ── Checkboxes ───────────────────────────────────────────────────
    age_var = tk.BooleanVar(value=False)
    age_cb = ttk.Checkbutton(
        frame,
        text="I confirm I am 18 years of age or older",
        variable=age_var,
        bootstyle="round-toggle",
    )
    age_cb.pack(anchor="w", pady=(4, 4))

    analytics_var = tk.BooleanVar(value=True)
    analytics_cb = ttk.Checkbutton(
        frame,
        text="Allow anonymous usage analytics to help improve the app",
        variable=analytics_var,
        bootstyle="round-toggle",
    )
    analytics_cb.pack(anchor="w", pady=(0, 16))

    # ── Warning label (shown if user tries to continue without age) ──
    warning_label = ttk.Label(
        frame,
        text="",
        font=("Segoe UI", 9),
        foreground=FluentColors.ERROR,
    )
    warning_label.pack(anchor="w")

    # ── Buttons ──────────────────────────────────────────────────────
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", pady=(8, 0))

    def _on_exit():
        result['accepted'] = False
        result['analytics'] = False
        dlg.destroy()

    def _on_continue():
        if not age_var.get():
            warning_label.configure(
                text="⚠ You must confirm your age to continue."
            )
            return
        result['accepted'] = True
        result['analytics'] = analytics_var.get()
        dlg.destroy()

    ttk.Button(
        btn_frame,
        text="Exit",
        command=_on_exit,
        bootstyle="secondary",
        width=12,
    ).pack(side="left")

    ttk.Button(
        btn_frame,
        text="Continue",
        command=_on_continue,
        bootstyle="primary",
        width=12,
    ).pack(side="right")

    # Block until dialog closed
    dlg.wait_window()
    return result
