#!/usr/bin/env python3
"""
Build script to package TV Viewer as a single executable.
Supports both Windows and Linux.

Usage:
    python build.py          # Build for current platform
    python build.py --onefile # Single file executable
    python build.py --clean   # Clean build artifacts
"""

import os
import sys
import shutil
import subprocess
import platform

# Build configuration
APP_NAME = "TV_Viewer"
MAIN_SCRIPT = "main.py"
ICON_FILE = "tv_viewer.ico"

# Files and folders to include
DATA_FILES = [
    ("config.py", "."),
    ("channels.json", ".") if os.path.exists("channels.json") else None,
]
DATA_FILES = [f for f in DATA_FILES if f is not None]

# Hidden imports that PyInstaller might miss
HIDDEN_IMPORTS = [
    "vlc",
    "aiohttp",
    "asyncio",
    "tkinter",
    "tkinter.ttk",
    "customtkinter",
    "customtkinter.windows",
    "customtkinter.windows.widgets",
    "tkintermapview",
    "tkintermapview.canvas_position_marker",
    "json",
    "threading",
    "queue",
    "pychromecast",
    "zeroconf",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "PIL._tkinter_finder",
    "PIL._imagingtk",
]

# Excluded modules to reduce size
EXCLUDED_MODULES = [
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "cv2",
    "tensorflow",
    "torch",
    "sklearn",
]


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def create_icon():
    """Create the icon file if it doesn't exist."""
    if not os.path.exists(ICON_FILE):
        try:
            from icon import get_icon_path
            icon_path = get_icon_path()
            if icon_path and os.path.exists(icon_path):
                if icon_path != ICON_FILE:
                    shutil.copy(icon_path, ICON_FILE)
                print(f"Icon created: {ICON_FILE}")
        except Exception as e:
            print(f"Could not create icon: {e}")


def clean_build():
    """Clean previous build artifacts."""
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = [f"{APP_NAME}.spec"]
    
    for d in dirs_to_remove:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Removed: {d}")
    
    for f in files_to_remove:
        if os.path.exists(f):
            os.remove(f)
            print(f"Removed: {f}")
    
    # Clean __pycache__ in subdirectories
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                path = os.path.join(root, d)
                shutil.rmtree(path)
                print(f"Removed: {path}")


def build_executable(onefile=True):
    """Build the executable using PyInstaller."""
    check_pyinstaller()
    create_icon()
    
    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--clean",
        "--noconfirm",
    ]
    
    # Single file or directory
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # Windowed mode (no console) - comment out for debugging
    if platform.system() == "Windows":
        cmd.append("--windowed")
    
    # Icon
    if os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])
    
    # Hidden imports
    for imp in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", imp])
    
    # Excluded modules
    for exc in EXCLUDED_MODULES:
        cmd.extend(["--exclude-module", exc])
    
    # Data files
    for src, dst in DATA_FILES:
        if os.path.exists(src):
            sep = ";" if platform.system() == "Windows" else ":"
            cmd.extend(["--add-data", f"{src}{sep}{dst}"])
    
    # Add the main script
    cmd.append(MAIN_SCRIPT)
    
    print("Building with command:")
    print(" ".join(cmd))
    print()
    
    # Run PyInstaller
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)
        
        if onefile:
            if platform.system() == "Windows":
                exe_path = os.path.join("dist", f"{APP_NAME}.exe")
            else:
                exe_path = os.path.join("dist", APP_NAME)
            print(f"\nExecutable: {os.path.abspath(exe_path)}")
        else:
            dist_path = os.path.join("dist", APP_NAME)
            print(f"\nApplication folder: {os.path.abspath(dist_path)}")
        
        print("\nNOTE: VLC must be installed on the target system!")
        print("      Windows: https://www.videolan.org/vlc/")
        print("      Linux: sudo apt install vlc")
    else:
        print("\nBuild failed!")
        return False
    
    return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build TV Viewer executable")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--onefile", action="store_true", help="Build single file (may be blocked by corporate security policies)")
    parser.add_argument("--onedir", action="store_true", default=True, help="Build directory (default, works everywhere)")
    parser.add_argument("--debug", action="store_true", help="Build with console for debugging")
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if args.clean:
        clean_build()
        return
    
    onefile = args.onefile  # Default is onedir unless --onefile explicitly passed
    build_executable(onefile=onefile)


if __name__ == "__main__":
    main()
