"""Video player window with embedded controls and Windows 11 Fluent Design.

This module provides an embedded video player using VLC with hardware acceleration
and optimized resource management.

Hardware Acceleration:
- Windows: Direct3D11 (d3d11va) or DXVA2 for GPU-accelerated decoding
- Linux: VAAPI or VDPAU for GPU-accelerated decoding  
- macOS: VideoToolbox for GPU-accelerated decoding

Memory Optimization:
- Proper resource cleanup on window close
- Thumbnail image caching with size limits
- Garbage collection triggers after heavy operations

Threading:
- VLC runs on its own thread (handled by libvlc)
- UI updates use tkinter's after() for thread safety
- Cast discovery runs in background thread
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import subprocess
import threading
import gc
import logging
from typing import Optional, Dict, Any, List, Callable

from utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

# VLC controller (handles vlc import internally)
from ui.vlc_controller import VLCController, VLC_AVAILABLE

# Import vlc for State constants used in playback logic
try:
    import vlc
except ImportError:
    vlc = None

# Try to import pychromecast for Google Cast
try:
    import pychromecast
    CAST_AVAILABLE = True
except ImportError:
    CAST_AVAILABLE = False
    logger.info("pychromecast not installed. Casting will not be available.")

import config
from utils.helpers import format_duration
from utils.telemetry import track_channel_fail, track_feature
from ui.constants import FluentColors, FluentSpacing
from ui.tooltip import add_tooltip


class PlayerWindow(tk.Toplevel):
    """Separate window for video playback with controls."""
    
    def __init__(self, parent, channel: Dict[str, Any],
                 channel_list: Optional[List[Dict[str, Any]]] = None,
                 channel_index: Optional[int] = None,
                 on_channel_change: Optional[Callable] = None):
        super().__init__(parent)
        
        self.channel = channel
        self.parent = parent
        self.channel_list = channel_list
        self.channel_index = channel_index
        self._on_channel_change = on_channel_change
        self.vlc = VLCController()
        self.is_playing = False
        self._update_job = None
        self._quality_update_job = None
        self._playback_confirmed = False  # True once VLC confirms video data received
        
        # Callback fired once when VLC confirms playback is working
        self.on_playback_confirmed: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Preloading: pre-buffers the next channel via VLCController
        self._preload_index: Optional[int] = None  # channel_list index being preloaded
        self._preload_job = None  # after() ID for scheduling preload
        
        # Cast-related
        self.cast_devices: List[Any] = []
        self.active_cast = None
        self.cast_browser = None
        
        self._setup_window()
        self._create_widgets()
        
        if self.vlc.is_available:
            self._init_vlc()
            self.play()
        else:
            self._show_vlc_error()
    
    def _setup_window(self):
        """Configure the window properties."""
        channel_name = self.channel.get('name', 'Unknown Channel')
        self.title(f"{config.APP_NAME} - {channel_name}")
        self.geometry(f"{config.PLAYER_WIDTH}x{config.PLAYER_HEIGHT}")
        self.minsize(400, 300)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Make window resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
    
    def _create_widgets(self):
        """Create the player UI components with Windows 11 Fluent Design."""
        # Configure window background
        self.configure(bg=FluentColors.BG_SOLID)
        
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        
        # Video frame (where VLC will render)
        self.video_frame = ttk.Frame(self.main_frame)
        self.video_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create a canvas for video (needed for VLC on some platforms)
        self.video_canvas = tk.Canvas(
            self.video_frame, 
            bg='black',
            highlightthickness=0
        )
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Controls frame with Fluent Design
        self.controls_frame = ttk.Frame(
            self.main_frame,
            height=60
        )
        self.controls_frame.grid(row=1, column=0, sticky="ew")
        self.controls_frame.grid_propagate(False)
        
        # Play/Pause button - Windows 11 style
        self.play_btn = ttk.Button(
            self.controls_frame,
            text="⏸",
            width=4,
            command=self._toggle_play,
            bootstyle="primary"
        )
        self.play_btn.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_LARGE, pady=8)
        add_tooltip(self.play_btn, "Play/Pause (Space)")
        
        # Stop button
        self.stop_btn = ttk.Button(
            self.controls_frame,
            text="⏹",
            width=4,
            command=self.stop,
            bootstyle="secondary"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_SMALL)
        add_tooltip(self.stop_btn, "Stop playback")
        
        # Previous channel button
        if self.channel_list and len(self.channel_list) > 1:
            self.prev_btn = ttk.Button(
                self.controls_frame,
                text="⏮",
                width=3,
                command=self._previous_channel,
                bootstyle="secondary",
                state="normal" if self.channel_index and self.channel_index > 0 else "disabled"
            )
            self.prev_btn.pack(side=tk.LEFT, padx=2)
            add_tooltip(self.prev_btn, "Previous channel")
            
            # Next channel button
            self.next_btn = ttk.Button(
                self.controls_frame,
                text="⏭",
                width=3,
                command=self._next_channel,
                bootstyle="secondary",
                state="normal" if self.channel_index is not None and self.channel_index < len(self.channel_list) - 1 else "disabled"
            )
            self.next_btn.pack(side=tk.LEFT, padx=2)
            add_tooltip(self.next_btn, "Next channel")
        
        # Time label
        self.time_label = ttk.Label(
            self.controls_frame,
            text="00:00",
            width=8,
            font=("Segoe UI", 14)
        )
        self.time_label.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_LARGE)
        
        # Volume controls
        volume_frame = ttk.Frame(self.controls_frame)
        volume_frame.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_LARGE)
        
        ttk.Label(volume_frame, text="🔊", font=("Segoe UI", 14)).pack(side=tk.LEFT)
        
        self.volume_var = tk.IntVar(value=80)
        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            variable=self.volume_var,
            command=self._on_volume_change,
            orient="horizontal",
            length=120
        )
        self.volume_slider.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_MEDIUM)
        add_tooltip(self.volume_slider, "Adjust volume")
        
        # Volume percentage label
        self.volume_label = ttk.Label(
            volume_frame,
            text="80%",
            width=4,
            font=("Segoe UI", 12)
        )
        self.volume_label.pack(side=tk.LEFT, padx=2)
        
        # Mute button
        self.mute_btn = ttk.Button(
            volume_frame,
            text="🔇",
            width=3,
            command=self._toggle_mute,
            bootstyle="secondary"
        )
        self.mute_btn.pack(side=tk.LEFT)
        add_tooltip(self.mute_btn, "Mute/Unmute (M)")
        
        # Fullscreen button
        self.fullscreen_btn = ttk.Button(
            self.controls_frame,
            text="⛶",
            width=3,
            command=self._toggle_fullscreen,
            bootstyle="secondary"
        )
        self.fullscreen_btn.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_SMALL)
        add_tooltip(self.fullscreen_btn, "Fullscreen (F) - Press ESC to exit")
        
        # Open in VLC button
        self.vlc_btn = ttk.Button(
            self.controls_frame,
            text="VLC",
            width=4,
            command=self._open_in_external_vlc,
            bootstyle="secondary"
        )
        self.vlc_btn.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_SMALL)
        add_tooltip(self.vlc_btn, "Open in external VLC player")
        
        # Cast button (if available)
        if CAST_AVAILABLE:
            self.cast_btn = ttk.Button(
                self.controls_frame,
                text="📺",
                width=3,
                command=self._show_cast_menu,
                bootstyle="secondary"
            )
            self.cast_btn.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_SMALL)
            add_tooltip(self.cast_btn, "Cast to TV/Chromecast")
        
        # Report broken channel button
        self._report_sent = False  # Debounce: one report per session
        self.report_btn = ttk.Button(
            self.controls_frame,
            text="🔴",
            width=3,
            command=self._report_broken,
            bootstyle="danger-outline"
        )
        self.report_btn.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_SMALL)
        add_tooltip(self.report_btn, "Report channel as broken")
        
        # Channel info
        channel_name = self.channel.get('name', 'Unknown')
        self.channel_label = ttk.Label(
            self.controls_frame,
            text=channel_name,
            font=("Segoe UI", 13, "bold")
        )
        self.channel_label.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_XLARGE)
        
        # Source selector (when multiple URLs available)
        urls = self.channel.get('urls', [])
        if len(urls) > 1:
            src_frame = ttk.Frame(self.controls_frame)
            src_frame.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_SMALL)
            ttk.Label(src_frame, text="Source:", font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=2)
            self._source_var = tk.StringVar()
            source_labels = [f"#{i+1}" for i in range(len(urls))]
            current_idx = self.channel.get('working_url_index', 0)
            self._source_var.set(source_labels[min(current_idx, len(source_labels)-1)])
            self._source_combo = ttk.Combobox(
                src_frame,
                textvariable=self._source_var,
                values=source_labels,
                width=5,
                state="readonly",
                font=("Segoe UI", 10)
            )
            self._source_combo.pack(side=tk.LEFT, padx=2)
            self._source_combo.bind('<<ComboboxSelected>>', self._on_source_selected)
            add_tooltip(self._source_combo, f"{len(urls)} stream sources available")
        
        # Quality info frame (below controls)
        self.quality_frame = ttk.Frame(
            self.main_frame,
            height=28
        )
        self.quality_frame.grid(row=2, column=0, sticky="ew")
        self.quality_frame.grid_propagate(False)
        
        self.quality_label = ttk.Label(
            self.quality_frame,
            text="Quality: --",
            font=("Segoe UI", 11)
        )
        self.quality_label.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_LARGE, pady=4)
        
        # Bind keyboard shortcuts
        self.bind('<space>', lambda e: self._toggle_play())
        self.bind('<Escape>', lambda e: self._exit_fullscreen())
        self.bind('f', lambda e: self._toggle_fullscreen())
        self.bind('m', lambda e: self._toggle_mute())
        self.bind('<Up>', lambda e: self._volume_up())
        self.bind('<Down>', lambda e: self._volume_down())
        self.bind('<Right>', lambda e: self._next_channel())
        self.bind('<Left>', lambda e: self._prev_channel())
        
        # Double-click for fullscreen
        self.video_canvas.bind('<Double-Button-1>', lambda e: self._toggle_fullscreen())
    
    def _init_vlc(self):
        """Initialize VLC player with fallback to minimal settings (Issue #35).
        
        Tries optimized settings first, falls back to minimal settings if needed.
        """
        if not self.vlc.initialize(self.video_canvas.winfo_id(), self.volume_var.get()):
            self._show_vlc_error()
    
    def _show_vlc_error(self):
        """Show error message when VLC is not available with specific diagnostics (Issue #33)."""
        import webbrowser
        import shutil
        
        # Detect what's missing (Issue #33)
        vlc_binary_exists = shutil.which('vlc') is not None
        python_vlc_exists = VLC_AVAILABLE
        
        # Determine specific error
        if not vlc_binary_exists and not python_vlc_exists:
            title = "⚠️ VLC Not Installed"
            message = "Both VLC media player and python-vlc are missing."
            install_cmd = "sudo apt-get install vlc\npip3 install python-vlc"
            show_download_btn = True
        elif not python_vlc_exists:
            title = "⚠️ python-vlc Not Installed"
            message = "VLC is installed, but python-vlc package is missing."
            install_cmd = "pip3 install python-vlc"
            show_download_btn = False
        else:
            title = "⚠️ VLC Configuration Error"
            message = "VLC installation detected but player initialization failed."
            install_cmd = "pip3 install --force-reinstall python-vlc"
            show_download_btn = False
        
        error_frame = ttk.Frame(self.video_canvas)
        error_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        ttk.Label(
            error_frame,
            text=title,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 10), padx=30)
        
        ttk.Label(
            error_frame,
            text=message,
            font=("Segoe UI", 12),
            justify="center"
        ).pack(pady=5, padx=30)
        
        # Installation command
        ttk.Label(
            error_frame,
            text=install_cmd,
            font=("Courier New", 11),
            justify="center"
        ).pack(pady=(10, 20), padx=30)
        
        # Buttons frame
        btn_frame = ttk.Frame(error_frame)
        btn_frame.pack(pady=(15, 20))
        
        # Download VLC button (only if VLC binary missing)
        if show_download_btn:
            def open_vlc_download():
                webbrowser.open("https://www.videolan.org/vlc/")
            
            ttk.Button(
                btn_frame,
                text="Download VLC",
                width=15,
                command=open_vlc_download,
                bootstyle="primary"
            ).pack(side=tk.LEFT, padx=5)
        
        # Retry button
        ttk.Button(
            btn_frame,
            text="Retry",
            width=10,
            command=lambda: [error_frame.destroy(), self._init_vlc(), self.play() if self.vlc.player else None],
            bootstyle="secondary"
        ).pack(side=tk.LEFT, padx=5)
    
    def play(self):
        """Start playing the stream with multi-URL fallback."""
        if not self.vlc.is_available or not self.vlc.player:
            return
        
        # Get URL list (multi-URL support)
        urls = self.channel.get('urls', [])
        if not urls:
            single_url = self.channel.get('url', '')
            urls = [single_url] if single_url else []
        
        if not urls:
            return
        
        # Start from the working URL index
        start_idx = self.channel.get('working_url_index', 0)
        if start_idx >= len(urls):
            start_idx = 0
        
        # Reorder URLs to try working one first
        ordered_urls = urls[start_idx:] + urls[:start_idx]
        
        for idx, url in enumerate(ordered_urls):
            if not url:
                continue
            
            # Security: Validate URL scheme
            url_lower = url.lower()
            allowed_schemes = ('http://', 'https://', 'rtmp://', 'rtsp://', 'mms://')
            if not url_lower.startswith(allowed_schemes):
                continue
            
            # Security: Block dangerous schemes
            if url_lower.startswith(('file://', 'javascript:', 'data:')):
                continue
            
            try:
                if not self.vlc.play_url(url):
                    logger.warning(f"Failed to create media for URL {idx}: {url[:60]}")
                    continue
                self.is_playing = True
                self.play_btn.configure(text="⏸")
                
                # Update channel with working URL
                actual_idx = (start_idx + idx) % len(urls)
                self.channel['url'] = url
                self.channel['working_url_index'] = actual_idx
                self.channel['is_working'] = True
                
                # Report health
                self._report_channel_health(url, True)
                
                # Start updating time display
                self._update_time()
                
                # Start updating quality info (with delay to let stream start)
                self.after(2000, self._update_quality_info)
                
                # Monitor playback health after 5 seconds
                self.after(5000, lambda: self._check_playback_health(url))
                
                return
                
            except Exception as e:
                logger.warning(f"Failed to play URL {idx}: {e}")
                self._report_channel_health(url, False, str(e))
                continue
        
        # All URLs failed
        self.channel['is_working'] = False
        track_channel_fail(self.channel, 'all_urls_failed')
        logger.error(f"All URLs failed for channel: {self.channel.get('name', '?')}")
        messagebox.showerror("Stream Unavailable", 
            "Unable to play this channel. All stream URLs failed to load.\n\n"
            "The channel may be offline or experiencing technical issues.")
    
    def _check_playback_health(self, url: str):
        """Check if playback is actually working after a few seconds."""
        if not self.vlc.player:
            return
        state = self.vlc.get_state()
        if state in (vlc.State.Error, vlc.State.Ended):
            self.channel['is_working'] = False
            self._report_channel_health(url, False, f"state={state}")
            # Try next URL
            self._try_next_url()
        elif state == vlc.State.Playing:
            self.channel['is_working'] = True
    
    def _try_next_url(self):
        """Try the next URL in the channel's URL list."""
        urls = self.channel.get('urls', [])
        if len(urls) <= 1:
            return
        current_idx = self.channel.get('working_url_index', 0)
        next_idx = (current_idx + 1) % len(urls)
        if next_idx == current_idx:
            return
        self.channel['working_url_index'] = next_idx
        logger.info(f"Trying fallback URL {next_idx} for {self.channel.get('name', '?')}")
        self.play()
    
    def _on_source_selected(self, event=None):
        """User selected a different stream source from the combo."""
        if not hasattr(self, '_source_var'):
            return
        selected = self._source_var.get()
        try:
            idx = int(selected.replace('#', '')) - 1
        except (ValueError, AttributeError):
            return
        urls = self.channel.get('urls', [])
        if idx < 0 or idx >= len(urls) or idx == self.channel.get('working_url_index', 0):
            return
        logger.info(f"User selected source #{idx+1} for {self.channel.get('name', '?')}")
        self.channel['working_url_index'] = idx
        self.play()
    
    def _previous_channel(self):
        """Switch to the previous channel in the list."""
        if not self.channel_list or self.channel_index is None or self.channel_index <= 0:
            return
        new_idx = self.channel_index - 1
        self._switch_channel(new_idx)
    
    def _next_channel(self):
        """Switch to the next channel in the list."""
        if not self.channel_list or self.channel_index is None:
            return
        if self.channel_index >= len(self.channel_list) - 1:
            return
        new_idx = self.channel_index + 1
        self._switch_channel(new_idx)
    
    def _switch_channel(self, new_index: int):
        """Switch to a different channel by index in the list.

        If the next channel was preloaded, swap the pre-buffered player in
        for near-instant playback.  Otherwise fall back to the normal
        stop → play flow.
        """
        if not self.channel_list or new_index < 0 or new_index >= len(self.channel_list):
            return

        # ── Bug #121: Cancel pending timers and reset stale state ──
        if self._update_job:
            self.after_cancel(self._update_job)
            self._update_job = None
        if self._quality_update_job:
            self.after_cancel(self._quality_update_job)
            self._quality_update_job = None
        if self._preload_job:
            self.after_cancel(self._preload_job)
            self._preload_job = None

        self._playback_confirmed = False
        self.quality_label.configure(text="Quality: --")
        self.time_label.configure(text="00:00")
        # ── End Bug #121 cleanup ──

        use_preload = (
            self.vlc.preload_player is not None
            and self._preload_index == new_index
        )

        if use_preload:
            # Swap preloaded player into the main slot
            logger.info(f"Using preloaded player for channel [{new_index}]")
            self.stop()

            # Resolve URL: prefer preload URL, fall back to channel URL
            url = self.vlc.preload_url or self._resolve_channel_url(self.channel_list[new_index])
            old_player, url = self.vlc.activate_preload(
                self.video_canvas.winfo_id(),
                self.volume_var.get(),
                url
            )
            self._preload_index = None

            self.is_playing = True
            self.play_btn.configure(text="⏸")
            self._playback_confirmed = False
            self._update_time()
            self.after(2000, self._update_quality_info)
            self.after(5000, lambda u=url: self._check_playback_health(u) if u else None)

            # Release old player
            VLCController.release_player(old_player)
        else:
            self.stop()
            self._release_preload()

        self.channel = self.channel_list[new_index]
        self.channel_index = new_index
        
        # Update window title
        channel_name = self.channel.get('name', 'Unknown Channel')
        self.title(f"{config.APP_NAME} - {channel_name}")
        
        # Update prev/next button states
        if hasattr(self, 'prev_btn'):
            self.prev_btn.configure(state="normal" if new_index > 0 else "disabled")
        if hasattr(self, 'next_btn'):
            self.next_btn.configure(
                state="normal" if new_index < len(self.channel_list) - 1 else "disabled")
        
        # Update source selector if present
        if hasattr(self, '_source_combo'):
            urls = self.channel.get('urls', [self.channel.get('url', '')])
            values = [f"#{i+1}" for i in range(len(urls))]
            self._source_combo.configure(values=values)
            widx = self.channel.get('working_url_index', 0)
            self._source_var.set(f"#{widx + 1}")
        
        logger.info(f"Switched to channel [{new_index}]: {channel_name}")

        if not use_preload:
            self.play()

        # Notify parent if callback provided
        if self._on_channel_change:
            try:
                self._on_channel_change(self.channel, new_index)
            except Exception as e:
                logger.debug(f"Channel change callback error: {e}")

        # Preload the *next* channel after this one
        self._schedule_preload()
    def _report_channel_health(self, url: str, is_working: bool, error: str = ""):
        """Report channel health to analytics and SharedDb (async-safe from UI thread)."""
        try:
            from utils.analytics import analytics
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(analytics.track_channel_health(
                    url=url,
                    is_working=is_working,
                    error_message=error,
                ))
            finally:
                loop.close()
        except Exception:
            pass  # Don't let analytics errors affect playback

        # Report failures to Supabase shared DB (fire-and-forget)
        if not is_working:
            try:
                from utils.shared_db import SharedDbService
                SharedDbService.report_channel_failure(url)
            except Exception:
                pass
    
    def _report_broken(self):
        """Report current channel as broken via Supabase. One report per player session."""
        if self._report_sent:
            from tkinter import messagebox
            messagebox.showinfo("Already Reported", "You already reported this channel.")
            return
        
        import hashlib as _hashlib
        # Use primary URL (urls[0]) for stable hash, fallback to current url
        urls = self.channel.get('urls', [])
        url = urls[0] if urls else self.channel.get('url', '')
        name = self.channel.get('name', 'Unknown')
        if not url:
            return
        
        url_hash = _hashlib.sha256(url.encode('utf-8')).hexdigest()
        self._report_sent = True
        self.report_btn.configure(state="disabled", text="✓")
        
        def _run():
            success = False
            try:
                import asyncio as _aio
                from utils.supabase_channels import report_channel, is_configured
                if is_configured():
                    loop = _aio.new_event_loop()
                    _aio.set_event_loop(loop)
                    try:
                        success = loop.run_until_complete(report_channel(url_hash))
                    finally:
                        loop.close()
            except Exception:
                pass
            
            def _ui_update():
                if success:
                    # Mark channel as not working locally
                    self.channel['is_working'] = False
                    self.channel['user_reported'] = True
                    self.channel['scan_status'] = 'scanned'
                    try:
                        from utils.analytics import track_feature
                        track_feature("channel_reported_broken")
                    except Exception:
                        pass
            
            self.after(0, _ui_update)
        
        import threading as _thr
        _thr.Thread(target=_run, daemon=True).start()
    
    def pause(self):
        """Pause playback."""
        if self.vlc.player:
            self.vlc.pause()
            self.is_playing = False
            self.play_btn.configure(text="▶")
    
    def stop(self):
        """Stop playback."""
        if self.vlc.player:
            self.vlc.stop()
            self.is_playing = False
            self.play_btn.configure(text="▶")
            self.time_label.configure(text="00:00")
    
    def _toggle_play(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self.pause()
        else:
            if self.vlc.player and self.vlc.get_state() == vlc.State.Paused:
                self.vlc.pause()  # Unpause
                self.is_playing = True
                self.play_btn.configure(text="⏸")
            else:
                self.play()
    
    def _toggle_mute(self):
        """Toggle audio mute."""
        if self.vlc.player:
            is_muted = self.vlc.get_mute()
            self.vlc.set_mute(not is_muted)
            self.mute_btn.configure(text="🔈" if not is_muted else "🔇")
    
    def _on_volume_change(self, value):
        """Handle volume slider change."""
        if self.vlc.player:
            volume = int(float(value))
            self.vlc.set_volume(volume)
            self.volume_label.configure(text=f"{volume}%")
    
    def _volume_up(self):
        """Increase volume by 5%."""
        current = self.volume_var.get()
        new_vol = min(100, current + 5)
        self.volume_var.set(new_vol)
        self._on_volume_change(new_vol)
    
    def _volume_down(self):
        """Decrease volume by 5%."""
        current = self.volume_var.get()
        new_vol = max(0, current - 5)
        self.volume_var.set(new_vol)
        self._on_volume_change(new_vol)
    
    def _prev_channel(self):
        """Switch to the previous channel in the list."""
        if not self.channel_list or self.channel_index is None:
            return
        if self.channel_index <= 0:
            return
        new_idx = self.channel_index - 1
        self._switch_channel(new_idx)

    # ── Channel preloading ──────────────────────────────────────────────

    def _schedule_preload(self):
        """Schedule preloading the next channel after current playback stabilises."""
        if self._preload_job:
            self.after_cancel(self._preload_job)
        # Wait 3 seconds after playback starts before preloading
        self._preload_job = self.after(3000, self._preload_next_channel)

    def _preload_next_channel(self):
        """Pre-buffer the next channel's stream in a hidden VLC player."""
        self._preload_job = None
        if not self.vlc.is_available or not self.vlc.instance:
            return
        if not self.channel_list or self.channel_index is None:
            return
        next_idx = self.channel_index + 1
        if next_idx >= len(self.channel_list):
            self._release_preload()
            return
        # Already preloading the right channel?
        if self._preload_index == next_idx and self.vlc.preload_player:
            return

        self._release_preload()

        next_ch = self.channel_list[next_idx]
        url = self._resolve_channel_url(next_ch)
        if not url:
            return

        if self.vlc.create_preload_player(url):
            self._preload_index = next_idx
            logger.info(f"Preloading channel [{next_idx}]: "
                        f"{next_ch.get('name', '?')}")

    def _release_preload(self):
        """Release the preloaded player resources."""
        self.vlc.release_preload()
        self._preload_index = None

    @staticmethod
    def _resolve_channel_url(channel: Dict[str, Any]) -> Optional[str]:
        """Return the best URL for a channel, or None."""
        urls = channel.get('urls', [])
        if not urls:
            single = channel.get('url', '')
            urls = [single] if single else []
        if not urls:
            return None
        idx = channel.get('working_url_index', 0)
        if idx >= len(urls):
            idx = 0
        url = urls[idx]
        if not url:
            return None
        allowed = ('http://', 'https://', 'rtmp://', 'rtsp://', 'mms://')
        if not url.lower().startswith(allowed):
            return None
        return url

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        is_fullscreen = self.attributes('-fullscreen')
        self.attributes('-fullscreen', not is_fullscreen)
        if not is_fullscreen:
            track_feature('fullscreen')
        
        if not is_fullscreen:
            # Hide controls in fullscreen
            self.controls_frame.grid_remove()
        else:
            self.controls_frame.grid()
    
    def _exit_fullscreen(self):
        """Exit fullscreen mode."""
        self.attributes('-fullscreen', False)
        self.controls_frame.grid()
    
    def _update_time(self):
        """Update the time display and detect confirmed playback."""
        if self.vlc.player and self.is_playing:
            try:
                time_ms = self.vlc.get_time()
                if time_ms > 0:
                    time_sec = time_ms // 1000
                    self.time_label.configure(text=format_duration(time_sec))
                    
                    # Confirm playback once we have actual video data
                    if not self._playback_confirmed and time_ms > 500:
                        self._playback_confirmed = True
                        if self.on_playback_confirmed and self.channel:
                            self.on_playback_confirmed(self.channel)
                        # Start preloading the next channel
                        self._schedule_preload()
            except (AttributeError, OSError):
                pass  # VLC instance may be closed
        
        # Schedule next update (every 2 seconds to reduce CPU)
        if self.winfo_exists():
            self._update_job = self.after(2000, self._update_time)
    
    def _update_quality_info(self):
        """Update video quality information display."""
        if not self.vlc.player or not self.is_playing:
            return
        
        try:
            if not self.vlc.has_media():
                return
            
            # Get video track info
            width = 0
            height = 0
            fps = 0.0
            bitrate = 0
            
            # Try to get video dimensions from player
            width, height = self.vlc.get_video_dimensions()
            
            # Get media stats for bitrate
            stats = self.vlc.get_media_stats()
            if stats:
                # Bitrate in bytes/sec, convert to kbps
                bitrate = int(stats.demux_bitrate * 8 / 1000) if stats.demux_bitrate > 0 else 0
            
            # Try to get FPS
            fps = self.vlc.get_fps()
            
            # Build quality string
            parts = []
            if width > 0 and height > 0:
                # Determine quality label
                if height >= 2160:
                    quality = "4K"
                elif height >= 1080:
                    quality = "FHD"
                elif height >= 720:
                    quality = "HD"
                elif height >= 480:
                    quality = "SD"
                else:
                    quality = "LD"
                parts.append(f"{width}x{height} ({quality})")
            
            if fps > 0:
                parts.append(f"{fps:.1f} fps")
            
            if bitrate > 0:
                if bitrate >= 1000:
                    parts.append(f"{bitrate/1000:.1f} Mbps")
                else:
                    parts.append(f"{bitrate} kbps")
            
            quality_text = "Quality: " + " | ".join(parts) if parts else "Quality: Loading..."
            self.quality_label.configure(text=quality_text)
            
        except Exception as e:
            logger.debug(f"Quality info update skipped: {e}")
        
        # Schedule next update (every 5 seconds to reduce CPU)
        if self.winfo_exists() and self.is_playing:
            self._quality_update_job = self.after(5000, self._update_quality_info)
    
    def _open_in_external_vlc(self):
        """Open the current stream in external VLC player and close embedded player."""
        url = self.channel.get('url', '')
        if not url:
            messagebox.showwarning("No URL", "No stream URL available.")
            return
        
        # Security: Validate URL scheme before subprocess execution
        from urllib.parse import urlparse
        parsed = urlparse(url)
        allowed_schemes = ('http', 'https', 'rtmp', 'rtsp', 'mms')
        if parsed.scheme.lower() not in allowed_schemes:
            messagebox.showerror("Invalid Stream URL", 
                f"This stream type ('{parsed.scheme}') is not supported.\n\n"
                "Only HTTP, HTTPS, RTMP, RTSP, and MMS streams are allowed.")
            return
        # Security: Block shell metacharacters in URLs
        import re
        if re.search(r'[;&|`$(){}!<>]', url):
            messagebox.showerror("Invalid Stream URL",
                "The stream URL contains invalid characters.")
            return
        
        try:
            vlc_launched = False
            
            if sys.platform == 'win32':
                # Try common VLC locations on Windows
                vlc_paths = [
                    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
                    os.path.expandvars(r"%PROGRAMFILES%\VideoLAN\VLC\vlc.exe"),
                ]
                vlc_exe = None
                for path in vlc_paths:
                    if os.path.exists(path):
                        vlc_exe = path
                        break
                
                if vlc_exe:
                    # Use '--' to prevent URL from being interpreted as option
                    subprocess.Popen([vlc_exe, '--', url], creationflags=subprocess.DETACHED_PROCESS)
                    vlc_launched = True
                else:
                    messagebox.showwarning("VLC Not Found", 
                        "Cannot find VLC media player on your system.\n\n"
                        "Please install VLC from:\nhttps://www.videolan.org/vlc/")
                    return
                    
            elif sys.platform == 'darwin':
                # macOS
                subprocess.Popen(['open', '-a', 'VLC', '--args', '--', url])
                vlc_launched = True
            else:
                # Linux
                subprocess.Popen(['vlc', '--', url])
                vlc_launched = True
            
            # Stop embedded player and close window if VLC was launched
            # Bug #75: Use _on_close() for full cleanup instead of stop()/destroy()
            if vlc_launched:
                self._on_close()
                
        except Exception as e:
            messagebox.showerror("Cannot Launch VLC", 
                "Unable to open VLC media player.\n\n"
                "Please make sure VLC is properly installed on your system.")
    
    def _show_cast_menu(self):
        """Show menu with available Cast devices."""
        if not CAST_AVAILABLE:
            messagebox.showinfo("Cast Not Available", 
                "Google Cast support is not installed.\n\n"
                "To enable casting, run:\npip install pychromecast")
            return
        
        # Create popup menu
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Searching for devices...", state=tk.DISABLED)
        
        # Position menu under button
        try:
            x = self.cast_btn.winfo_rootx()
            y = self.cast_btn.winfo_rooty() + self.cast_btn.winfo_height()
            menu.tk_popup(x, y)
        except tk.TclError:
            pass  # Widget may have been destroyed
        
        # Search for devices in background
        threading.Thread(target=self._discover_cast_devices, daemon=True).start()
    
    def _discover_cast_devices(self):
        """Discover Chromecast devices on the network."""
        if not CAST_AVAILABLE:
            return
        
        try:
            # Get chromecasts
            chromecasts, browser = pychromecast.get_chromecasts()
            self.cast_browser = browser
            self.cast_devices = chromecasts
            
            # Update UI on main thread
            self.after(0, self._show_cast_devices_menu)
            
        except Exception as e:
            logger.error(f"Error discovering cast devices: {e}")
            err_msg = str(e)
            self.after(0, lambda: messagebox.showerror("Cast Discovery Failed", 
                "Unable to find Cast devices on your network.\n\n"
                "Make sure your Chromecast is on the same network as this computer."))
    
    def _show_cast_devices_menu(self):
        """Show menu with discovered Cast devices."""
        menu = tk.Menu(self, tearoff=0)
        
        if not self.cast_devices:
            menu.add_command(label="No devices found", state=tk.DISABLED)
        else:
            for cast in self.cast_devices:
                device_name = cast.cast_info.friendly_name
                menu.add_command(
                    label=device_name,
                    command=lambda c=cast: self._cast_to_device(c)
                )
        
        menu.add_separator()
        menu.add_command(label="Refresh", command=self._show_cast_menu)
        
        if self.active_cast:
            menu.add_separator()
            menu.add_command(label="Stop Casting", command=self._stop_casting)
        
        # Position menu under button
        try:
            x = self.cast_btn.winfo_rootx()
            y = self.cast_btn.winfo_rooty() + self.cast_btn.winfo_height()
            menu.tk_popup(x, y)
        except tk.TclError:
            pass  # Widget may have been destroyed
    
    def _cast_to_device(self, cast):
        """Cast current stream to a Chromecast device."""
        url = self.channel.get('url', '')
        if not url:
            messagebox.showwarning("No Stream URL", 
                "This channel doesn't have a valid stream URL to cast.")
            return
        
        try:
            # Wait for device to be ready
            cast.wait()
            
            # Get media controller
            mc = cast.media_controller
            
            # Determine content type
            url_lower = url.lower()
            if '.m3u8' in url_lower:
                content_type = 'application/x-mpegURL'
            elif '.mpd' in url_lower:
                content_type = 'application/dash+xml'
            elif '.mp4' in url_lower:
                content_type = 'video/mp4'
            else:
                content_type = 'video/mp2t'  # MPEG-TS default for streams
            
            # Cast the stream
            mc.play_media(
                url, 
                content_type,
                title=self.channel.get('name', 'TV Stream')
            )
            mc.block_until_active()
            
            self.active_cast = cast
            messagebox.showinfo("Casting", 
                f"Now casting to {cast.cast_info.friendly_name}")
            
        except Exception as e:
            messagebox.showerror("Casting Failed", 
                "Unable to start casting to the selected device.\n\n"
                "The device may be busy or disconnected.")
    
    def _stop_casting(self):
        """Stop casting to the active device."""
        if self.active_cast:
            try:
                self.active_cast.media_controller.stop()
                self.active_cast = None
            except Exception as e:
                logger.debug(f"Error stopping cast: {e}")
    
    def _on_close(self):
        """Handle window close with proper resource cleanup and timeout protection."""
        logger.info("Starting player window cleanup...")
        
        # Cancel update jobs
        if self._update_job:
            self.after_cancel(self._update_job)
            self._update_job = None
        if self._quality_update_job:
            self.after_cancel(self._quality_update_job)
            self._quality_update_job = None
        if self._preload_job:
            self.after_cancel(self._preload_job)
            self._preload_job = None
        
        # Release preloaded player
        self._release_preload()
        
        # Stop casting if active
        if self.active_cast:
            try:
                self.active_cast.media_controller.stop()
                self.active_cast = None
            except (AttributeError, OSError):
                pass  # Cast may be disconnected
        
        # Stop cast browser
        if self.cast_browser:
            try:
                self.cast_browser.stop_discovery()
                self.cast_browser = None
            except (AttributeError, OSError):
                pass  # Browser may be stopped
        
        # Clear cast devices list
        self.cast_devices.clear()
        
        # Two-stage VLC cleanup with timeout protection (Issue #36)
        self.vlc.cleanup()
        
        # Clear references
        self.channel = None
        self.video_canvas = None
        
        # Force garbage collection
        gc.collect()
        
        logger.info("Player window cleanup completed successfully")
        self.destroy()
    
    def set_channel(self, channel: Dict[str, Any]):
        """
        Switch to a different channel.
        
        Args:
            channel: New channel dictionary
        """
        # Bug #121: Cancel pending timers to avoid stale callbacks
        if self._update_job:
            self.after_cancel(self._update_job)
            self._update_job = None
        if self._quality_update_job:
            self.after_cancel(self._quality_update_job)
            self._quality_update_job = None

        self.stop()
        self._playback_confirmed = False
        self.quality_label.configure(text="Quality: --")
        self.channel = channel
        self.title(f"{config.APP_NAME} - {channel.get('name', 'Unknown')}")
        self.channel_label.configure(text=channel.get('name', 'Unknown'))
        self.play()
