"""Structured logging system for TV Viewer application.

Provides rotating file logs with proper formatting for debugging and support.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime

# Get base directory from config or use default
try:
    import config
    LOG_DIR = os.path.join(config.BASE_DIR, "logs")
except ImportError:
    LOG_DIR = os.path.join(os.path.expanduser("~"), ".tv_viewer", "logs")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Log file path
LOG_FILE = os.path.join(LOG_DIR, "tv_viewer.log")

# Create formatter
_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create file handler with rotation (10MB max, keep 5 backups)
_file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
_file_handler.setFormatter(_formatter)
_file_handler.setLevel(logging.DEBUG)

# Create console handler for warnings and above
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_formatter)
_console_handler.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handlers if not already added
    if not logger.handlers:
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
        logger.setLevel(logging.DEBUG)
    
    return logger


def set_debug_mode(enabled: bool = True):
    """Enable or disable debug output to console.
    
    Args:
        enabled: If True, show DEBUG level messages on console
    """
    _console_handler.setLevel(logging.DEBUG if enabled else logging.WARNING)


def get_log_file_path() -> str:
    """Get the path to the current log file.
    
    Returns:
        Full path to log file
    """
    return LOG_FILE


# Create root logger for the application
root_logger = get_logger("tv_viewer")
root_logger.info(f"TV Viewer logging initialized - Log file: {LOG_FILE}")
