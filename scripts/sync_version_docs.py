#!/usr/bin/env python3
"""Sync version-related copy across README.md, docs/index.html, config.py.

Source of truth: the section in CHANGELOG.md for the version passed in.
Run after publishing a release (CI does this automatically), or manually:

    python scripts/sync_version_docs.py 2.9.5
    python scripts/sync_version_docs.py v2.9.5    # 'v' prefix is fine

What it updates:
- README.md     -> "## ✨ What's New in vX.Y.Z" + bullets (replaces the entire
                   What's-New block until the next H2)
- docs/index.html -> "<div class='section-tag'>vX.Y.Z - Latest Release</div>"
                   + the subtitle paragraph following it
- config.py     -> APP_VERSION = "X.Y.Z"

Idempotent: re-running with the same version produces no changes.
Exits 0 if everything matched, 1 on parse errors.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
INDEX_HTML = ROOT / "docs" / "index.html"
CONFIG_PY = ROOT / "config.py"
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_RE = re.compile(r"^v?(\d+\.\d+\.\d+)$")


def parse_version(arg: str) -> str:
    m = VERSION_RE.match(arg.strip())
    if not m:
        sys.exit(f"error: '{arg}' is not a valid semver (expected X.Y.Z or vX.Y.Z)")
    return m.group(1)


def extract_changelog_section(version: str) -> tuple[str, list[str]]:
    """Return (raw_body, bullet_list) for the given version's CHANGELOG entry.

    bullet_list strips the leading '- ' / '* '. raw_body is the full
    sub-section (between '## [version]' and the next '## [' header).
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        sys.exit(f"error: no '## [{version}]' section found in CHANGELOG.md")
    body = m.group(1).strip()
    bullets: list[str] = []
    for line in body.splitlines():
        s = line.lstrip()
        if s.startswith(("- ", "* ")):
            bullets.append(s[2:].strip())
    return body, bullets


def headline_from_bullets(bullets: list[str], max_chars: int = 220) -> str:
    """Build a short marketing-friendly subtitle from up to 3 bullets."""
    if not bullets:
        return "Bug fixes and improvements."
    # Strip markdown emphasis and take the bold lead phrase if present.
    parts: list[str] = []
    for b in bullets[:3]:
        # drop ** markers, drop trailing details after first em-dash/colon
        s = re.sub(r"\*\*", "", b)
        s = re.sub(r":\s.*$", "", s).strip().rstrip(".")
        if s:
            parts.append(s)
    out = "; ".join(parts) + "."
    if len(out) > max_chars:
        out = out[: max_chars - 1].rstrip(",; ") + "..."
    return out


def update_readme(version: str, bullets: list[str]) -> bool:
    src = README.read_text(encoding="utf-8")
    # Region: from "## ✨ What's New in v..." up to (but not including) the
    # next H2 that is NOT one of the legacy "### Earlier in" sub-headings.
    region_re = re.compile(
        r"## \u2728 What's New in v[^\n]*\n.*?(?=^## [^#])",
        re.DOTALL | re.MULTILINE,
    )
    if not region_re.search(src):
        # Fallback: try without the sparkle emoji
        region_re = re.compile(
            r"## What's New in v[^\n]*\n.*?(?=^## [^#])",
            re.DOTALL | re.MULTILINE,
        )
    top_bullets = bullets[:8] if bullets else ["Bug fixes and improvements."]
    bullet_md = "\n".join(f"- {b}" for b in top_bullets)
    new_block = (
        f"## \u2728 What's New in v{version}\n\n"
        f"{bullet_md}\n\n"
        f"_See the [CHANGELOG](CHANGELOG.md) for the full release history._\n\n"
    )
    new_src, n = region_re.subn(new_block, src, count=1)
    if n == 0:
        sys.exit("error: README.md is missing a 'What's New in v...' section to replace")
    if new_src == src:
        return False
    README.write_text(new_src, encoding="utf-8")
    return True


def update_index_html(version: str, subtitle: str) -> bool:
    src = INDEX_HTML.read_text(encoding="utf-8")
    EM = "\u2014"  # em dash — used literally in replacement strings since
                  # re.sub does NOT interpret \uXXXX escapes in replacements.
    changed = False
    # 1. Section tag
    tag_re = re.compile(
        r'(<div class="section-tag">)v\d+\.\d+\.\d+\s*[\u2014\-]\s*Latest Release(</div>)'
    )
    new_src, n1 = tag_re.subn(rf"\1v{version} {EM} Latest Release\2", src)
    if n1 == 0:
        sys.exit("error: docs/index.html missing the 'Latest Release' section-tag")
    # 2. Subtitle paragraph immediately after the section tag inside #whats-new
    #    Matches: <p class="section-subtitle">....</p> on the line(s) after the tag.
    subtitle_re = re.compile(
        r'(<div class="section-tag">v\d+\.\d+\.\d+\s*\u2014\s*Latest Release</div>\s*'
        r'<h2 class="section-title">[^<]*</h2>\s*'
        r'<p class="section-subtitle">)([^<]*)(</p>)',
        re.DOTALL,
    )
    # Escape HTML special chars in the subtitle, plus regex-replacement backslashes.
    safe = (
        subtitle.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    new_src, n2 = subtitle_re.subn(
        lambda m: m.group(1) + safe + m.group(3), new_src
    )
    if n2 == 0:
        # Keep the tag update even if subtitle pattern fails - just warn.
        print("warning: could not locate landing-page subtitle paragraph; left unchanged")
    if new_src != src:
        INDEX_HTML.write_text(new_src, encoding="utf-8")
        changed = True
    return changed


def update_config_py(version: str) -> bool:
    src = CONFIG_PY.read_text(encoding="utf-8")
    new_src, n = re.subn(
        r'^APP_VERSION\s*=\s*["\'][^"\']+["\']',
        f'APP_VERSION = "{version}"',
        src,
        count=1,
        flags=re.MULTILINE,
    )
    if n == 0:
        sys.exit("error: config.py missing APP_VERSION assignment")
    if new_src == src:
        return False
    CONFIG_PY.write_text(new_src, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: sync_version_docs.py <version>")
        return 2
    version = parse_version(argv[1])
    body, bullets = extract_changelog_section(version)
    subtitle = headline_from_bullets(bullets)

    print(f"Syncing docs to v{version}")
    print(f"  Subtitle: {subtitle}")
    print(f"  Bullets:  {len(bullets)} from CHANGELOG")

    changes: list[str] = []
    if update_readme(version, bullets):
        changes.append("README.md")
    if update_index_html(version, subtitle):
        changes.append("docs/index.html")
    if update_config_py(version):
        changes.append("config.py")

    if changes:
        print("Updated: " + ", ".join(changes))
    else:
        print("No changes (already in sync).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
