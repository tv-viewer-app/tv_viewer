#!/usr/bin/env python3
"""
TV Viewer - Cross-platform IPTV Streaming Application

A worldwide TV streams viewer that:
- Discovers and polls open IPTV repositories
- Validates streams in background
- Provides categorized channel browsing
- Plays streams in a separate window with controls
- Caches working channels for faster startup
"""

import sys
import os
import gc
import atexit

# Optimize Python for better performance
sys.setrecursionlimit(2000)  # Reasonable limit

# Enable garbage collection optimization
gc.set_threshold(700, 10, 10)  # More aggressive GC for lower memory

# Add project root to path for imports
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)  # Set working directory


def cleanup_temp_files():
    """Clean up temporary files and force garbage collection."""
    # Force garbage collection
    gc.collect()
    print("Cleanup complete")


def main():
    """Application entry point."""
    print("Starting TV Viewer...")
    
    # Register cleanup on exit
    atexit.register(cleanup_temp_files)
    
    # Check for VLC
    try:
        import vlc
        print("VLC library found")
    except ImportError:
        print("Warning: python-vlc not installed.")
        print("Install with: pip install python-vlc")
        print("Also ensure VLC media player is installed on your system.")
        print()
    
    # Import after path setup
    from ui.main_window import MainWindow
    
    # Create and run the main window
    app = MainWindow()
    app.run()
    
    # Explicit cleanup after mainloop exits
    cleanup_temp_files()


if __name__ == "__main__":
    main()
