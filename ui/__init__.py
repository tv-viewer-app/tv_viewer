"""UI components for TV Viewer.

Heavy window modules are loaded lazily so importing a lightweight dialog or
compatibility helper does not initialize VLC or other optional UI dependencies.
"""

from .constants import MaterialColors

__all__ = [
    "MaterialColors",
    "MainWindow",
    "PlayerWindow",
    "ScanAnimationWidget",
    "ScanProgressFrame",
]


def __getattr__(name):
    if name == "MainWindow":
        from .main_window import MainWindow

        return MainWindow
    if name == "PlayerWindow":
        from .player_window import PlayerWindow

        return PlayerWindow
    if name in {"ScanAnimationWidget", "ScanProgressFrame"}:
        from .scan_animation import ScanAnimationWidget, ScanProgressFrame

        return {
            "ScanAnimationWidget": ScanAnimationWidget,
            "ScanProgressFrame": ScanProgressFrame,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
