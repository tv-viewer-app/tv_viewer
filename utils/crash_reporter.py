"""Anonymous crash reporting via GitHub Issues.

This module provides automatic crash reporting by creating GitHub issues
when unhandled exceptions occur. No user data is collected - only crash
details needed to diagnose and fix the issue.

Privacy:
- No user identifying information collected
- No IP addresses or location data
- No system usernames or paths (sanitized)
- Only technical crash data: traceback, OS, Python version, app version
"""

import sys
import platform
import traceback
import webbrowser
import urllib.parse
import re
import logging
from typing import Optional
from datetime import datetime

import config

logger = logging.getLogger(__name__)

# GitHub repository for issue creation
GITHUB_REPO = "arielsaghiv/tv_viewer"
GITHUB_ISSUES_URL = f"https://github.com/{GITHUB_REPO}/issues/new"


def sanitize_path(text: str) -> str:
    """Remove user-identifying paths from text.
    
    Replaces paths like C:\\Users\\username\\... with [USER_PATH]
    to protect privacy while keeping useful debug info.
    """
    # Windows paths
    text = re.sub(r'[A-Za-z]:\\Users\\[^\\]+', '[USER_PATH]', text)
    text = re.sub(r'[A-Za-z]:\\Documents and Settings\\[^\\]+', '[USER_PATH]', text)
    # Unix paths
    text = re.sub(r'/home/[^/]+', '[USER_PATH]', text)
    text = re.sub(r'/Users/[^/]+', '[USER_PATH]', text)
    # Environment variables that might contain usernames
    text = re.sub(r'%USERPROFILE%', '[USER_PATH]', text)
    text = re.sub(r'\$HOME', '[USER_PATH]', text)
    return text


def get_system_info() -> str:
    """Get sanitized system information for crash report."""
    info = []
    info.append(f"- **App Version:** {config.APP_VERSION}")
    info.append(f"- **Python:** {platform.python_version()}")
    info.append(f"- **OS:** {platform.system()} {platform.release()}")
    info.append(f"- **Architecture:** {platform.machine()}")
    return "\n".join(info)


def categorize_exception(exc_type: type, exc_value: Exception) -> str:
    """Categorize the exception for the issue label."""
    exc_name = exc_type.__name__
    
    # Network errors
    if any(x in exc_name for x in ['Connection', 'Timeout', 'SSL', 'HTTP', 'URL', 'Socket']):
        return "bug/network"
    
    # UI errors
    if any(x in exc_name for x in ['Tcl', 'Tk', 'Widget', 'Window', 'GUI']):
        return "bug/ui"
    
    # File errors
    if any(x in exc_name for x in ['File', 'IO', 'Permission', 'Path']):
        return "bug/filesystem"
    
    # Import errors
    if 'Import' in exc_name or 'Module' in exc_name:
        return "bug/dependency"
    
    # Memory errors
    if 'Memory' in exc_name:
        return "bug/performance"
    
    # General
    return "bug"


def format_crash_report(
    exc_type: type,
    exc_value: Exception,
    exc_tb,
    context: Optional[str] = None
) -> tuple[str, str]:
    """Format exception into a GitHub issue title and body.
    
    Returns:
        Tuple of (title, body) for the issue
    """
    # Get sanitized traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    tb_text = sanitize_path("".join(tb_lines))
    
    # Limit traceback length for URL
    if len(tb_text) > 2000:
        tb_text = tb_text[:1000] + "\n...[truncated]...\n" + tb_text[-1000:]
    
    # Create title
    exc_name = exc_type.__name__
    exc_msg = str(exc_value)[:80] if exc_value else "No message"
    exc_msg = sanitize_path(exc_msg)
    title = f"[Crash] {exc_name}: {exc_msg}"
    
    # Create body
    category = categorize_exception(exc_type, exc_value)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    body = f"""## Crash Report

**Timestamp:** {timestamp}
**Category:** {category}

### System Information
{get_system_info()}

### Context
{context or "Application crash"}

### Exception
```
{exc_name}: {sanitize_path(str(exc_value))}
```

### Traceback
```python
{tb_text}
```

---
*This crash report was generated automatically. No personal data was collected.*
"""
    
    return title, body


def create_github_issue_url(title: str, body: str, labels: list[str] = None) -> str:
    """Create a GitHub new issue URL with pre-filled content.
    
    Args:
        title: Issue title
        body: Issue body (markdown)
        labels: Optional list of labels
        
    Returns:
        URL that opens GitHub new issue page with pre-filled content
    """
    params = {
        "title": title[:256],  # GitHub title limit
        "body": body[:65000],  # URL length safety
    }
    
    if labels:
        params["labels"] = ",".join(labels)
    
    return f"{GITHUB_ISSUES_URL}?{urllib.parse.urlencode(params)}"


def report_crash(
    exc_type: type,
    exc_value: Exception,
    exc_tb,
    context: Optional[str] = None,
    auto_open: bool = True
) -> Optional[str]:
    """Report a crash by opening a GitHub issue.
    
    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_tb: Exception traceback
        context: Optional context string describing what was happening
        auto_open: If True, automatically open browser to create issue
        
    Returns:
        The GitHub issue URL, or None if failed
    """
    try:
        title, body = format_crash_report(exc_type, exc_value, exc_tb, context)
        category = categorize_exception(exc_type, exc_value)
        
        url = create_github_issue_url(title, body, labels=[category, "crash-report"])
        
        if auto_open:
            webbrowser.open(url)
            logger.info(f"Opened crash report in browser")
        
        return url
        
    except Exception as e:
        logger.error(f"Failed to create crash report: {e}")
        return None


def install_global_handler():
    """Install global exception handler that reports crashes.
    
    This replaces sys.excepthook to catch unhandled exceptions
    and offer to report them via GitHub issues.
    """
    original_hook = sys.excepthook
    
    def crash_handler(exc_type, exc_value, exc_tb):
        """Global exception handler."""
        # Don't report KeyboardInterrupt or SystemExit
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            original_hook(exc_type, exc_value, exc_tb)
            return
        
        # Log the error
        logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_tb)
        )
        
        # Try to show a dialog and report
        try:
            from tkinter import messagebox
            import tkinter as tk
            
            # Create hidden root if needed
            try:
                root = tk._default_root
                if root is None:
                    root = tk.Tk()
                    root.withdraw()
            except Exception:
                root = None
            
            # Ask user if they want to report
            result = messagebox.askyesno(
                "TV Viewer - Crash Detected",
                f"An error occurred:\n\n{exc_type.__name__}: {str(exc_value)[:100]}\n\n"
                "Would you like to report this crash?\n\n"
                "(This will open GitHub to create an issue. No personal data is collected.)",
                icon='error'
            )
            
            if result:
                report_crash(exc_type, exc_value, exc_tb, auto_open=True)
                
        except Exception as dialog_error:
            logger.error(f"Could not show crash dialog: {dialog_error}")
            # Still try to report
            report_crash(exc_type, exc_value, exc_tb, auto_open=True)
        
        # Call original hook
        original_hook(exc_type, exc_value, exc_tb)
    
    sys.excepthook = crash_handler
    logger.debug("Installed global crash handler")


def report_error_manually(error: Exception, context: str = "Manual report"):
    """Manually report an error (for caught exceptions).
    
    Use this for errors that are caught but still worth reporting.
    
    Args:
        error: The exception that occurred
        context: Description of what was happening
    """
    try:
        report_crash(
            type(error),
            error,
            error.__traceback__,
            context=context,
            auto_open=True
        )
    except Exception as e:
        logger.error(f"Failed to report error: {e}")
