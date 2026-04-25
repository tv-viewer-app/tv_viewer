"""Feedback dialog for collecting user feedback and ratings.

Provides a CustomTkinter dialog for users to submit feedback via email
and optionally logs to Supabase analytics. Follows the pattern from 
Flutter's feedback_service.dart with graceful degradation.
"""

import tkinter as tk
from tkinter import messagebox
import webbrowser
import urllib.parse
import asyncio
import threading
from typing import Optional
import platform
import sys

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from utils.logger import get_logger
from .constants import FluentColorsDark as FluentColors
import config

logger = get_logger(__name__)

# Supabase integration for analytics (fire-and-forget)
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

SUPPORT_URL = "https://github.com/tv-viewer-app/tv_viewer/issues"  # All support via GitHub Issues


class FeedbackDialog:
    """Feedback dialog with email and optional Supabase logging."""
    
    def __init__(self, parent):
        """Initialize feedback dialog.
        
        Args:
            parent: Parent tkinter window
        """
        self.parent = parent
        self.dialog = None
        self.feedback_text = None
        self.rating_var = None
        self.category_var = None
        
    def show(self):
        """Show the feedback dialog."""
        # Create toplevel dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Send Feedback")
        self.dialog.geometry("560x520")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 560) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 520) // 2
        dialog_x = max(0, x)
        dialog_y = max(0, y)
        self.dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        # Configure background
        self.dialog.configure(bg=FluentColors.BG_SOLID)
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main container with padding
        main_frame = tk.Frame(self.dialog, bg=FluentColors.BG_SOLID)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title with icon
        title_frame = tk.Frame(main_frame, bg=FluentColors.BG_SOLID)
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = tk.Label(
            title_frame,
            text="📝 Send Feedback",
            font=("Segoe UI", 18, "bold"),
            fg=FluentColors.TEXT_PRIMARY,
            bg=FluentColors.BG_SOLID
        )
        title_label.pack(side="left")
        
        # Subtitle
        subtitle = tk.Label(
            main_frame,
            text="Help us improve TV Viewer by sharing your thoughts",
            font=("Segoe UI", 10),
            fg=FluentColors.TEXT_SECONDARY,
            bg=FluentColors.BG_SOLID
        )
        subtitle.pack(fill="x", pady=(0, 20))
        
        # Category selection
        category_frame = tk.Frame(main_frame, bg=FluentColors.BG_SOLID)
        category_frame.pack(fill="x", pady=(0, 12))
        
        category_label = tk.Label(
            category_frame,
            text="Category:",
            font=("Segoe UI", 11),
            fg=FluentColors.TEXT_PRIMARY,
            bg=FluentColors.BG_SOLID
        )
        category_label.pack(side="left", padx=(0, 10))
        
        self.category_var = tk.StringVar(value="General")
        category_menu = tk.OptionMenu(
            category_frame,
            self.category_var,
            "Bug Report",
            "Feature Request", 
            "General Feedback",
            "Question"
        )
        category_menu.config(
            font=("Segoe UI", 11),
            bg=FluentColors.CONTROL_DEFAULT,
            fg=FluentColors.TEXT_PRIMARY,
            activebackground=FluentColors.CONTROL_HOVER,
            highlightthickness=1,
            highlightbackground=FluentColors.CONTROL_BORDER,
            relief="solid",
            borderwidth=0,
            width=18
        )
        category_menu["menu"].config(
            font=("Segoe UI", 10),
            bg=FluentColors.CONTROL_DEFAULT,
            fg=FluentColors.TEXT_PRIMARY
        )
        category_menu.pack(side="left", fill="x", expand=True)
        
        # Rating selection
        rating_frame = tk.Frame(main_frame, bg=FluentColors.BG_SOLID)
        rating_frame.pack(fill="x", pady=(0, 12))
        
        rating_label = tk.Label(
            rating_frame,
            text="Rating (optional):",
            font=("Segoe UI", 11),
            fg=FluentColors.TEXT_PRIMARY,
            bg=FluentColors.BG_SOLID
        )
        rating_label.pack(side="left", padx=(0, 10))
        
        # Star rating buttons
        self.rating_var = tk.IntVar(value=0)
        star_frame = tk.Frame(rating_frame, bg=FluentColors.BG_SOLID)
        star_frame.pack(side="left")
        
        for i in range(1, 6):
            star_btn = tk.Button(
                star_frame,
                text="☆",
                font=("Segoe UI", 16),
                fg=FluentColors.TEXT_SECONDARY,
                bg=FluentColors.BG_SOLID,
                activebackground=FluentColors.BG_SOLID,
                relief="flat",
                borderwidth=0,
                cursor="hand2",
                command=lambda rating=i: self._set_rating(rating)
            )
            star_btn.pack(side="left", padx=2)
            star_btn.bind("<Enter>", lambda e, btn=star_btn: btn.config(fg=FluentColors.WARNING))
            star_btn.bind("<Leave>", lambda e, btn=star_btn: btn.config(fg=FluentColors.TEXT_SECONDARY))
        
        # Feedback text area
        text_label = tk.Label(
            main_frame,
            text="Your Feedback:",
            font=("Segoe UI", 11),
            fg=FluentColors.TEXT_PRIMARY,
            bg=FluentColors.BG_SOLID,
            anchor="w"
        )
        text_label.pack(fill="x", pady=(0, 5))
        
        # Text widget with scrollbar
        text_frame = tk.Frame(main_frame, bg=FluentColors.CONTROL_BORDER)
        text_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.feedback_text = tk.Text(
            text_frame,
            font=("Segoe UI", 11),
            bg=FluentColors.CONTROL_DEFAULT,
            fg=FluentColors.TEXT_PRIMARY,
            insertbackground=FluentColors.TEXT_PRIMARY,
            relief="flat",
            borderwidth=0,
            wrap="word",
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.feedback_text.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        scrollbar.config(command=self.feedback_text.yview)
        
        # Placeholder text
        placeholder = "Tell us what you think, report a bug, or request a feature..."
        self.feedback_text.insert("1.0", placeholder)
        self.feedback_text.config(fg=FluentColors.TEXT_DISABLED)
        
        def on_focus_in(event):
            if self.feedback_text.get("1.0", "end-1c") == placeholder:
                self.feedback_text.delete("1.0", "end")
                self.feedback_text.config(fg=FluentColors.TEXT_PRIMARY)
        
        def on_focus_out(event):
            if not self.feedback_text.get("1.0", "end-1c").strip():
                self.feedback_text.insert("1.0", placeholder)
                self.feedback_text.config(fg=FluentColors.TEXT_DISABLED)
        
        self.feedback_text.bind("<FocusIn>", on_focus_in)
        self.feedback_text.bind("<FocusOut>", on_focus_out)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=FluentColors.BG_SOLID)
        button_frame.pack(fill="x")
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Segoe UI", 11),
            bg=FluentColors.CONTROL_DEFAULT,
            fg=FluentColors.TEXT_PRIMARY,
            activebackground=FluentColors.CONTROL_HOVER,
            relief="solid",
            borderwidth=1,
            cursor="hand2",
            command=self._cancel,
            width=12,
            pady=8
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        # Submit button
        submit_btn = tk.Button(
            button_frame,
            text="📧 Send Feedback",
            font=("Segoe UI", 11, "bold"),
            bg=FluentColors.ACCENT,
            fg="#FFFFFF",
            activebackground=FluentColors.ACCENT_DARK,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            command=self._submit,
            width=18,
            pady=8
        )
        submit_btn.pack(side="right")
        
    def _set_rating(self, rating: int):
        """Set the star rating and update UI.
        
        Args:
            rating: Rating from 1-5
        """
        self.rating_var.set(rating)
        
        # Update star display
        star_frame = None
        for child in self.dialog.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Frame):
                        for widget in subchild.winfo_children():
                            if isinstance(widget, tk.Frame):
                                # Find star frame
                                buttons = [w for w in widget.winfo_children() if isinstance(w, tk.Button)]
                                if len(buttons) == 5:
                                    star_frame = widget
                                    break
        
        if star_frame:
            buttons = [w for w in star_frame.winfo_children() if isinstance(w, tk.Button)]
            for i, btn in enumerate(buttons, 1):
                if i <= rating:
                    btn.config(text="★", fg=FluentColors.WARNING)
                else:
                    btn.config(text="☆", fg=FluentColors.TEXT_SECONDARY)
    
    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()
    
    def _submit(self):
        """Submit feedback via email and log to Supabase."""
        # Get feedback text
        feedback = self.feedback_text.get("1.0", "end-1c").strip()
        placeholder = "Tell us what you think, report a bug, or request a feature..."
        
        if not feedback or feedback == placeholder:
            messagebox.showwarning(
                "No Feedback",
                "Please enter your feedback before submitting.",
                parent=self.dialog
            )
            return
        
        category = self.category_var.get()
        rating = self.rating_var.get()
        
        # Log to Supabase (fire-and-forget)
        self._log_to_analytics(category, rating, feedback)
        
        # Open email client
        self._open_email(category, rating, feedback)
        
        # Show confirmation
        messagebox.showinfo(
            "Thank You!",
            "Your feedback has been recorded.\n\n"
            "An email draft has been opened in your email client.\n"
            "Please review and send it to complete the submission.",
            parent=self.dialog
        )
        
        self.dialog.destroy()
    
    def _open_email(self, category: str, rating: int, feedback: str):
        """Open email client with pre-filled feedback.
        
        Args:
            category: Feedback category
            rating: User rating (0-5, 0 means not provided)
            feedback: Feedback message
        """
        # Build email subject
        subject = f"TV Viewer Feedback - {category}"
        
        # Build email body
        body_parts = [
            f"Feedback Category: {category}",
            f"Rating: {'⭐' * rating if rating > 0 else 'Not provided'}",
            "",
            "Feedback:",
            feedback,
            "",
            "---",
            f"App Version: {config.APP_VERSION}",
            f"Platform: {platform.system()} {platform.release()}",
            f"Python: {sys.version.split()[0]}",
        ]
        body = "\n".join(body_parts)
        
        # Create GitHub Issues URL
        issues_url = f"{SUPPORT_URL}/new?title={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        
        try:
            webbrowser.open(issues_url)
            logger.info(f"Opened GitHub Issues for feedback category: {category}")
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            messagebox.showerror(
                "Browser Error",
                "Could not open browser.\n\n"
                f"Please submit feedback at:\n{SUPPORT_URL}",
                parent=self.dialog
            )
    
    def _log_to_analytics(self, category: str, rating: int, feedback: str):
        """Log feedback to Supabase analytics (fire-and-forget).
        
        Args:
            category: Feedback category
            rating: User rating (0-5)
            feedback: Feedback message (truncated for privacy)
        """
        if not AIOHTTP_AVAILABLE:
            return
        
        # Don't log full feedback text for privacy - just metadata
        event_data = {
            "category": category,
            "rating": rating if rating > 0 else None,
            "has_text": len(feedback) > 0,
            "text_length": len(feedback),
        }
        
        # Fire-and-forget in background thread
        def log_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._send_to_supabase(event_data))
                loop.close()
            except Exception as e:
                logger.debug(f"Failed to log feedback to analytics: {e}")
        
        thread = threading.Thread(target=log_async, daemon=True)
        thread.start()
    
    async def _send_to_supabase(self, event_data: dict):
        """Send event to Supabase (async).
        
        Args:
            event_data: Event data dictionary
        """
        try:
            from utils.telemetry import track_feature
            # Use existing telemetry function
            track_feature("feedback_submitted", metadata=event_data)
        except Exception as e:
            logger.debug(f"Supabase logging failed: {e}")


def show_feedback_dialog(parent):
    """Show the feedback dialog.
    
    Args:
        parent: Parent tkinter window
    """
    try:
        dialog = FeedbackDialog(parent)
        dialog.show()
    except Exception as e:
        logger.error(f"Failed to show feedback dialog: {e}")
        messagebox.showerror(
            "Error",
            "Could not open feedback dialog.\n\n"
            f"Please submit feedback at:\n{SUPPORT_URL}"
        )
