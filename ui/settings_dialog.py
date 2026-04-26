"""Settings dialog for TV Viewer.

Extracted from MainWindow._show_settings_dialog to reduce the size of main_window.py.
All references to `self` have been replaced with `parent_window` (the MainWindow instance).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk_bs
import json as _json
import os

import config
from utils.logger import get_logger
from .constants import FluentColorsDark as FluentColors

logger = get_logger(__name__)

# Try to import icon module
try:
    from icon import set_window_icon
except ImportError:
    set_window_icon = None


def show_settings_dialog(parent_window):
    """Show a proper Settings dialog with stream, repo, and display options.

    Args:
        parent_window: The MainWindow instance (needed for accessing root,
                      favorites, parental controls, channels, etc.)
    """

    # Prevent multiple dialogs
    if hasattr(parent_window, '_settings_win') and parent_window._settings_win is not None:
        try:
            parent_window._settings_win.focus_set()
            return
        except tk.TclError:
            parent_window._settings_win = None

    C = FluentColors  # alias for dark colors used below
    CD = FluentColors
    try:
        from .constants import FluentColorsDark
        CD = FluentColorsDark
    except Exception:
        pass

    FONT = ("Segoe UI", 11)
    FONT_BOLD = ("Segoe UI", 11, "bold")
    FONT_SECTION = ("Segoe UI", 13, "bold")
    FONT_SMALL = ("Segoe UI", 10)

    # ── Load current values ──────────────────────────────────────────
    cur_stream_timeout = getattr(config, 'STREAM_CHECK_TIMEOUT', 5)
    cur_max_concurrent = getattr(config, 'MAX_CONCURRENT_CHECKS', 30)
    cur_request_timeout = getattr(config, 'REQUEST_TIMEOUT', 15)
    cur_batch_size = getattr(config, 'SCAN_BATCH_SIZE', 200)
    cur_scan_delay = getattr(config, 'SCAN_REQUEST_DELAY', 0.005)

    # Load repos from channels_config.json
    config_path = config.CHANNELS_CONFIG_FILE
    cfg_data = {}
    repos_list: list = []
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg_data = _json.load(f)
            repos_list = list(cfg_data.get('repositories', []))
    except Exception as e:
        logger.error(f"Settings: failed to read config JSON: {e}")

    # Default repos for Reset
    default_repos = [
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://iptv-org.github.io/iptv/index.country.m3u",
    ]

    # ── Create dialog window ─────────────────────────────────────────
    dlg = ttk_bs.Toplevel(parent_window.root)
    dlg.title("Settings")
    dlg.resizable(False, False)
    dlg.grab_set()
    parent_window._settings_win = dlg

    # Size & center on parent
    dw, dh = 520, 880
    rx = parent_window.root.winfo_rootx() + (parent_window.root.winfo_width() - dw) // 2
    ry = parent_window.root.winfo_rooty() + (parent_window.root.winfo_height() - dh) // 2
    dlg.geometry(f"{dw}x{dh}+{rx}+{ry}")

    def _on_close():
        # Unbind mousewheel handler to prevent stacking on repeated opens
        if hasattr(parent_window, '_settings_mousewheel_handler'):
            try:
                dlg.unbind_all("<MouseWheel>")
            except Exception:
                pass
        parent_window._settings_win = None
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)

    # Try to set icon
    if set_window_icon:
        try:
            set_window_icon(dlg)
        except Exception:
            pass

    # ── Scrollable content ───────────────────────────────────────────
    outer = ttk.Frame(dlg)
    outer.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Enable mouse-wheel scrolling (5x faster than default)
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-5 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Store reference so we can unbind on dialog close
    parent_window._settings_mousewheel_handler = _on_mousewheel
    parent_window._settings_canvas = canvas

    content = ttk.Frame(scroll_frame, padding=18)
    content.pack(fill="both", expand=True)

    # ── Section helper ───────────────────────────────────────────────
    def _section(parent, title, row):
        lbl = ttk.Label(parent, text=title, font=FONT_SECTION,
                        foreground=CD.ACCENT)
        lbl.grid(row=row, column=0, columnspan=3, sticky="w", pady=(14, 4))
        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=row + 1, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        return row + 2

    # ── 1. Stream Settings ───────────────────────────────────────────
    r = _section(content, "⚡  Stream Settings", 0)

    # Stream check timeout
    ttk.Label(content, text="Stream check timeout (s):", font=FONT
              ).grid(row=r, column=0, sticky="w", padx=(0, 8))
    stream_timeout_var = tk.IntVar(value=cur_stream_timeout)
    stream_timeout_spin = ttk.Spinbox(
        content, from_=1, to=30, width=6,
        textvariable=stream_timeout_var, font=FONT
    )
    stream_timeout_spin.grid(row=r, column=1, sticky="w")
    ttk.Label(content, text="1–30", font=FONT_SMALL,
              foreground=CD.TEXT_SECONDARY
              ).grid(row=r, column=2, sticky="w", padx=4)
    r += 1

    # Max concurrent checks
    ttk.Label(content, text="Max concurrent checks:", font=FONT
              ).grid(row=r, column=0, sticky="w", padx=(0, 8))
    max_concurrent_var = tk.IntVar(value=cur_max_concurrent)
    max_concurrent_spin = ttk.Spinbox(
        content, from_=1, to=100, width=6,
        textvariable=max_concurrent_var, font=FONT
    )
    max_concurrent_spin.grid(row=r, column=1, sticky="w")
    ttk.Label(content, text="1–100", font=FONT_SMALL,
              foreground=CD.TEXT_SECONDARY
              ).grid(row=r, column=2, sticky="w", padx=4)
    r += 1

    # Request timeout
    ttk.Label(content, text="Request timeout (s):", font=FONT
              ).grid(row=r, column=0, sticky="w", padx=(0, 8))
    request_timeout_var = tk.IntVar(value=cur_request_timeout)
    request_timeout_spin = ttk.Spinbox(
        content, from_=5, to=60, width=6,
        textvariable=request_timeout_var, font=FONT
    )
    request_timeout_spin.grid(row=r, column=1, sticky="w")
    ttk.Label(content, text="5–60", font=FONT_SMALL,
              foreground=CD.TEXT_SECONDARY
              ).grid(row=r, column=2, sticky="w", padx=4)
    r += 1

    # Batch size
    ttk.Label(content, text="Scan batch size:", font=FONT
              ).grid(row=r, column=0, sticky="w", padx=(0, 8))
    batch_size_var = tk.IntVar(value=cur_batch_size)
    batch_size_spin = ttk.Spinbox(
        content, from_=50, to=1000, increment=50, width=6,
        textvariable=batch_size_var, font=FONT
    )
    batch_size_spin.grid(row=r, column=1, sticky="w")
    ttk.Label(content, text="50–1000", font=FONT_SMALL,
              foreground=CD.TEXT_SECONDARY
              ).grid(row=r, column=2, sticky="w", padx=4)
    r += 1

    # ── 2. Repository Management ────────────────────────────────────
    r = _section(content, "📡  Repositories", r)

    repo_frame = ttk.Frame(content)
    repo_frame.grid(row=r, column=0, columnspan=3, sticky="nsew", pady=(0, 4))
    content.grid_rowconfigure(r, weight=1)
    content.grid_columnconfigure(0, weight=1)
    r += 1

    # Listbox + scrollbar for repos
    repo_lb_frame = ttk.Frame(repo_frame)
    repo_lb_frame.pack(fill="both", expand=True)

    repo_scrollbar = ttk.Scrollbar(repo_lb_frame, orient="vertical")
    repo_listbox = tk.Listbox(
        repo_lb_frame, height=6, selectmode=tk.EXTENDED,
        font=FONT_SMALL,
        bg=CD.BG_CARD, fg=CD.TEXT_PRIMARY,
        selectbackground=FluentColors.ACCENT, selectforeground=FluentColors.BG_CARD,
        highlightthickness=0, bd=1, relief="solid",
        yscrollcommand=repo_scrollbar.set
    )
    repo_scrollbar.configure(command=repo_listbox.yview)
    repo_listbox.pack(side="left", fill="both", expand=True)
    repo_scrollbar.pack(side="right", fill="y")

    # Populate
    for url in repos_list:
        repo_listbox.insert(tk.END, url)

    # Repo buttons
    repo_btn_frame = ttk.Frame(repo_frame)
    repo_btn_frame.pack(fill="x", pady=(4, 0))

    def _add_repo():
        add_dlg = ttk_bs.Toplevel(dlg)
        add_dlg.title("Add Repository URL")
        add_dlg.resizable(False, False)
        add_dlg.grab_set()
        adw, adh = 440, 120
        ax = dlg.winfo_rootx() + (dlg.winfo_width() - adw) // 2
        ay = dlg.winfo_rooty() + (dlg.winfo_height() - adh) // 2
        add_dlg.geometry(f"{adw}x{adh}+{ax}+{ay}")

        ttk.Label(add_dlg, text="Repository URL:", font=FONT
                  ).pack(anchor="w", padx=12, pady=(10, 2))
        url_var = tk.StringVar()
        url_entry = ttk.Entry(add_dlg, textvariable=url_var, width=52, font=FONT_SMALL)
        url_entry.pack(padx=12, fill="x")
        url_entry.focus_set()

        def _confirm(event=None):
            url = url_var.get().strip()
            if url:
                repo_listbox.insert(tk.END, url)
            add_dlg.destroy()

        url_entry.bind("<Return>", _confirm)
        btn_fr = ttk.Frame(add_dlg)
        btn_fr.pack(pady=8)
        ttk.Button(btn_fr, text="Add", command=_confirm,
                   bootstyle="primary", width=10).pack(side="left", padx=4)
        ttk.Button(btn_fr, text="Cancel", command=add_dlg.destroy,
                   bootstyle="secondary", width=10).pack(side="left", padx=4)

    def _remove_repo():
        sel = repo_listbox.curselection()
        for idx in reversed(sel):
            repo_listbox.delete(idx)

    ttk.Button(repo_btn_frame, text="➕ Add", command=_add_repo,
               bootstyle="success-outline", width=10
               ).pack(side="left", padx=(0, 4))
    ttk.Button(repo_btn_frame, text="➖ Remove", command=_remove_repo,
               bootstyle="danger-outline", width=10
               ).pack(side="left", padx=(0, 4))

    repo_count_lbl = ttk.Label(
        repo_btn_frame, text=f"{repo_listbox.size()} repos",
        font=FONT_SMALL, foreground=CD.TEXT_SECONDARY
    )
    repo_count_lbl.pack(side="right")

    # Keep count label updated
    def _update_repo_count(*_args):
        repo_count_lbl.configure(text=f"{repo_listbox.size()} repos")

    repo_listbox.bind("<<ListboxSelect>>", _update_repo_count)

    # ── 3. Display Settings ──────────────────────────────────────────
    r = _section(content, "🎨  Display Settings", r)

    # Default group mode
    ttk.Label(content, text="Default group by:", font=FONT
              ).grid(row=r, column=0, sticky="w", padx=(0, 8))
    group_mode_var = tk.StringVar(
        value=parent_window.group_by_mode.capitalize()
    )
    group_combo = ttk.Combobox(
        content, textvariable=group_mode_var,
        values=["Category", "Country"],
        state="readonly", width=14, font=FONT
    )
    group_combo.grid(row=r, column=1, columnspan=2, sticky="w")
    r += 1

    # Theme selector
    ttk.Label(content, text="Theme:", font=FONT
              ).grid(row=r, column=0, sticky="w", padx=(0, 8))
    available_themes = ["darkly", "superhero", "cyborg", "vapor", "solar"]
    current_theme = parent_window.root.style.theme.name if hasattr(parent_window.root.style, 'theme') else "darkly"
    theme_var = tk.StringVar(value=current_theme)
    theme_combo = ttk.Combobox(
        content, textvariable=theme_var,
        values=available_themes,
        state="readonly", width=14, font=FONT
    )
    theme_combo.grid(row=r, column=1, columnspan=2, sticky="w")
    r += 1

    # ── 4. Parental Controls ─────────────────────────────────────────
    r = _section(content, "🔒  Parental Controls", r)

    # Available categories for blocking
    _parental_categories = [
        "XXX", "Adult", "Movies", "Series", "Entertainment",
        "Sports", "News", "Kids", "Music", "Religious",
    ]

    # Enable/disable toggle
    parental_enabled_var = tk.BooleanVar(value=parent_window.parental_controls.enabled)

    def _on_parental_toggle():
        if parental_enabled_var.get():
            # Enabling — require a PIN to be set
            if not parent_window.parental_controls.has_pin():
                parent_window._show_set_pin_dialog(
                    parent=dlg,
                    on_success=lambda: None,
                    on_cancel=lambda: parental_enabled_var.set(False),
                )
        else:
            # Disabling — require PIN verification
            if parent_window.parental_controls.has_pin():
                def _disable():
                    parental_enabled_var.set(False)
                def _cancel():
                    parental_enabled_var.set(True)
                parent_window._show_pin_entry_dialog(
                    title="🔒 Disable Parental Controls",
                    message="Enter PIN to disable parental controls:",
                    on_success=_disable,
                    on_cancel=_cancel,
                    parent=dlg,
                )
                # Keep it enabled until PIN is verified
                parental_enabled_var.set(True)

    parental_cb = ttk.Checkbutton(
        content, text="Enable parental controls",
        variable=parental_enabled_var,
        command=_on_parental_toggle,
    )
    parental_cb.grid(row=r, column=0, columnspan=3, sticky="w")
    r += 1

    # Set/Change PIN button
    def _on_set_change_pin():
        if parent_window.parental_controls.has_pin():
            parent_window._show_change_pin_dialog(parent=dlg)
        else:
            parent_window._show_set_pin_dialog(parent=dlg)

    ttk.Button(
        content, text="Set / Change PIN",
        command=_on_set_change_pin,
        bootstyle="info-outline", width=18,
    ).grid(row=r, column=0, columnspan=3, sticky="w", pady=(2, 6))
    r += 1

    # Category checkboxes
    ttk.Label(content, text="Block categories:", font=FONT
              ).grid(row=r, column=0, columnspan=3, sticky="w")
    r += 1

    cat_vars = {}
    blocked_lower = {c.lower() for c in parent_window.parental_controls.blocked_categories}
    cat_frame = ttk.Frame(content)
    cat_frame.grid(row=r, column=0, columnspan=3, sticky="w", padx=(12, 0))
    for idx, cat_name in enumerate(_parental_categories):
        var = tk.BooleanVar(value=cat_name.lower() in blocked_lower)
        cat_vars[cat_name] = var
        ttk.Checkbutton(cat_frame, text=cat_name, variable=var
                        ).grid(row=idx // 3, column=idx % 3, sticky="w", padx=(0, 12))
    r += 1

    # Over-18 confirmation checkbox (replaces the old age-rating slider)
    over18_var = tk.BooleanVar(value=parent_window.parental_controls.is_over_18)
    over18_cb = ttk.Checkbutton(
        content, text="I confirm I am 18 or older",
        variable=over18_var,
    )
    over18_cb.grid(row=r, column=0, columnspan=3, sticky="w")
    r += 1

    # ── 5. Privacy Settings (Issues #65, #79, #114) ─────────────────
    r = _section(content, "🔒  Privacy", r)

    telemetry_var = tk.BooleanVar(value=getattr(config, 'TELEMETRY_ENABLED', False))
    telemetry_cb = ttk.Checkbutton(
        content, text="Allow anonymous usage data",
        variable=telemetry_var,
    )
    telemetry_cb.grid(row=r, column=0, columnspan=3, sticky="w")
    r += 1

    telemetry_hint = ttk.Label(
        content,
        text="Collects anonymous stats (app version, feature usage, crash reports).\n"
             "No personal info, channel names, or URLs are ever sent.",
        font=FONT_SMALL, foreground=CD.TEXT_SECONDARY,
        wraplength=440, justify="left",
    )
    telemetry_hint.grid(row=r, column=0, columnspan=3, sticky="w", padx=(18, 0))
    r += 1

    # ── 6. Support the Project ─────────────────────────────────────
    r = _section(content, "🍺  Support the Project", r)

    import webbrowser as _webbrowser

    # Warm amber/gold colors for the support section
    _AMBER = "#F59E0B"
    _AMBER_DARK = "#D97706"
    _GOLD = "#FBBF24"

    support_hint = ttk.Label(
        content,
        text="If you enjoy TV Viewer, consider buying the developer a beer!",
        font=FONT_SMALL, foreground=_GOLD,
        wraplength=440, justify="left",
    )
    support_hint.grid(row=r, column=0, columnspan=3, sticky="w", pady=(0, 8))
    r += 1

    support_btn_frame = ttk.Frame(content)
    support_btn_frame.grid(row=r, column=0, columnspan=3, sticky="w", pady=(0, 4))

    beer_btn = tk.Button(
        support_btn_frame,
        text="🍺 Buy Me a Beer",
        font=("Segoe UI", 11, "bold"),
        bg=_AMBER, fg="#1E1E1E",
        activebackground=_AMBER_DARK, activeforeground="#FFFFFF",
        relief="flat", borderwidth=0, cursor="hand2",
        padx=14, pady=6,
        command=lambda: _webbrowser.open("https://ko-fi.com/tvviewer"),
    )
    beer_btn.pack(side="left")

    request_btn = tk.Button(
        support_btn_frame,
        text="📺 Request Channels",
        font=("Segoe UI", 10),
        bg="#1E3A5F", fg="#58A6FF",
        activebackground="#264F78", activeforeground="#79C0FF",
        relief="flat", borderwidth=0, cursor="hand2",
        padx=14, pady=6,
        command=lambda: _webbrowser.open(
            "https://github.com/tv-viewer-app/tv_viewer/issues/new?template=channel_request.yml"
        ),
    )
    request_btn.pack(side="left", padx=(12, 0))
    r += 1

    # ── Bottom button bar ────────────────────────────────────────────
    btn_bar = ttk.Frame(dlg, padding=(18, 8))
    btn_bar.pack(fill="x", side="bottom")

    def _save():
        """Persist all settings and apply in-memory."""
        # -- Stream settings -- apply to config module --
        try:
            config.STREAM_CHECK_TIMEOUT = max(1, min(30, stream_timeout_var.get()))
        except (tk.TclError, ValueError):
            pass
        try:
            config.MAX_CONCURRENT_CHECKS = max(1, min(100, max_concurrent_var.get()))
        except (tk.TclError, ValueError):
            pass
        try:
            config.REQUEST_TIMEOUT = max(5, min(60, request_timeout_var.get()))
        except (tk.TclError, ValueError):
            pass
        try:
            config.SCAN_BATCH_SIZE = max(50, min(1000, batch_size_var.get()))
        except (tk.TclError, ValueError):
            pass

        # -- Repositories -- write to channels_config.json --
        new_repos = list(repo_listbox.get(0, tk.END))
        try:
            save_data = dict(cfg_data)  # preserve custom_channels etc.
            save_data['repositories'] = new_repos
            with open(config_path, 'w', encoding='utf-8') as f:
                _json.dump(save_data, f, indent=2, ensure_ascii=False)
            # Update in-memory repos
            config.IPTV_REPOSITORIES = new_repos
            logger.info(f"Settings: saved {len(new_repos)} repos to {config_path}")
        except Exception as e:
            logger.error(f"Settings: failed to save repos: {e}")
            messagebox.showerror("Save Failed", 
                "Could not save repository settings. Please check that the configuration file is writable.",
                parent=dlg)
            return

        # -- Display settings --
        new_group = group_mode_var.get()
        if new_group.lower() != parent_window.group_by_mode:
            parent_window._on_group_by_change(new_group)
            parent_window.group_by_var.set(new_group)

        new_theme = theme_var.get()
        if new_theme != current_theme:
            try:
                parent_window.root.style.theme_use(new_theme)
                logger.info(f"Settings: theme changed to {new_theme}")
            except Exception as e:
                logger.warning(f"Settings: failed to apply theme: {e}")

        # -- Parental controls --
        parent_window.parental_controls.enabled = parental_enabled_var.get()
        new_blocked = [cat for cat, var in cat_vars.items() if var.get()]
        parent_window.parental_controls.set_blocked_categories(new_blocked)
        parent_window.parental_controls.set_over_18(bool(over18_var.get()))
        parent_window.parental_controls.save()
        # Re-filter to apply parental control changes immediately
        if parent_window.current_group:
            parent_window.root.after(50, lambda: parent_window._select_group(parent_window.current_group))

        # -- Privacy / Telemetry (Issues #65, #79, #114) --
        new_telemetry = telemetry_var.get()
        if new_telemetry != getattr(config, 'TELEMETRY_ENABLED', False):
            parent_window._save_telemetry_preference(new_telemetry)
            logger.info(f"Settings: telemetry {'enabled' if new_telemetry else 'disabled'}")

        _on_close()
        logger.info("Settings saved successfully")

    def _reset():
        """Reset all fields to defaults."""
        stream_timeout_var.set(5)
        max_concurrent_var.set(30)
        request_timeout_var.set(15)
        batch_size_var.set(200)
        group_mode_var.set("Category")
        theme_var.set("darkly")
        telemetry_var.set(False)
        # Reset repo list to defaults
        repo_listbox.delete(0, tk.END)
        for url in default_repos:
            repo_listbox.insert(tk.END, url)
        _update_repo_count()

    ttk.Button(btn_bar, text="Reset to Defaults", command=_reset,
               bootstyle="warning-outline", width=16
               ).pack(side="left")
    ttk.Button(btn_bar, text="Cancel", command=_on_close,
               bootstyle="secondary", width=10
               ).pack(side="right", padx=(4, 0))
    ttk.Button(btn_bar, text="Save", command=_save,
               bootstyle="primary", width=10
               ).pack(side="right")
