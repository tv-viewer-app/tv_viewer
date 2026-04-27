"""Diagnostics / Stream Tester dialog for TV Viewer.

Provides device information, network diagnostics, a stream URL tester,
and a report generator — matching the Flutter app's diagnostics screen.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import platform
import sys
import os
import time
import threading

from .constants import FluentColorsDark as FluentColors
from .tooltip import add_tooltip
import config
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import icon module
try:
    from icon import set_window_icon
except ImportError:
    set_window_icon = None


def _get_vlc_version() -> str:
    """Return installed VLC version or 'Not installed'."""
    try:
        import vlc
        return vlc.libvlc_get_version().decode() if isinstance(
            vlc.libvlc_get_version(), bytes
        ) else str(vlc.libvlc_get_version())
    except Exception:
        return "Not installed"


def _get_screen_resolution(parent) -> str:
    """Return screen resolution string."""
    try:
        return f"{parent.winfo_screenwidth()}x{parent.winfo_screenheight()}"
    except Exception:
        return "Unknown"


def _check_internet() -> tuple:
    """Check internet connectivity. Returns (ok: bool, latency_ms: float, error: str)."""
    import requests
    try:
        start = time.time()
        resp = requests.head("https://www.google.com", timeout=5)
        latency = (time.time() - start) * 1000
        return True, latency, ""
    except Exception as e:
        return False, 0, str(e)


def _check_dns() -> tuple:
    """Check DNS resolution. Returns (ok: bool, ip: str, error: str)."""
    import socket
    try:
        ip = socket.gethostbyname("www.google.com")
        return True, ip, ""
    except Exception as e:
        return False, "", str(e)


def _test_stream_url(url: str) -> dict:
    """Test a stream URL. Returns result dict."""
    import requests
    result = {
        'url': url,
        'status_code': None,
        'content_type': None,
        'response_time_ms': None,
        'error': None,
    }
    try:
        start = time.time()
        resp = requests.head(url, timeout=10, allow_redirects=True)
        elapsed = (time.time() - start) * 1000
        result['status_code'] = resp.status_code
        result['content_type'] = resp.headers.get('Content-Type', 'N/A')
        result['response_time_ms'] = round(elapsed, 1)
    except Exception as e:
        result['error'] = str(e)
    return result


def show_diagnostics_dialog(parent_window):
    """Show the diagnostics dialog.

    Args:
        parent_window: The parent Tk widget (root or MainWindow.root).
    """
    # Resolve to actual Tk root
    root = parent_window if isinstance(parent_window, (tk.Tk, tk.Toplevel)) else getattr(parent_window, 'root', parent_window)

    dlg = tk.Toplevel(root)
    dlg.title("Diagnostics — Stream Tester")
    dlg.geometry("620x660")
    dlg.resizable(True, True)
    dlg.transient(root)
    dlg.grab_set()
    dlg.minsize(500, 500)

    if set_window_icon:
        set_window_icon(dlg)

    # Center
    dlg.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - 620) // 2
    y = root.winfo_y() + (root.winfo_height() - 660) // 2
    dlg.geometry(f"+{max(0, x)}+{max(0, y)}")

    FONT = ("Segoe UI", 10)
    FONT_BOLD = ("Segoe UI", 10, "bold")
    FONT_SECTION = ("Segoe UI", 13, "bold")
    FONT_MONO = ("Consolas", 10)

    # Scrollable container
    from ttkbootstrap.widgets.scrolled import ScrolledFrame
    scroll = ScrolledFrame(dlg, autohide=True)
    scroll.pack(fill="both", expand=True, padx=12, pady=12)

    report_lines = []  # accumulate report text

    # ── Device Info ──────────────────────────────────────────────────
    ttk.Label(scroll, text="🖥 Device Info", font=FONT_SECTION,
              foreground=FluentColors.ACCENT).pack(anchor="w", pady=(0, 6))

    device_frame = ttk.Frame(scroll)
    device_frame.pack(fill="x", pady=(0, 12))

    device_info = {
        "OS": f"{platform.system()} {platform.release()} ({platform.version()})",
        "Python": f"{sys.version.split()[0]}",
        "VLC": _get_vlc_version(),
        "Screen": _get_screen_resolution(root),
        "App Version": config.APP_VERSION,
    }
    report_lines.append("=== Device Info ===")
    for i, (label, value) in enumerate(device_info.items()):
        ttk.Label(device_frame, text=f"{label}:", font=FONT_BOLD).grid(
            row=i, column=0, sticky="w", padx=(0, 12), pady=1)
        ttk.Label(device_frame, text=value, font=FONT).grid(
            row=i, column=1, sticky="w", pady=1)
        report_lines.append(f"{label}: {value}")

    # ── Network ──────────────────────────────────────────────────────
    ttk.Separator(scroll).pack(fill="x", pady=8)
    ttk.Label(scroll, text="🌐 Network", font=FONT_SECTION,
              foreground=FluentColors.ACCENT).pack(anchor="w", pady=(0, 6))

    net_frame = ttk.Frame(scroll)
    net_frame.pack(fill="x", pady=(0, 12))

    inet_label = ttk.Label(net_frame, text="Internet: checking…", font=FONT)
    inet_label.grid(row=0, column=0, sticky="w", pady=2)
    dns_label = ttk.Label(net_frame, text="DNS: checking…", font=FONT)
    dns_label.grid(row=1, column=0, sticky="w", pady=2)

    report_lines.append("\n=== Network ===")

    def _run_network_checks():
        inet_ok, inet_ms, inet_err = _check_internet()
        dns_ok, dns_ip, dns_err = _check_dns()

        def _update():
            if inet_ok:
                inet_label.configure(
                    text=f"Internet: ✓ Connected ({inet_ms:.0f} ms)",
                    foreground=FluentColors.SUCCESS)
                report_lines.append(f"Internet: Connected ({inet_ms:.0f} ms)")
            else:
                inet_label.configure(
                    text=f"Internet: ✗ Failed — {inet_err}",
                    foreground=FluentColors.ERROR)
                report_lines.append(f"Internet: Failed — {inet_err}")
            if dns_ok:
                dns_label.configure(
                    text=f"DNS: ✓ Resolved (google.com → {dns_ip})",
                    foreground=FluentColors.SUCCESS)
                report_lines.append(f"DNS: Resolved (google.com → {dns_ip})")
            else:
                dns_label.configure(
                    text=f"DNS: ✗ Failed — {dns_err}",
                    foreground=FluentColors.ERROR)
                report_lines.append(f"DNS: Failed — {dns_err}")

        try:
            dlg.after(0, _update)
        except Exception:
            pass

    threading.Thread(target=_run_network_checks, daemon=True).start()

    # ── Stream Tester ────────────────────────────────────────────────
    ttk.Separator(scroll).pack(fill="x", pady=8)
    ttk.Label(scroll, text="📡 Stream Tester", font=FONT_SECTION,
              foreground=FluentColors.ACCENT).pack(anchor="w", pady=(0, 6))

    test_frame = ttk.Frame(scroll)
    test_frame.pack(fill="x", pady=(0, 6))
    test_frame.columnconfigure(0, weight=1)

    url_var = tk.StringVar()
    url_entry = ttk.Entry(test_frame, textvariable=url_var, font=FONT_MONO)
    url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
    url_entry.insert(0, "https://")
    add_tooltip(url_entry, "Enter a stream URL to test connectivity")

    test_btn = ttk.Button(test_frame, text="Test", bootstyle="primary", width=8)
    test_btn.grid(row=0, column=1, sticky="e")

    result_text = tk.Text(
        scroll, height=6, font=FONT_MONO, wrap="word",
        relief="flat", state="disabled",
        background=FluentColors.BG_CARD,
        foreground=FluentColors.TEXT_PRIMARY,
    )
    result_text.pack(fill="x", pady=(4, 12))

    def _on_test():
        url = url_var.get().strip()
        if not url or url == "https://":
            return
        test_btn.configure(state="disabled", text="…")
        result_text.configure(state="normal")
        result_text.delete("1.0", "end")
        result_text.insert("1.0", f"Testing {url}…\n")
        result_text.configure(state="disabled")

        def _do():
            res = _test_stream_url(url)

            def _show():
                result_text.configure(state="normal")
                result_text.delete("1.0", "end")
                if res['error']:
                    result_text.insert("1.0", f"❌ Error: {res['error']}\n")
                    report_lines.append(f"\nStream test ({url}): Error — {res['error']}")
                else:
                    lines = [
                        f"✅ Status: {res['status_code']}",
                        f"   Content-Type: {res['content_type']}",
                        f"   Response time: {res['response_time_ms']} ms",
                    ]
                    result_text.insert("1.0", "\n".join(lines) + "\n")
                    report_lines.append(
                        f"\nStream test ({url}): {res['status_code']} "
                        f"({res['content_type']}, {res['response_time_ms']} ms)")
                result_text.configure(state="disabled")
                test_btn.configure(state="normal", text="Test")

            try:
                dlg.after(0, _show)
            except Exception:
                pass

        threading.Thread(target=_do, daemon=True).start()

    test_btn.configure(command=_on_test)
    url_entry.bind("<Return>", lambda e: _on_test())

    # ── Report ───────────────────────────────────────────────────────
    ttk.Separator(scroll).pack(fill="x", pady=8)
    ttk.Label(scroll, text="📋 Report", font=FONT_SECTION,
              foreground=FluentColors.ACCENT).pack(anchor="w", pady=(0, 6))

    report_btn_frame = ttk.Frame(scroll)
    report_btn_frame.pack(fill="x", pady=(0, 4))

    report_output = tk.Text(
        scroll, height=6, font=FONT_MONO, wrap="word",
        relief="flat", state="disabled",
        background=FluentColors.BG_CARD,
        foreground=FluentColors.TEXT_PRIMARY,
    )
    report_output.pack(fill="x", pady=(4, 8))

    def _generate_report():
        header = f"TV Viewer Diagnostics Report — {time.strftime('%Y-%m-%d %H:%M:%S')}"
        full = header + "\n" + "=" * len(header) + "\n\n" + "\n".join(report_lines)
        report_output.configure(state="normal")
        report_output.delete("1.0", "end")
        report_output.insert("1.0", full)
        report_output.configure(state="disabled")

    def _copy_report():
        _generate_report()
        text = report_output.get("1.0", "end").strip()
        dlg.clipboard_clear()
        dlg.clipboard_append(text)
        copy_btn.configure(text="✓ Copied!")
        try:
            dlg.after(2000, lambda: copy_btn.configure(text="📋 Copy"))
        except tk.TclError:
            pass

    def _save_report():
        _generate_report()
        text = report_output.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(
            parent=dlg,
            title="Save Diagnostics Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"tv_viewer_diagnostics_{time.strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
            except Exception as e:
                logger.error(f"Failed to save diagnostics report: {e}")

    ttk.Button(report_btn_frame, text="Generate Report",
               command=_generate_report, bootstyle="info-outline").pack(side="left", padx=(0, 6))
    copy_btn = ttk.Button(report_btn_frame, text="📋 Copy",
                          command=_copy_report, bootstyle="secondary")
    copy_btn.pack(side="left", padx=(0, 6))
    ttk.Button(report_btn_frame, text="💾 Save",
               command=_save_report, bootstyle="secondary").pack(side="left")

    # ── Close ────────────────────────────────────────────────────────
    ttk.Button(scroll, text="Close", command=dlg.destroy,
               bootstyle="secondary", width=10).pack(anchor="e", pady=(8, 0))
