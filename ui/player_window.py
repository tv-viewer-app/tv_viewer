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
import customtkinter as ctk
import sys
import os
import subprocess
import threading
import gc
import logging
from typing import Optional, Dict, Any, List

from utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Try to import VLC
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    logger.warning("python-vlc not installed. Video playback will not work.")

# Try to import pychromecast for Google Cast
try:
    import pychromecast
    CAST_AVAILABLE = True
except ImportError:
    CAST_AVAILABLE = False
    logger.info("pychromecast not installed. Casting will not be available.")

import config
from utils.helpers import format_duration
from ui.constants import FluentColors, FluentSpacing
from ui.tooltip import add_tooltip


def get_vlc_hardware_acceleration_args() -> list:
    """Get VLC arguments for hardware-accelerated video decoding.
    
    Returns platform-specific arguments to enable GPU video decoding,
    which significantly reduces CPU usage during playback.
    
    Returns:
        List of VLC command-line arguments
    """
    base_args = [
        '--no-xlib',           # Disable X11 threading (Linux)
        '--quiet',             # Reduce logging
        '--no-lua',            # Disable Lua scripting (security/performance)
        '--no-video-title-show',  # Don't show title on video
        '--network-caching=1000',  # 1 second network buffer (reduces latency)
        '--live-caching=1000',     # 1 second live stream buffer
    ]
    
    if sys.platform == 'win32':
        # Windows: Use Direct3D11 hardware acceleration
        return base_args + [
            '--avcodec-hw=d3d11va',  # Direct3D 11 Video Acceleration
            '--directx-use-sysmem',   # Fallback to system memory if needed
        ]
    elif sys.platform == 'darwin':
        # macOS: Use VideoToolbox hardware acceleration
        return base_args + [
            '--avcodec-hw=videotoolbox',  # Apple VideoToolbox
            '--videotoolbox-temporal-deinterlacing',
        ]
    else:
        # Linux: Try VAAPI first, fallback to VDPAU
        return base_args + [
            '--avcodec-hw=vaapi',  # Video Acceleration API (Intel/AMD)
            # '--avcodec-hw=vdpau',  # VDPAU fallback (NVIDIA)
        ]


