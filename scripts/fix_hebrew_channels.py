"""Fix Hebrew/Arabic channel names (triple-encoded mojibake) and remove misclassified Israel channels."""
import json
import sys

def fix_triple_encode(text):
    """Decode: UTF-8 interpreted as CP437, then Latin-1 re-encoded as UTF-8."""
    if not text:
        return text
    try:
        step1 = text.encode('cp437').decode('utf-8')
        step2 = step1.encode('latin-1').decode('utf-8')
        return step2
    except (UnicodeDecodeError, UnicodeEncodeError):
        return None

def has_hebrew(text):
    return any('\u0590' <= c <= '\u05FF' for c in text)

def has_arabic(text):
    return any('\u0600' <= c <= '\u06FF' for c in text)

# Known misclassified channels (not Israeli)
MISCLASSIFIED_NAMES = {
    "Best of Paradise Hotel: Kyssar",  # Swedish
    "Comunicaciones Jiménez",  # Spanish
    "Radio y Televisión Budokan",  # Spanish
    "Télévision La Brise",  # French
    "Die Sieben-Millionen-Dollar-Frau",  # German
}

def is_misclassified_israel(ch):
    """Detect channels that shouldn't be in Israel."""
    name = ch.get('name', '')
    # Known misclassified
    for bad in MISCLASSIFIED_NAMES:
        if bad in name:
            return True
    # "Tempe Channel 11" - Arizona US
    if 'tempe' in name.lower() and 'channel' in name.lower():
        return True
    # "The National Channel 10" - not Israeli Channel 10
    if name.lower() == 'the national channel 10':
        return True
    return False

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    channels = data.get('channels', data) if isinstance(data, dict) else data

    # 1. Fix triple-encoded Hebrew/Arabic names
    fixed_count = 0
    for ch in channels:
        name = ch.get('name', '')
        if '\u251c' in name or '\u252c' in name or '\u2310' in name:
            result = fix_triple_encode(name)
            if result and (has_hebrew(result) or has_arabic(result)):
                ch['name'] = result
                fixed_count += 1

    # 2. Also fix names with ╫ pattern (different mojibake variant)
    for ch in channels:
        name = ch.get('name', '')
        if '\u256b' in name or ('\u256b' <= name[:1] <= '\u256f' if name else False):
            result = fix_triple_encode(name)
            if result and (has_hebrew(result) or has_arabic(result)):
                ch['name'] = result
                fixed_count += 1

    # 3. Remove misclassified Israel channels
    removed = []
    israel_channels = [ch for ch in channels if ch.get('country', '').lower() in ('israel', 'il')]
    for ch in israel_channels:
        if is_misclassified_israel(ch):
            ch['country'] = 'Unknown'
            removed.append(ch['name'])

    # 4. Find Israel channels that look non-Israeli (German, French, Swedish names)
    german_words = ['die ', 'der ', 'das ', 'und ', 'frau', 'mann', 'sieben']
    french_words = ['télé', 'chaîne', 'brise']
    swedish_words = ['kyssar', 'kärlek']
    
    for ch in channels:
        if ch.get('country', '').lower() not in ('israel', 'il'):
            continue
        name_lower = ch.get('name', '').lower()
        if any(w in name_lower for w in german_words + french_words + swedish_words):
            if not has_hebrew(ch.get('name', '')):
                ch['country'] = 'Unknown'
                removed.append(ch['name'])

    # Save
    if isinstance(data, dict):
        data['channels'] = channels
    with open('channels.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    print(f"Fixed {fixed_count} Hebrew/Arabic channel names")
    print(f"Reclassified {len(removed)} misclassified channels from Israel:")
    for name in removed:
        print(f"  - {name}")

if __name__ == '__main__':
    main()
