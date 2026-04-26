# Contributing to TV Viewer

Thank you for your interest in contributing to TV Viewer! This is a community-driven project and we welcome contributions of all kinds — from reporting broken channels to submitting code improvements.

## 📺 Contributing Channels

The heart of TV Viewer is its crowdsourced channel list. Here's how you can help:

### Via the App (Easiest)
1. **Report broken channels** — Long-press (Android) or right-click (Windows) any channel and select "Report Broken". This sends an anonymous health report to our shared database so other users benefit immediately.
2. **Submit new channels** — Use the "Add Channel" button in Settings to add a channel URL you've discovered. If it works, it gets shared with the community.

### Via GitHub Issues
1. Go to [GitHub Issues → New Issue](https://github.com/tv-viewer-app/tv_viewer/issues/new/choose)
2. Select the **"Channel Report"** template
3. Provide:
   - Channel name and country
   - Stream URL (m3u8, mpd, or direct stream link)
   - Category (News, Sports, Entertainment, etc.)
   - Whether it's currently working
4. Our maintainers will verify and add it to the channel list

### Bulk Channel Submissions
If you have a list of channels (e.g., an M3U playlist), open an issue with the **"Channel Report"** template and attach the playlist or paste the URLs. We'll review and merge working channels.

## 🐛 Reporting Bugs

Found a bug? We want to know!

1. Go to [GitHub Issues → New Issue](https://github.com/tv-viewer-app/tv_viewer/issues/new?template=bug_report.yml)
2. Select the **"Bug Report"** template
3. Include:
   - **Platform**: Windows / Android / Linux
   - **App version**: Shown in Settings → About
   - **Steps to reproduce**: What did you do?
   - **Expected behavior**: What should have happened?
   - **Actual behavior**: What actually happened?
   - **Screenshots/logs**: If applicable (logs are in the app's Diagnostics screen)

## 💡 Requesting Features

Have an idea to make TV Viewer better?

1. Go to [GitHub Issues → New Issue](https://github.com/tv-viewer-app/tv_viewer/issues/new?template=feature_request.yml)
2. Select the **"Feature Request"** template
3. Describe:
   - What problem does this solve?
   - How should it work?
   - Any examples from other apps?

## 🛠️ Contributing Code

### Prerequisites

- **Python 3.12+** — for the Windows/Linux desktop app
- **Flutter 3.x** — for the Android app
- **VLC media player** — required for Windows video playback
- **Git** — for version control

### Development Setup

#### Windows/Linux Desktop App
```bash
# Clone the repository
git clone https://github.com/tv-viewer-app/tv_viewer.git
cd tv_viewer

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py

# Run tests
python -m pytest tests/ -v
```

#### Android App (Flutter)
```bash
cd flutter_app

# Get dependencies
flutter pub get

# Run on connected device / emulator
flutter run

# Build APK
flutter build apk --release
```

### Workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tv_viewer.git
   ```
3. **Create a branch** for your change:
   ```bash
   git checkout -b feature/my-awesome-feature
   ```
4. **Make your changes** — follow the existing code style
5. **Test** your changes:
   ```bash
   python -m pytest tests/ -v          # Desktop app tests
   cd flutter_app && flutter test      # Flutter app tests
   ```
6. **Commit** with a descriptive message following [Conventional Commits](docs/CONVENTIONAL_COMMITS.md):
   ```bash
   git commit -m "feat: add channel export to M3U format"
   ```
7. **Push** to your fork:
   ```bash
   git push origin feature/my-awesome-feature
   ```
8. **Open a Pull Request** against the `main` branch

### Code Style

- **Python**: Follow PEP 8. Use type hints where practical. Docstrings for public functions.
- **Dart/Flutter**: Follow the [Dart style guide](https://dart.dev/guides/language/effective-dart/style). Use `flutter analyze` before committing.
- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) format (`feat:`, `fix:`, `docs:`, `chore:`, etc.)

### What Makes a Good PR

- ✅ Focused on a single change
- ✅ Includes tests for new functionality
- ✅ Doesn't break existing tests
- ✅ Has a clear description of what and why
- ✅ References related issues (e.g., "Fixes #123")

## 📋 Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. By participating in this project, you agree to:

- **Be respectful** — Treat all contributors with kindness and respect
- **Be constructive** — Provide helpful feedback, not criticism
- **Be inclusive** — Welcome newcomers and help them get started
- **No harassment** — Harassment of any kind is not tolerated
- **Focus on the project** — Keep discussions relevant and productive

Violations can be reported via [GitHub Issues](https://github.com/tv-viewer-app/tv_viewer/issues) (use a private security advisory if sensitive).

## 📖 Project Architecture

For a deeper understanding of the codebase, see:

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design and component overview
- [API.md](docs/API.md) — Internal API reference
- [TEST_PLAN.md](docs/TEST_PLAN.md) — Testing strategy and coverage

## 🙏 Thank You!

Every contribution matters — whether it's reporting a single broken channel, fixing a typo in the docs, or implementing a major feature. TV Viewer is built by its community, and that includes you.

If you enjoy using TV Viewer, consider [buying us a beer 🍺](https://ko-fi.com/tvviewerapp).
