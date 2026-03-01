# Conventional Commits Quick Reference

Quick reference for writing conventional commits that work with our automated release workflow.

## Basic Format

```
<type>[(optional scope)]: <description>

[optional body]

[optional footer(s)]
```

## Commit Types

| Type | When to Use | Appears In Release |
|------|-------------|-------------------|
| `feat` | Adding a new feature | ✨ New Features |
| `fix` | Fixing a bug | 🐛 Bug Fixes |
| `perf` | Performance improvement | ⚡ Performance Improvements |
| `refactor` | Code restructuring (no functionality change) | ♻️ Code Refactoring |
| `docs` | Documentation only | 📚 Documentation |
| `style` | Code style/formatting (no code change) | 💄 Style |
| `test` | Adding or updating tests | ✅ Tests |
| `build` | Build system or external dependencies | 🔧 Build System |
| `ci` | CI/CD configuration changes | 👷 CI/CD |
| `chore` | Other changes (no production code change) | 📦 Other Changes |

## Quick Examples

### Features
```bash
git commit -m "feat: add channel search"
git commit -m "feat(ui): implement dark mode"
git commit -m "feat(player): add volume controls"
```

### Bug Fixes
```bash
git commit -m "fix: resolve crash on startup"
git commit -m "fix(android): fix video playback stutter"
git commit -m "fix(database): prevent duplicate channels"
```

### Performance
```bash
git commit -m "perf: optimize video buffer"
git commit -m "perf(ui): reduce memory usage"
```

### Refactoring
```bash
git commit -m "refactor: simplify channel manager"
git commit -m "refactor(core): extract playlist parser"
```

### Documentation
```bash
git commit -m "docs: update installation guide"
git commit -m "docs: add API documentation"
```

### Build/CI
```bash
git commit -m "build: update PyInstaller config"
git commit -m "ci: add automated release workflow"
```

### Tests
```bash
git commit -m "test: add unit tests for player"
git commit -m "test: add integration tests"
```

## Breaking Changes

Use `!` after type or add `BREAKING CHANGE:` in footer:

```bash
# Method 1: Using !
git commit -m "feat!: redesign settings API"

# Method 2: In footer
git commit -m "feat: redesign settings API

BREAKING CHANGE: Settings now use class-based API instead of dict"
```

## Scopes (Optional)

Add scope for better organization:

```bash
feat(ui): add search bar         # UI-related feature
fix(android): resolve crash      # Android-specific fix
perf(player): optimize buffer    # Player performance
docs(api): update endpoints      # API documentation
```

Common scopes:
- `ui` - User interface
- `android` - Android app
- `windows` - Windows app
- `player` - Video player
- `database` - Database operations
- `api` - API changes
- `core` - Core functionality

## Multi-line Commits

For detailed changes:

```bash
git commit -m "feat: add EPG support

- Fetch program guide from API
- Display current/next programs  
- Add schedule view
- Cache EPG data locally

Resolves #15"
```

## Tips

✅ **DO:**
- Use present tense: "add feature" not "added feature"
- Start with lowercase: "feat: add" not "feat: Add"
- Keep first line under 72 characters
- Be specific and descriptive
- Reference issue numbers in footer

❌ **DON'T:**
- Use generic messages: "fix stuff", "updates"
- Mix multiple types in one commit
- Include irrelevant changes
- Forget the colon after type

## Common Patterns

### Feature Implementation
```bash
git commit -m "feat(ui): add channel favorites

Users can now mark channels as favorites and access them
from a dedicated favorites section.

Resolves #23"
```

### Bug Fix
```bash
git commit -m "fix(player): prevent video freeze on network loss

Added connection monitoring and automatic reconnection.

Fixes #42"
```

### Dependency Update
```bash
git commit -m "build: update dependencies

- python-vlc 3.0.18122 → 3.0.20123
- customtkinter 5.2.0 → 5.2.1
- flutter 3.19.0 → 3.19.1"
```

## Integration with Release Workflow

When you push a tag:
```bash
git tag v1.10.0
git push origin v1.10.0
```

The workflow will:
1. Find all commits since last tag (e.g., `v1.9.0..v1.10.0`)
2. Parse each commit by type
3. Group into categories
4. Generate release notes automatically

## Example Release Notes Output

From these commits:
```
feat: add channel search
feat(ui): implement dark mode
fix: resolve crash on startup
fix(player): prevent video freeze
perf: optimize video buffer
docs: update README
ci: add release workflow
```

Generates:
```markdown
## ✨ New Features
- add channel search
- implement dark mode

## 🐛 Bug Fixes
- resolve crash on startup
- prevent video freeze

## ⚡ Performance Improvements
- optimize video buffer

## 📚 Documentation
- update README

## 👷 CI/CD
- add release workflow
```

## More Information

- Full specification: https://www.conventionalcommits.org/
- Release process: See RELEASE_PROCESS.md
- Workflow file: .github/workflows/release.yml

## IDE Integration

### VS Code
Install extension: **Conventional Commits**
- Provides commit message template
- Validates format
- Suggests types

### IntelliJ/PyCharm
Install plugin: **Git Commit Template**
- Commit message templates
- Type suggestions

### Git Hook (Optional)
Add `.git/hooks/commit-msg` to enforce format:
```bash
#!/bin/sh
commit_msg=$(cat "$1")
pattern="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?: .{1,}"

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "ERROR: Commit message doesn't follow conventional commits format"
    echo "Format: <type>[(scope)]: <description>"
    echo "Example: feat: add channel search"
    exit 1
fi
```
