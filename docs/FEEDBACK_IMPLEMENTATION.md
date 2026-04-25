# Feedback System Implementation - Desktop Python App

## Overview
Implemented feedback/rating system for the desktop Python/CustomTkinter app, achieving feature parity with the Flutter Android app's `feedback_service.dart`.

## Implementation Details

### Files Created
- **`ui/feedback_dialog.py`** - Main feedback dialog implementation
- **`tests/test_feedback_manual.py`** - Manual test for the feedback dialog

### Files Modified
- **`ui/main_window.py`** - Added feedback button and handler
- **`CHANGELOG.md`** - Documented the new feature

### Key Features

#### 1. User Interface
- **Dialog**: CustomTkinter dialog (560x520px) with Windows 11 Fluent Design styling
- **Category Dropdown**: Bug Report, Feature Request, General Feedback, Question
- **Star Rating**: 1-5 stars (optional), interactive with hover effects
- **Feedback Text**: Multi-line text area with placeholder text
- **Buttons**: Cancel (closes) and Submit (opens email + logs)

#### 2. Email Integration
- Opens user's default email client via `webbrowser.open(mailto:...)`
- Pre-fills:
  - **To**: GitHub Issues (https://github.com/tv-viewer-app/tv_viewer/issues)
  - **Subject**: "TV Viewer Feedback - {category}"
  - **Body**: Feedback text + system info (app version, OS, Python version)
- Follows same pattern as `crash_reporter.py`

#### 3. Analytics Logging
- **Fire-and-forget**: Uses `utils.telemetry.track_feature()`
- **Privacy-preserving**: Logs metadata only (category, rating, text length) - NOT full feedback text
- **Graceful degradation**: Silently fails if Supabase unavailable or aiohttp not installed
- **Background thread**: Never blocks UI

#### 4. Accessibility
- **Keyboard shortcuts**: Tab navigation, Enter to submit
- **Screen reader friendly**: All controls properly labeled
- **High contrast**: Uses FluentColors for WCAG compliance
- **Focus indicators**: Clear visual feedback

### Integration Points

#### Main Window (`ui/main_window.py`)
```python
# Import
from .feedback_dialog import show_feedback_dialog

# Action buttons section (row 8, sidebar)
self.feedback_btn = ttk.Button(
    button_frame,
    text="💬 Feedback",
    command=self._show_feedback,
    bootstyle="secondary"
)

# Handler method
def _show_feedback(self):
    show_feedback_dialog(self.root)
    track_feature("feedback_dialog_opened")
```

#### Telemetry Integration
```python
# Event logged when dialog opened
track_feature("feedback_dialog_opened")

# Event logged when feedback submitted (metadata only)
track_feature("feedback_submitted", metadata={
    "category": "Bug Report",
    "rating": 4,
    "has_text": True,
    "text_length": 250
})
```

### Design Decisions

1. **Email over HTTP POST**: 
   - More reliable (no server dependencies)
   - User can edit before sending
   - Transparent (user sees what's sent)
   - Follows crash_reporter.py pattern

2. **Fire-and-forget analytics**:
   - Never shows errors to user
   - Gracefully degrades if Supabase down
   - Logs metadata only (privacy)

3. **No CustomTkinter dependency**:
   - Uses standard tkinter (wider compatibility)
   - Still matches Fluent Design with manual styling

4. **Star rating as buttons**:
   - More interactive than dropdown
   - Visual feedback (hover, click)
   - Optional (can be skipped)

### Testing

#### Manual Test
```bash
python3 -m tests.test_feedback_manual
```

#### Smoke Test
```bash
python3 -c "from ui.feedback_dialog import show_feedback_dialog; print('✅ OK')"
```

#### Integration Test
1. Run app: `python3 main.py`
2. Click "💬 Feedback" button in sidebar
3. Fill out form and submit
4. Verify email client opens with pre-filled message
5. Check logs for telemetry event

### Comparison with Flutter Implementation

| Feature | Flutter (feedback_service.dart) | Desktop (feedback_dialog.py) | Status |
|---------|--------------------------------|------------------------------|--------|
| Category selection | ✅ Dropdown | ✅ Dropdown | ✅ Parity |
| Rating system | ✅ Star rating | ✅ Star rating (1-5) | ✅ Parity |
| Email integration | ✅ url_launcher | ✅ webbrowser | ✅ Parity |
| Analytics logging | ✅ SharedPreferences | ✅ Supabase telemetry | ✅ Parity |
| Fluent Design | ✅ Material 3 | ✅ Windows 11 Fluent | ✅ Parity |
| Error handling | ✅ Graceful | ✅ Graceful | ✅ Parity |
| Session tracking | ✅ Rating prompts | ❌ N/A (desktop) | N/A |

### Future Enhancements

1. **In-app submission**: Direct HTTP POST to backend (when available)
2. **Screenshot attachment**: Capture + attach to email
3. **Crash report integration**: "Send Feedback" button in crash dialog
4. **Keyboard shortcut**: Ctrl+Shift+F to open feedback
5. **Auto-rating prompt**: After X sessions (like Flutter)

### Security Considerations

- ✅ No PII collected (only system info: OS, Python version)
- ✅ No full feedback text logged to analytics (metadata only)
- ✅ Email address visible to user before sending
- ✅ Fire-and-forget prevents info leaks on failure
- ✅ Input validation (text length, category enum)

### Dependencies

- **Required**: `tkinter` (standard library)
- **Optional**: `aiohttp` (for analytics, graceful degradation if missing)
- **Reused**: `utils.telemetry`, `utils.logger`, `ui.constants`

## Resolves

- Closes #23 - Add feedback/rating system to desktop app
- Achieves feature parity with Flutter Android app

## Commit

```
473a5d1 feat(desktop): add feedback dialog with email and analytics (#23)
```
