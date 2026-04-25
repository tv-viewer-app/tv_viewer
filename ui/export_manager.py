"""M3U playlist export functionality.

Extracted from MainWindow._export_m3u to reduce the size of main_window.py.
All references to `self` have been replaced with `parent_window` (the MainWindow instance).
"""

import time
from tkinter import filedialog

from utils.logger import get_logger

logger = get_logger(__name__)


def export_m3u(parent_window):
    """Export all channels as M3U playlist file.

    Args:
        parent_window: The MainWindow instance (needed for channel_manager, toast).
    """
    # Get all working channels
    channels = parent_window.channel_manager.get_all_channels()
    working_channels = [ch for ch in channels if ch.get('is_working', False)]

    if not working_channels:
        parent_window.toast.show_warning("No working channels to export. Run a scan first.")
        return

    # Ask for save location
    filepath = filedialog.asksaveasfilename(
        title="Export M3U Playlist",
        defaultextension=".m3u",
        filetypes=[("M3U Playlist", "*.m3u"), ("M3U8 Playlist", "*.m3u8"), ("All Files", "*.*")],
        initialfile="tv_channels.m3u"
    )

    if not filepath:
        return

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"# TV Viewer Export - {len(working_channels)} channels\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for ch in working_channels:
                name = ch.get('name', 'Unknown')
                url = ch.get('url', '')
                category = ch.get('category', 'Other')
                logo = ch.get('logo', '')
                country = ch.get('country', '')

                if not url:
                    continue

                # Build EXTINF line with attributes
                extinf = f'#EXTINF:-1 tvg-name="{name}"'
                if category:
                    extinf += f' group-title="{category}"'
                if logo:
                    extinf += f' tvg-logo="{logo}"'
                if country:
                    extinf += f' tvg-country="{country}"'
                extinf += f',{name}\n'

                f.write(extinf)
                f.write(f'{url}\n')

        parent_window.toast.show_success(f"Exported {len(working_channels)} channels")
        logger.info(f"Exported {len(working_channels)} channels to {filepath}")

    except Exception as e:
        parent_window.toast.show_error(f"Export failed: {e}")
        logger.error(f"Export failed: {e}")
