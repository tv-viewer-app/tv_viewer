"""Fix mojibake (garbled encoding) in channel names across all languages.

The channels.json has names that were multi-encoded:
  Original UTF-8 → misread as CP437/Latin-1 → stored as UTF-8 again

This script tries multiple decode chains and picks the one that produces
valid text without box-drawing or control characters.
"""

import json
import re
import sys
from pathlib import Path

CHANNELS_FILE = Path(__file__).parent.parent / "channels.json"

# Characters that indicate mojibake (box-drawing, partial sequences)
MOJIBAKE_CHARS = set('\u251c\u2500\u2502\u2514\u252c\u2518\u250c\u2510\u253c\u2524\u251c\u2534\u00c3\u00c2\u00c4\u00c5\u00c6\u00c9\u00e2\u00e3\u00e4')

# Box-drawing range used by CP437 mojibake
BOX_DRAWING = re.compile(r'[\u2500-\u257F]')

# Pattern: sequences like ├â┬í or ├É┬║ (double-encoded UTF-8 via CP437)
DOUBLE_ENCODED = re.compile(r'[\u00C0-\u00FF][\u00A0-\u00BF\u0080-\u009F]|[\u251c\u2500-\u257f][\u00a0-\u00ff\u2500-\u257f]+')


def try_fix_name(name: str) -> str:
    """Attempt to decode a mojibake name back to proper UTF-8."""
    if not any(c in name for c in '\u251c\u2500\u2502\u2514\u252c\u2518\u250c\u2510\u253c\u2524\u2534\u00c3\u00c2\u00c4\u00c5\u00c9\u00e3\u00e2'):
        return name  # No mojibake indicators
    
    # Strategy 1: CP437 decode → UTF-8 (common for box-drawing chars)
    try:
        decoded = name.encode('cp437').decode('utf-8')
        if not BOX_DRAWING.search(decoded) and is_readable(decoded):
            return decoded
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    
    # Strategy 2: Latin-1 decode → UTF-8 (common for Ã/Â sequences)
    try:
        decoded = name.encode('latin-1').decode('utf-8')
        if not BOX_DRAWING.search(decoded) and is_readable(decoded):
            return decoded
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    
    # Strategy 3: CP437 → UTF-8, then Latin-1 → UTF-8 (triple encoding)
    try:
        step1 = name.encode('cp437').decode('utf-8')
        decoded = step1.encode('latin-1').decode('utf-8')
        if not BOX_DRAWING.search(decoded) and is_readable(decoded):
            return decoded
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    
    # Strategy 4: Windows-1252 decode → UTF-8
    try:
        decoded = name.encode('windows-1252').decode('utf-8')
        if not BOX_DRAWING.search(decoded) and is_readable(decoded):
            return decoded
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    
    # Strategy 5: CP437 → Latin-1 → UTF-8 (variant order)
    try:
        step1 = name.encode('cp437').decode('latin-1')
        decoded = step1.encode('latin-1').decode('utf-8')
        if not BOX_DRAWING.search(decoded) and is_readable(decoded):
            return decoded
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    
    return name  # Give up, return original


def is_readable(text: str) -> bool:
    """Check if text looks like a real channel name (no garbage chars)."""
    # Must not have box-drawing characters
    if BOX_DRAWING.search(text):
        return False
    # Must not have excessive control characters
    control = sum(1 for c in text if ord(c) < 32 and c not in '\n\r\t')
    if control > 0:
        return False
    # Should have mostly printable chars
    printable = sum(1 for c in text if c.isprintable())
    return printable >= len(text) * 0.8


def main():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    channels = data["channels"]
    fixed_count = 0
    removed_count = 0
    clean_channels = []
    
    for ch in channels:
        name = ch.get("name", "")
        if not name:
            clean_channels.append(ch)
            continue
        
        # Try to fix mojibake
        new_name = try_fix_name(name)
        
        # If still has box-drawing after all attempts, remove channel
        if BOX_DRAWING.search(new_name):
            removed_count += 1
            continue
        
        if new_name != name:
            fixed_count += 1
            ch["name"] = new_name
        
        clean_channels.append(ch)
    
    data["channels"] = clean_channels
    
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Fixed: {fixed_count} channel names")
    print(f"Removed: {removed_count} unfixable channels")
    print(f"Remaining: {len(clean_channels)} channels")


if __name__ == "__main__":
    main()
