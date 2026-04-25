"""VLC media player controller with hardware acceleration support.

Encapsulates VLC instance lifecycle, media player operations, preloading,
and resource cleanup. This module contains no UI (tkinter) code.

Hardware Acceleration:
- Windows: Direct3D11 (d3d11va) or DXVA2 for GPU-accelerated decoding
- Linux: VAAPI or VDPAU for GPU-accelerated decoding
- macOS: VideoToolbox for GPU-accelerated decoding

Threading:
- VLC runs on its own thread (handled by libvlc)
- Cleanup uses a two-stage timeout to prevent freezes
"""

import sys
import os
import gc
import threading
import logging
from typing import Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    logger.warning("python-vlc not installed. Video playback will not work.")


def get_vlc_hardware_acceleration_args() -> list:
    """Get VLC arguments optimized for IPTV streaming.
    
    Hardware acceleration is disabled by default as it causes compatibility issues.
    The args focus on stability and low latency for IPTV streams.
    
    Returns:
        List of VLC command-line arguments
    """
    # Base args optimized for IPTV streaming (Issue #35)
    base_args = [
        '--no-xlib',           # Disable X11 threading (Linux)
        '--quiet',             # Reduce logging
        '--no-lua',            # Disable Lua scripting (security/performance)
        '--no-video-title-show',  # Don't show title on video
        '--network-caching=1000',  # 1 second network buffer
        '--live-caching=1000',     # 1 second live stream buffer
        '--clock-jitter=0',        # Disable jitter compensation (smoother)
        '--clock-synchro=0',       # Disable clock synchronization
    ]
    
    # Platform-specific adjustments (no hardware acceleration to avoid failures)
    if sys.platform == 'win32':
        # Windows: Simple, stable settings
        return base_args + [
            '--no-plugins-cache',  # Don't cache plugins
        ]
    elif sys.platform == 'darwin':
        # macOS: Simple, stable settings
        return base_args + [
            '--no-plugins-cache',
        ]
    else:
        # Linux: Simple, stable settings (no VAAPI/VDPAU)
        return base_args + [
            '--no-plugins-cache',
            '--no-sub-autodetect-file',  # Don't scan for subtitles
        ]


