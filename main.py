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


# Required packages with minimum versions
REQUIRED_PACKAGES = {
    'customtkinter': ('customtkinter', '5.2.0'),
    'PIL': ('Pillow', '10.0.0'),
    'aiohttp': ('aiohttp', '3.9.0'),
    'requests': ('requests', '2.31.0'),
}

# Optional packages (app works without them but with reduced functionality)
OPTIONAL_PACKAGES = {
    'vlc': ('python-vlc', '3.0.18122', 'Video playback will not work'),
    'pychromecast': ('pychromecast', '13.0.0', 'Google Cast will not be available'),
}


def check_requirements():
    """Check if all required packages are installed.
    
    Returns:
        tuple: (success: bool, missing: list, warnings: list)
    """
    missing = []
    warnings = []
    
    # Check required packages
    for import_name, (package_name, min_version) in REQUIRED_PACKAGES.items():
        try:
            module = __import__(import_name)
            # Try to get version
            version = getattr(module, '__version__', None) or getattr(module, 'VERSION', 'unknown')
        except ImportError:
            missing.append(f"{package_name}>={min_version}")
    
    # Check optional packages
    for import_name, (package_name, min_version, warning_msg) in OPTIONAL_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            warnings.append(f"{package_name}: {warning_msg}")
    
    return len(missing) == 0, missing, warnings


def show_requirements_error(missing: list):
    """Show error dialog for missing requirements."""
    msg = "Missing required packages:\n\n"
    msg += "\n".join(f"  • {pkg}" for pkg in missing)
    msg += "\n\nInstall with:\n"
    msg += f"  pip install {' '.join(missing)}"
    
    # Try to show GUI error if tkinter available
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("TV Viewer - Missing Dependencies", msg)
        root.destroy()
    except Exception:
        pass
    
    print("\n" + "="*50)
    print("ERROR: Missing required dependencies")
    print("="*50)
    print(msg)
    print("="*50 + "\n")


def cleanup_temp_files():
    """Clean up temporary files and force garbage collection."""
    # Force garbage collection
    gc.collect()
    print("Cleanup complete")


def main():
    """Application entry point."""
    print("Starting TV Viewer...")
    
    # Check requirements first
    success, missing, warnings = check_requirements()
    
    if not success:
        show_requirements_error(missing)
        sys.exit(1)
    
    # Show warnings for optional packages
    for warning in warnings:
        print(f"Warning: {warning}")
    
    # Register cleanup on exit
    atexit.register(cleanup_temp_files)
    
    # Check for VLC (already in optional packages but provide install hint)
    try:
        import vlc
        print("VLC library found")
    except ImportError:
        print("Warning: python-vlc not installed.")
        print("Install with: pip install python-vlc")
        print("Also ensure VLC media player is installed on your system.")
        print()
    
    # Import after path setup and requirements check
    from ui.main_window import MainWindow
    
    # Create and run the main window
    app = MainWindow()
    app.run()
    
    # Explicit cleanup after mainloop exits
    cleanup_temp_files()


if __name__ == "__main__":
    main()