class PlayerWindow(ctk.CTkToplevel):
    """Separate window for video playback with controls."""
    
    def __init__(self, parent, channel: Dict[str, Any]):
        super().__init__(parent)
        
        self.channel = channel
        self.parent = parent
        self.player: Optional[vlc.MediaPlayer] = None
        self.instance: Optional[vlc.Instance] = None
        self.is_playing = False
        self._update_job = None
        self._quality_update_job = None
        
        # Cast-related
        self.cast_devices: List[Any] = []
        self.active_cast = None
        self.cast_browser = None
        
        self._setup_window()
        self._create_widgets()
        
        if VLC_AVAILABLE:
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
        self.configure(fg_color=FluentColors.BG_MICA)
        
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color=FluentColors.BG_MICA, corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        
        # Video frame (where VLC will render)
        self.video_frame = ctk.CTkFrame(self.main_frame, fg_color="black", corner_radius=0)
        self.video_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create a canvas for video (needed for VLC on some platforms)
        self.video_canvas = tk.Canvas(
            self.video_frame, 
            bg='black',
            highlightthickness=0
        )
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Controls frame with Fluent Design
        self.controls_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=FluentColors.BG_ACRYLIC,
            corner_radius=0,
            height=60
        )
        self.controls_frame.grid(row=1, column=0, sticky="ew")
        self.controls_frame.grid_propagate(False)
        
        # Play/Pause button - Windows 11 style
        self.play_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏸",
            width=44,
            height=44,
            corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
            fg_color=FluentColors.ACCENT,
            hover_color=FluentColors.ACCENT_DARK,
            command=self._toggle_play,
            font=ctk.CTkFont(size=16)
        )
        self.play_btn.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_LARGE, pady=8)
        add_tooltip(self.play_btn, "Play/Pause (Space)")
        
        # Stop button
        self.stop_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏹",
            width=44,
            height=44,
            corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
            fg_color=FluentColors.CONTROL_DEFAULT,
            hover_color=FluentColors.CONTROL_HOVER,
            command=self.stop,
            font=ctk.CTkFont(size=16)
        )
        self.stop_btn.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_SMALL)
        add_tooltip(self.stop_btn, "Stop playback")
        
        # Time label
        self.time_label = ctk.CTkLabel(
            self.controls_frame,
            text="00:00",
            width=80,
            font=ctk.CTkFont(size=14),
            text_color=FluentColors.TEXT_PRIMARY
        )
        self.time_label.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_LARGE)
        
        # Volume controls
        volume_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        volume_frame.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_LARGE)
        
        ctk.CTkLabel(volume_frame, text="🔊", font=ctk.CTkFont(size=14)).pack(side=tk.LEFT)
        
        self.volume_var = tk.IntVar(value=80)
        self.volume_slider = ctk.CTkSlider(
            volume_frame,
            from_=0,
            to=100,
            variable=self.volume_var,
            command=self._on_volume_change,
            width=120,
            progress_color=FluentColors.ACCENT,
            button_color=FluentColors.ACCENT,
            button_hover_color=FluentColors.ACCENT_LIGHT
        )
        self.volume_slider.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_MEDIUM)
        add_tooltip(self.volume_slider, "Adjust volume")
        
        # Volume percentage label
        self.volume_label = ctk.CTkLabel(
            volume_frame,
            text="80%",
            width=40,
            font=ctk.CTkFont(size=12),
            text_color=FluentColors.TEXT_SECONDARY
        )
        self.volume_label.pack(side=tk.LEFT, padx=2)
        
        # Mute button
        self.mute_btn = ctk.CTkButton(
            volume_frame,
            text="🔇",
            width=36,
            height=36,
            corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
            fg_color=FluentColors.CONTROL_DEFAULT,
            hover_color=FluentColors.CONTROL_HOVER,
            command=self._toggle_mute,
            font=ctk.CTkFont(size=14)
        )
        self.mute_btn.pack(side=tk.LEFT)
        add_tooltip(self.mute_btn, "Mute/Unmute (M)")
        
        # Fullscreen button
        self.fullscreen_btn = ctk.CTkButton(
            self.controls_frame,
            text="⛶",
            width=36,
            height=36,
            corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
            fg_color=FluentColors.CONTROL_DEFAULT,
            hover_color=FluentColors.CONTROL_HOVER,
            command=self._toggle_fullscreen,
            font=ctk.CTkFont(size=14)
        )
        self.fullscreen_btn.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_SMALL)
        add_tooltip(self.fullscreen_btn, "Fullscreen (F) - Press ESC to exit")
        
        # Open in VLC button
        self.vlc_btn = ctk.CTkButton(
            self.controls_frame,
            text="VLC",
            width=48,
            height=36,
            corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
            fg_color=FluentColors.CONTROL_DEFAULT,
            hover_color=FluentColors.CONTROL_HOVER,
            command=self._open_in_external_vlc,
            font=ctk.CTkFont(size=12)
        )
        self.vlc_btn.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_SMALL)
        add_tooltip(self.vlc_btn, "Open in external VLC player")
        
        # Cast button (if available)
        if CAST_AVAILABLE:
            self.cast_btn = ctk.CTkButton(
                self.controls_frame,
                text="📺",
                width=36,
                height=36,
                corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
                fg_color=FluentColors.CONTROL_DEFAULT,
                hover_color=FluentColors.CONTROL_HOVER,
                command=self._show_cast_menu,
                font=ctk.CTkFont(size=14)
            )
            self.cast_btn.pack(side=tk.RIGHT, padx=FluentSpacing.PADDING_SMALL)
            add_tooltip(self.cast_btn, "Cast to TV/Chromecast")
        
        # Channel info
        channel_name = self.channel.get('name', 'Unknown')
        self.channel_label = ctk.CTkLabel(
            self.controls_frame,
            text=channel_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=FluentColors.TEXT_PRIMARY
        )
        self.channel_label.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_XLARGE)
        
        # Quality info frame (below controls)
        self.quality_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=FluentColors.BG_CARD,
            corner_radius=0,
            height=28
        )
        self.quality_frame.grid(row=2, column=0, sticky="ew")
        self.quality_frame.grid_propagate(False)
        
        self.quality_label = ctk.CTkLabel(
            self.quality_frame,
            text="Quality: --",
            font=ctk.CTkFont(size=11),
            text_color=FluentColors.TEXT_SECONDARY
        )
        self.quality_label.pack(side=tk.LEFT, padx=FluentSpacing.PADDING_LARGE, pady=4)
        
        # Bind keyboard shortcuts
        self.bind('<space>', lambda e: self._toggle_play())
        self.bind('<Escape>', lambda e: self._exit_fullscreen())
        self.bind('f', lambda e: self._toggle_fullscreen())
        self.bind('m', lambda e: self._toggle_mute())
        
        # Double-click for fullscreen
        self.video_canvas.bind('<Double-Button-1>', lambda e: self._toggle_fullscreen())
    
    def _init_vlc(self):
        """Initialize VLC player with hardware acceleration and error handling.
        
        This method creates a VLC instance with platform-specific hardware
        acceleration enabled. Hardware decoding significantly reduces CPU usage
        by offloading video decoding to the GPU.
        
        Hardware Acceleration Priority:
        - Windows: D3D11VA (Direct3D 11 Video Acceleration)
        - macOS: VideoToolbox
        - Linux: VAAPI (Intel/AMD) or VDPAU (NVIDIA)
        """
        try:
            # Get platform-specific hardware acceleration arguments
            vlc_args = get_vlc_hardware_acceleration_args()
            
            # Create VLC instance with hardware acceleration
            self.instance = vlc.Instance(*vlc_args)
            if not self.instance:
                # Fallback: try without hardware acceleration
                print("Hardware acceleration failed, trying software decoding...")
                self.instance = vlc.Instance('--no-xlib', '--quiet', '--no-lua')
            
            if not self.instance:
                raise RuntimeError("Failed to create VLC instance")
            
            self.player = self.instance.media_player_new()
            if not self.player:
                raise RuntimeError("Failed to create media player")
            
            # Set video output to our canvas window
            # This is platform-specific for proper video embedding
            if sys.platform == 'win32':
                self.player.set_hwnd(self.video_canvas.winfo_id())
            elif sys.platform == 'darwin':
                self.player.set_nsobject(self.video_canvas.winfo_id())
            else:
                self.player.set_xwindow(self.video_canvas.winfo_id())
            
            # Set initial volume
            self.player.audio_set_volume(self.volume_var.get())
            
        except Exception as e:
            logger.error(f"Error initializing VLC: {e}")
            self.player = None
            self.instance = None
            self._show_vlc_error()
    
    def _show_vlc_error(self):
        """Show error message when VLC is not available with recovery options."""
        import webbrowser
        
        error_frame = ctk.CTkFrame(self.video_canvas, fg_color=FluentColors.BG_CARD)
        error_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        ctk.CTkLabel(
            error_frame,
            text="⚠️ VLC Media Player Required",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=FluentColors.WARNING
        ).pack(pady=(20, 10), padx=30)
        
        ctk.CTkLabel(
            error_frame,
            text="VLC is required for video playback.\nPlease install it to watch streams.",
            font=ctk.CTkFont(size=12),
            text_color=FluentColors.TEXT_SECONDARY,
            justify="center"
        ).pack(pady=5, padx=30)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(error_frame, fg_color="transparent")
        btn_frame.pack(pady=(15, 20))
        
        # Download VLC button
        def open_vlc_download():
            webbrowser.open("https://www.videolan.org/vlc/")
        
        ctk.CTkButton(
            btn_frame,
            text="Download VLC",
            width=120,
            fg_color=FluentColors.ACCENT,
            hover_color=FluentColors.ACCENT_DARK,
            command=open_vlc_download
        ).pack(side=tk.LEFT, padx=5)
        
        # Retry button
        ctk.CTkButton(
            btn_frame,
            text="Retry",
            width=80,
            fg_color=FluentColors.CONTROL_DEFAULT,
            hover_color=FluentColors.CONTROL_HOVER,
            command=lambda: [error_frame.destroy(), self._init_vlc(), self.play() if self.player else None]
        ).pack(side=tk.LEFT, padx=5)
        
        # Help text
        ctk.CTkLabel(
            error_frame,
            text="After installing VLC, also run: pip install python-vlc",
            font=ctk.CTkFont(size=10),
            text_color=FluentColors.TEXT_DISABLED
        ).pack(pady=(0, 15))
    
    def play(self):
        """Start playing the stream."""
        if not VLC_AVAILABLE or not self.player:
            return
        
        url = self.channel.get('url', '')
        if not url:
            return
        
        # Security: Validate URL scheme
        url_lower = url.lower()
        allowed_schemes = ('http://', 'https://', 'rtmp://', 'rtsp://', 'mms://')
        if not url_lower.startswith(allowed_schemes):
            logger.warning(f"Invalid URL scheme: {url}")
            messagebox.showwarning("Invalid URL", "This stream URL scheme is not supported.")
            return
        
        # Security: Block dangerous schemes
        if url_lower.startswith(('file://', 'javascript:', 'data:')):
            logger.warning(f"Blocked dangerous URL: {url}")
            return
        
        try:
            media = self.instance.media_new(url)
            if not media:
                logger.error(f"Failed to create media for: {url}")
                messagebox.showerror("Playback Error", "Failed to load stream. The URL may be invalid.")
                return
            
            self.player.set_media(media)
            self.player.play()
            self.is_playing = True
            self.play_btn.configure(text="⏸")
            
            # Start updating time display
            self._update_time()
            
            # Start updating quality info (with delay to let stream start)
            self.after(2000, self._update_quality_info)
            
        except Exception as e:
            logger.error(f"Error playing stream: {e}")
            messagebox.showerror("Playback Error", f"Failed to play stream:\n{e}")
    
    def pause(self):
        """Pause playback."""
        if self.player:
            self.player.pause()
            self.is_playing = False
            self.play_btn.configure(text="▶")
    
    def stop(self):
        """Stop playback."""
        if self.player:
            self.player.stop()
            self.is_playing = False
            self.play_btn.configure(text="▶")
            self.time_label.configure(text="00:00")
    
    def _toggle_play(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self.pause()
        else:
            if self.player and self.player.get_state() == vlc.State.Paused:
                self.player.pause()  # Unpause
                self.is_playing = True
                self.play_btn.configure(text="⏸")
            else:
                self.play()
    
    def _toggle_mute(self):
        """Toggle audio mute."""
        if self.player:
            is_muted = self.player.audio_get_mute()
            self.player.audio_set_mute(not is_muted)
            self.mute_btn.configure(text="🔈" if not is_muted else "🔇")
    
    def _on_volume_change(self, value):
        """Handle volume slider change."""
        if self.player:
            volume = int(float(value))
            self.player.audio_set_volume(volume)
            self.volume_label.configure(text=f"{volume}%")
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        is_fullscreen = self.attributes('-fullscreen')
        self.attributes('-fullscreen', not is_fullscreen)
        
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
        """Update the time display."""
        if self.player and self.is_playing:
            try:
                time_ms = self.player.get_time()
                if time_ms > 0:
                    time_sec = time_ms // 1000
                    self.time_label.configure(text=format_duration(time_sec))
            except (AttributeError, OSError):
                pass  # VLC instance may be closed
        
        # Schedule next update (every 2 seconds to reduce CPU)
        if self.winfo_exists():
            self._update_job = self.after(2000, self._update_time)
    
    def _update_quality_info(self):
        """Update video quality information display."""
        if not self.player or not self.is_playing:
            return
        
        try:
            media = self.player.get_media()
            if not media:
                return
            
            # Get video track info
            width = 0
            height = 0
            fps = 0.0
            bitrate = 0
            
            # Try to get video dimensions from player
            width = self.player.video_get_width()
            height = self.player.video_get_height()
            
            # Get media stats for bitrate
            stats = vlc.MediaStats()
            if media.get_stats(stats):
                # Bitrate in bytes/sec, convert to kbps
                bitrate = int(stats.demux_bitrate * 8 / 1000) if stats.demux_bitrate > 0 else 0
            
            # Try to get FPS
            fps = self.player.get_fps()
            
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
            pass  # Silently ignore quality info errors
        
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
            messagebox.showerror("Invalid URL", f"URL scheme '{parsed.scheme}' is not allowed.")
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
                        "VLC media player not found.\nPlease install VLC or check installation path.")
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
            if vlc_launched:
                self._stop_playback()
                self.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open VLC:\n{e}")
    
    def _show_cast_menu(self):
        """Show menu with available Cast devices."""
        if not CAST_AVAILABLE:
            messagebox.showinfo("Cast Unavailable", 
                "Google Cast is not available.\nInstall pychromecast: pip install pychromecast")
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
            self.after(0, lambda: messagebox.showerror("Cast Error", 
                f"Error discovering devices:\n{e}"))
    
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
            messagebox.showwarning("No URL", "No stream URL available.")
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
            messagebox.showerror("Cast Error", f"Could not cast to device:\n{e}")
    
    def _stop_casting(self):
        """Stop casting to the active device."""
        if self.active_cast:
            try:
                self.active_cast.media_controller.stop()
                self.active_cast = None
            except Exception as e:
                logger.debug(f"Error stopping cast: {e}")
    
    def _on_close(self):
        """Handle window close with proper resource cleanup."""
        # Cancel update jobs
        if self._update_job:
            self.after_cancel(self._update_job)
            self._update_job = None
        if self._quality_update_job:
            self.after_cancel(self._quality_update_job)
            self._quality_update_job = None
        
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
        
        # Stop and release player
        if self.player:
            try:
                self.player.stop()
                self.player.release()
            except (AttributeError, OSError):
                pass  # Player may be released
            self.player = None
        
        if self.instance:
            try:
                self.instance.release()
            except (AttributeError, OSError):
                pass  # Instance may be released
            self.instance = None
        
        # Clear references
        self.channel = None
        self.video_canvas = None
        
        # Force garbage collection
        gc.collect()
        
        self.destroy()
    
    def set_channel(self, channel: Dict[str, Any]):
        """
        Switch to a different channel.
        
        Args:
            channel: New channel dictionary
        """
        self.stop()
        self.channel = channel
        self.title(f"{config.APP_NAME} - {channel.get('name', 'Unknown')}")
        self.channel_label.configure(text=channel.get('name', 'Unknown'))
        self.play()