class VLCController:
    """Manages VLC media player instance lifecycle.
    
    Encapsulates VLC instance creation, media player operations, preloading,
    and resource cleanup. Does not contain any UI (tkinter) code.
    """
    
    def __init__(self):
        self._instance = None
        self._player = None
        self._preload_player = None
        self._preload_url: Optional[str] = None
    
    @property
    def is_available(self) -> bool:
        """Whether python-vlc is installed and importable."""
        return VLC_AVAILABLE
    
    @property
    def instance(self):
        """The underlying vlc.Instance, or None."""
        return self._instance
    
    @property
    def player(self):
        """The main vlc.MediaPlayer, or None."""
        return self._player
    
    @property
    def preload_player(self):
        """The preloaded vlc.MediaPlayer, or None."""
        return self._preload_player
    
    @property
    def preload_url(self) -> Optional[str]:
        """The URL currently being preloaded, or None."""
        return self._preload_url
    
    def initialize(self, hwnd: int, initial_volume: int = 80) -> bool:
        """Initialize VLC instance and media player with fallback.
        
        Tries optimized settings first, falls back to minimal settings if
        needed (Issue #35).
        
        Args:
            hwnd: Window handle for video output.
            initial_volume: Initial volume level (0-100).
        
        Returns:
            True if initialization succeeded, False otherwise.
        """
        try:
            # Try with optimized arguments first
            vlc_args = get_vlc_hardware_acceleration_args()
            logger.info(f"Initializing VLC with args: {vlc_args}")
            
            self._instance = vlc.Instance(*vlc_args)
            if not self._instance:
                # Fallback: try with absolute minimal settings
                logger.warning("Optimized VLC init failed, trying minimal settings...")
                self._instance = vlc.Instance('--quiet', '--no-xlib')
            
            if not self._instance:
                # Last resort: no arguments at all
                logger.warning("Minimal VLC init failed, trying no arguments...")
                self._instance = vlc.Instance()
            
            if not self._instance:
                raise RuntimeError("Failed to create VLC instance with all fallbacks")
            
            logger.info(f"✅ VLC Instance created successfully")
            
            self._player = self._instance.media_player_new()
            if not self._player:
                raise RuntimeError("Failed to create media player")
            
            logger.info(f"✅ Media Player created successfully")
            
            # Set video output to canvas window
            # This is platform-specific for proper video embedding
            self._set_hwnd_on_player(self._player, hwnd)
            
            # Set initial volume
            self._player.audio_set_volume(initial_volume)
            
            logger.info(f"✅ VLC initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing VLC: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._player = None
            self._instance = None
            return False
    
    def play_url(self, url: str) -> bool:
        """Create media from URL, set it on the player, and start playback.
        
        Args:
            url: Stream URL to play.
        
        Returns:
            True if media was created and playback started, False otherwise.
        """
        if not self._instance or not self._player:
            return False
        
        media = self._instance.media_new(url)
        if not media:
            return False
        
        self._player.set_media(media)
        self._player.play()
        return True
    
    def pause(self):
        """Pause (toggle) the media player."""
        if self._player:
            self._player.pause()
    
    def stop(self):
        """Stop the media player."""
        if self._player:
            self._player.stop()
    
    def set_volume(self, volume: int):
        """Set audio volume (0-100)."""
        if self._player:
            self._player.audio_set_volume(volume)
    
    def get_mute(self) -> bool:
        """Get current mute state."""
        if self._player:
            return self._player.audio_get_mute()
        return False
    
    def set_mute(self, mute: bool):
        """Set mute state."""
        if self._player:
            self._player.audio_set_mute(mute)
    
    def get_time(self) -> int:
        """Get current playback time in milliseconds.
        
        Returns:
            Playback time in ms, or -1 if unavailable.
        """
        if self._player:
            return self._player.get_time()
        return -1
    
    def get_length(self) -> int:
        """Get media length in milliseconds.
        
        Returns:
            Media length in ms, or -1 if unavailable.
        """
        if self._player:
            return self._player.get_length()
        return -1
    
    def get_state(self):
        """Get the current VLC player state.
        
        Returns:
            vlc.State enum value, or None if player unavailable.
        """
        if self._player:
            return self._player.get_state()
        return None
    
    def get_fps(self) -> float:
        """Get current video frames per second."""
        if self._player:
            return self._player.get_fps()
        return 0.0
    
    def get_video_dimensions(self) -> Tuple[int, int]:
        """Get video width and height.
        
        Returns:
            Tuple of (width, height). Both 0 if unavailable.
        """
        if self._player:
            return self._player.video_get_width(), self._player.video_get_height()
        return 0, 0
    
    def has_media(self) -> bool:
        """Check if the player currently has media loaded."""
        if not self._player:
            return False
        return self._player.get_media() is not None
    
    def get_media_stats(self):
        """Get media statistics (bitrate, etc.).
        
        Returns:
            vlc.MediaStats object if available, None otherwise.
        """
        if not VLC_AVAILABLE or not self._player:
            return None
        media = self._player.get_media()
        if not media:
            return None
        stats = vlc.MediaStats()
        if media.get_stats(stats):
            return stats
        return None
    
    def create_preload_player(self, url: str) -> bool:
        """Create a muted, video-less preload player for the given URL.
        
        Releases any existing preload player first.
        
        Args:
            url: Stream URL to preload.
        
        Returns:
            True if preload player was created successfully.
        """
        if not self._instance:
            return False
        
        self.release_preload()
        
        try:
            player = self._instance.media_player_new()
            if not player:
                return False
            media = self._instance.media_new(url)
            if not media:
                player.release()
                return False
            # Low-latency preload: small cache, muted, no video output
            media.add_option(':network-caching=500')
            media.add_option(':no-video')
            player.set_media(media)
            player.audio_set_mute(True)
            player.play()
            
            self._preload_player = player
            self._preload_url = url
            return True
        except Exception as e:
            logger.debug(f"Preload failed: {e}")
            self.release_preload()
            return False
    
    def activate_preload(self, hwnd: int, volume: int, url: Optional[str] = None):
        """Swap preload player into main player slot.
        
        The preload player becomes the new main player with video output
        and audio enabled. A new media is created (with video) so the
        swapped player renders to the screen.
        
        Args:
            hwnd: Window handle for video output.
            volume: Audio volume (0-100).
            url: URL for creating fresh media with video. If None, uses
                the stored preload_url.
        
        Returns:
            Tuple of (old_player, resolved_url). Caller should release
            old_player via release_player().
        """
        old_player = self._player
        self._player = self._preload_player
        self._preload_player = None
        
        resolved_url = url or self._preload_url
        self._preload_url = None
        
        if self._player:
            # Attach video output and unmute
            self._set_hwnd_on_player(self._player, hwnd)
            self._player.audio_set_mute(False)
            self._player.audio_set_volume(volume)
            
            # Re-enable video output: create new media with video
            if resolved_url and self._instance:
                media = self._instance.media_new(resolved_url)
                if media:
                    media.add_option(':network-caching=500')
                    self._player.set_media(media)
                    self._player.play()
        
        return old_player, resolved_url
    
    def release_preload(self):
        """Stop and release the preload player."""
        if self._preload_player:
            try:
                self._preload_player.stop()
                self._preload_player.release()
            except Exception:
                pass
            self._preload_player = None
        self._preload_url = None
    
    def cleanup(self):
        """Release all VLC resources with timeout protection.
        
        Implements two-stage shutdown (Issue #36):
        - Stage 1: Graceful cleanup (2 seconds timeout)
        - Stage 2: Force cleanup if graceful fails
        Total maximum time: 5 seconds
        """
        # Release preload first (fast, synchronous)
        self.release_preload()
        
        if not self._player and not self._instance:
            return
        
        # Flag to track if cleanup completed
        cleanup_completed = threading.Event()
        force_cleanup_executed = threading.Event()
        
        # Capture references for closure safety
        controller = self
        
        def graceful_cleanup():
            """Stage 1: Graceful VLC cleanup."""
            try:
                logger.info("Stage 1: Starting graceful VLC cleanup...")
                if controller._player:
                    controller._player.stop()
                    controller._player.release()
                    controller._player = None
                    logger.info("Player stopped and released")
                
                if controller._instance:
                    controller._instance.release()
                    controller._instance = None
                    logger.info("VLC instance released")
                
                cleanup_completed.set()
                logger.info("Stage 1: Graceful cleanup completed")
            except Exception as e:
                logger.warning(f"Stage 1: Graceful cleanup failed: {e}")
                cleanup_completed.set()
        
        def force_cleanup():
            """Stage 2: Force cleanup if graceful cleanup times out."""
            if not force_cleanup_executed.is_set():
                force_cleanup_executed.set()
                logger.warning("Stage 2: Force cleanup triggered (graceful cleanup timed out)")
                try:
                    # Forcefully clear references
                    if controller._player:
                        controller._player = None
                        logger.info("Player reference forcefully cleared")
                    if controller._instance:
                        controller._instance = None
                        logger.info("VLC instance reference forcefully cleared")
                    
                    # Force garbage collection
                    gc.collect()
                    logger.info("Stage 2: Force cleanup completed")
                except Exception as e:
                    logger.error(f"Stage 2: Force cleanup error: {e}")
                finally:
                    cleanup_completed.set()
        
        # Start graceful cleanup in thread
        cleanup_thread = threading.Thread(target=graceful_cleanup, daemon=True)
        cleanup_thread.start()
        
        # Set up watchdog timer for force cleanup (2 seconds for graceful)
        watchdog = threading.Timer(2.0, force_cleanup)
        watchdog.daemon = True
        watchdog.start()
        
        # Wait for cleanup with total timeout of 5 seconds
        if not cleanup_completed.wait(timeout=5.0):
            logger.error("VLC cleanup exceeded 5 second timeout - forcing completion")
            if self._player:
                self._player = None
            if self._instance:
                self._instance = None
            gc.collect()
        else:
            # Cancel watchdog if cleanup completed before timeout
            watchdog.cancel()
        
        logger.info("VLC cleanup process finished")
    
    @staticmethod
    def _set_hwnd_on_player(player, hwnd: int):
        """Set video output window handle on a VLC player (platform-specific).
        
        Args:
            player: VLC media player instance.
            hwnd: Window handle / X window ID / NSObject ID.
        """
        if sys.platform == 'win32':
            player.set_hwnd(hwnd)
        elif sys.platform == 'darwin':
            player.set_nsobject(hwnd)
        else:
            player.set_xwindow(hwnd)
    
    @staticmethod
    def release_player(player):
        """Release an individual VLC media player.
        
        Useful for releasing old players after a preload swap.
        
        Args:
            player: VLC media player to release, or None.
        """
        if player:
            try:
                player.release()
            except Exception:
                pass
