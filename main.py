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

# Enable Windows DPI awareness for proper font/UI scaling
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

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

# Security: Remove CWD from DLL search path to mitigate DLL hijacking (Windows)
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.kernel32.SetDllDirectoryW("")
    except Exception:
        pass

# Configure VLC for PyInstaller executables (Issue #35)
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable - ensure VLC can find system libraries
    import ctypes.util
    
    # Add common VLC library paths to LD_LIBRARY_PATH
    vlc_lib_paths = [
        '/usr/lib/x86_64-linux-gnu',
        '/usr/lib64',
        '/usr/lib',
        '/usr/local/lib',
    ]
    
    # Set VLC plugin path to system location
    vlc_plugin_paths = [
        '/usr/lib/x86_64-linux-gnu/vlc/plugins',
        '/usr/lib64/vlc/plugins',
        '/usr/lib/vlc/plugins',
        '/usr/local/lib/vlc/plugins',
    ]
    
    # Find and set VLC_PLUGIN_PATH
    for plugin_path in vlc_plugin_paths:
        if os.path.exists(plugin_path):
            os.environ['VLC_PLUGIN_PATH'] = plugin_path
            print(f"VLC plugin path set to: {plugin_path}")
            break
    
    # Ensure LD_LIBRARY_PATH includes VLC libraries
    ld_path = os.environ.get('LD_LIBRARY_PATH', '')
    for lib_path in vlc_lib_paths:
        if os.path.exists(lib_path) and lib_path not in ld_path:
            if ld_path:
                ld_path = f"{lib_path}:{ld_path}"
            else:
                ld_path = lib_path
    
    if ld_path:
        os.environ['LD_LIBRARY_PATH'] = ld_path
        print(f"LD_LIBRARY_PATH configured for VLC")


# SECURITY: Package names below are hardcoded — NEVER load from external config.
# __import__() is called with these names for dependency checking.
REQUIRED_PACKAGES = {
    'ttkbootstrap': ('ttkbootstrap', '1.10.0'),
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
            # Try to get version and enforce minimum
            version = getattr(module, '__version__', None) or getattr(module, 'VERSION', None)
            if version and version != 'unknown':
                try:
                    from packaging.version import Version
                    if Version(str(version)) < Version(min_version):
                        warnings.append(
                            f"{package_name} {version} is below minimum {min_version} — please upgrade"
                        )
                except Exception:
                    # packaging not available — fall back to simple tuple comparison
                    try:
                        cur = tuple(int(x) for x in str(version).split('.')[:3])
                        req = tuple(int(x) for x in min_version.split('.')[:3])
                        if cur < req:
                            warnings.append(
                                f"{package_name} {version} is below minimum {min_version} — please upgrade"
                            )
                    except (ValueError, TypeError):
                        pass  # unparseable version — skip check
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
    
    # Install crash reporter early
    try:
        from utils.crash_reporter import install_global_handler
        install_global_handler()
        print("Crash reporter installed")
    except Exception as e:
        print(f"Warning: Could not install crash reporter: {e}")
    
    # Initialize anonymous analytics (non-blocking, fail-safe)
    try:
        import asyncio
        from utils.analytics import analytics
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(analytics.initialize())
            loop.run_until_complete(analytics.track_app_launch())
        finally:
            loop.close()
        print("Analytics initialized")
    except Exception as e:
        print(f"Warning: Analytics init skipped: {e}")
    
    # Check requirements first
    success, missing, warnings = check_requirements()
    
    if not success:
        show_requirements_error(missing)
        sys.exit(1)
    
    # Show warnings for optional packages
    for warning in warnings:
        print(f"Warning: {warning}")
    
    # Register cleanup on exit (flush analytics before exit)
    def _cleanup():
        try:
            import asyncio
            from utils.analytics import analytics
            # Create a fresh event loop for shutdown — the main loop may already
            # be closed by the time atexit handlers fire.
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(analytics.flush())
            finally:
                loop.close()
        except Exception:
            pass
        cleanup_temp_files()
    
    atexit.register(_cleanup)
    
    # Check for VLC (already in optional packages but provide install hint)
    try:
        import vlc
        print("VLC library found")
    except ImportError:
        print("Warning: python-vlc not installed.")
        print("Install with: pip install python-vlc")
        print("Also ensure VLC media player is installed on your system.")
        print()
    
    # ── First-run consent dialog (Feature #140) ──────────────────────
    # Show before MainWindow creation so the user can decline and exit.
    if not getattr(config, 'CONSENT_ACCEPTED', False):
        try:
            import tkinter as _tk
            _consent_root = _tk.Tk()
            _consent_root.withdraw()
            # Enable DPI awareness for the consent dialog on Windows
            try:
                _consent_root.tk.call('tk', 'scaling', 1.0)
            except Exception:
                pass
            from ui.consent_dialog import show_consent_dialog
            consent_result = show_consent_dialog(_consent_root)
            _consent_root.destroy()
            if not consent_result.get('accepted', False):
                print("User declined consent. Exiting.")
                sys.exit(0)
            # Persist consent
            config.CONSENT_ACCEPTED = True
            config.TELEMETRY_ENABLED = consent_result.get('analytics', False)
            # Save consent state to channels_config.json
            import json as _json
            _cfg_path = config.CHANNELS_CONFIG_FILE
            _cfg_data = {}
            try:
                if os.path.exists(_cfg_path):
                    with open(_cfg_path, 'r', encoding='utf-8') as _f:
                        _cfg_data = _json.load(_f)
            except Exception:
                pass
            _cfg_data['consent_accepted'] = True
            _cfg_data['analytics_enabled'] = consent_result.get('analytics', False)
            try:
                with open(_cfg_path, 'w', encoding='utf-8') as _f:
                    _json.dump(_cfg_data, _f, indent=2, ensure_ascii=False)
            except Exception:
                pass
        except SystemExit:
            raise
        except Exception as e:
            print(f"Warning: Consent dialog failed: {e}")
            # Allow app to continue if dialog fails

    # Import after path setup and requirements check
    # Bug #107: Wrap MainWindow creation in try/except with error dialog fallback
    try:
        from ui.main_window import MainWindow
        
        # Create and run the main window
        app = MainWindow()
        app.run()
    except Exception as e:
        import traceback
        error_msg = f"Fatal error: {e}\n\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        # Show GUI error dialog if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "TV Viewer - Fatal Error",
                f"The application encountered a fatal error and must close.\n\n{e}\n\n"
                "Check the log file for details."
            )
            root.destroy()
        except Exception:
            pass
        sys.exit(1)
    
    # Explicit cleanup after mainloop exits
    _cleanup()


if __name__ == "__main__":
    main()
