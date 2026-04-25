"""Thumbnail capture utility for TV channels using VLC."""

import os
import hashlib
import threading
from typing import Optional, Dict, Any
import config

# Try to import VLC
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False

# Try to import PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def get_thumbnail_path(url: str) -> str:
    """Get the thumbnail file path for a URL."""
    # Create a hash of the URL for the filename
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:32]
    return os.path.join(config.THUMBNAILS_DIR, f"{url_hash}.png")


def thumbnail_exists(url: str) -> bool:
    """Check if a thumbnail already exists for a URL."""
    return os.path.exists(get_thumbnail_path(url))


def capture_thumbnail(url: str, timeout: int = 5) -> Optional[str]:
    """
    Capture a thumbnail from a video stream using VLC.
    
    Args:
        url: Stream URL to capture from
        timeout: Maximum time to wait for capture
        
    Returns:
        Path to thumbnail file, or None if capture failed
    """
    if not VLC_AVAILABLE:
        return None
    
    # Skip if thumbnail already exists
    thumb_path = get_thumbnail_path(url)
    if os.path.exists(thumb_path):
        return thumb_path
    
    # Validate URL
    url_lower = url.lower()
    if not url_lower.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
        return None
    
    instance = None
    player = None
    
    try:
        # Create VLC instance with snapshot options
        # Using video memory output for reliable snapshot capture
        import sys
        if sys.platform == 'win32':
            # On Windows, use vmem or direct3d
            instance = vlc.Instance('--no-xlib', '--quiet', '--no-audio', 
                                    '--vout=vmem', '--avcodec-hw=none')
        else:
            instance = vlc.Instance('--no-xlib', '--quiet', '--no-audio', '--vout=dummy')
        
        if not instance:
            return None
        
        player = instance.media_player_new()
        if not player:
            return None
        
        media = instance.media_new(url)
        if not media:
            return None
        
        player.set_media(media)
        player.play()
        
        # Wait for video to start with better state checking
        import time
        start = time.time()
        video_ready = False
        
        while time.time() - start < timeout:
            state = player.get_state()
            if state == vlc.State.Playing:
                # Check if video has dimensions
                width = player.video_get_width()
                height = player.video_get_height()
                if width > 0 and height > 0:
                    # Wait a bit more for a good frame
                    time.sleep(1.0)
                    video_ready = True
                    break
            elif state in (vlc.State.Error, vlc.State.Ended, vlc.State.Stopped):
                return None
            time.sleep(0.2)
        
        if not video_ready:
            return None
        
        # Try to take snapshot with retries
        width = player.video_get_width()
        height = player.video_get_height()
        
        if width > 0 and height > 0:
            # Take snapshot to secure temp file (TOCTOU-safe, Issue #89)
            import tempfile
            fd, temp_path = tempfile.mkstemp(suffix='.png', dir=config.THUMBNAILS_DIR)
            os.close(fd)
            
            # Try snapshot multiple times
            for attempt in range(3):
                result = player.video_take_snapshot(0, temp_path, 
                                                     config.THUMBNAIL_WIDTH, 
                                                     config.THUMBNAIL_HEIGHT)
                
                if result == 0:
                    # Wait for file to be written
                    time.sleep(0.3)
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        # Atomic replace to final path (TOCTOU-safe)
                        os.replace(temp_path, thumb_path)
                        return thumb_path
                time.sleep(0.3)
            
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        
        return None
        
    except Exception as e:
        print(f"Thumbnail capture error for {url[:50]}: {e}")
        return None
        
    finally:
        # Cleanup
        if player:
            try:
                player.stop()
                player.release()
            except Exception:
                pass
        if instance:
            try:
                instance.release()
            except Exception:
                pass


def capture_thumbnail_async(url: str, callback=None):
    """
    Capture thumbnail in background thread.
    
    Args:
        url: Stream URL
        callback: Function to call with (url, thumbnail_path) when done
    """
    def _capture():
        path = capture_thumbnail(url)
        if callback:
            callback(url, path)
    
    thread = threading.Thread(target=_capture, daemon=True)
    thread.start()
