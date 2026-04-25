"""Manual GUI test - not part of automated test suite.

Run this to manually test the feedback dialog:
    python3 -m tests.manual_feedback_gui

Expected behavior:
1. Dialog opens with title "Send Feedback"
2. Category dropdown shows: Bug Report, Feature Request, General Feedback, Question
3. Star rating shows 5 stars (clickable)
4. Text area for feedback message
5. Cancel button closes dialog
6. Submit button:
   - Validates feedback is not empty
   - Opens email client with pre-filled message
   - Logs to Supabase (fire-and-forget, no errors shown)
   - Shows success message
   - Closes dialog
"""

import tkinter as tk
from ui.feedback_dialog import show_feedback_dialog


def test_feedback_dialog():
    """Manual test for feedback dialog."""
    root = tk.Tk()
    root.title("Feedback Dialog Test")
    root.geometry("400x200")
    
    # Info label
    info = tk.Label(
        root,
        text="Click the button below to test the feedback dialog.\n\n"
             "Test scenarios:\n"
             "1. Try submitting empty feedback (should show warning)\n"
             "2. Select different categories\n"
             "3. Rate with stars (optional)\n"
             "4. Submit feedback (opens email client)\n"
             "5. Cancel (closes dialog)",
        justify="left",
        padx=20,
        pady=20
    )
    info.pack(expand=True)
    
    # Test button
    btn = tk.Button(
        root,
        text="Open Feedback Dialog",
        command=lambda: show_feedback_dialog(root),
        font=("Segoe UI", 12),
        padx=20,
        pady=10
    )
    btn.pack(pady=20)
    
    root.mainloop()


if __name__ == "__main__":
    print("Starting feedback dialog manual test...")
    print("=" * 60)
    test_feedback_dialog()
