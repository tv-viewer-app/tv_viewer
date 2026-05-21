"""Clean misclassified Israel channels - remove non-Israeli content from Israel country."""
import json
import re

# Known legitimate Israeli channel name patterns
ISRAELI_PATTERNS = [
    r'^100fm', r'^102fm', r'^103fm', r'^106\.4', r'^88fm', r'^99\.?5?fm', r'^99fm',
    r'angel tv hebrew', r'audiversity', r'big brother',
    r'channel 1[0-4]', r'channel 9$',  # Channel 9 is Russian-Israeli
    r'diki radio', r'eco99', r'galei zahal', r'galgalatz',
    r'hakatze', r'i24', r'kan ', r'keshet', r'knesset',
    r'kol chai', r'kol play', r'makan', r'music 24',
    r'reshet', r'hot ', r'yes ', r'sport ?5',
    r'il:', r'israel:',
    # Hebrew names
    r'[\u0590-\u05FF]',  # Any Hebrew char
    r'[\u0600-\u06FF]',  # Arabic (for Arabic Israeli channels like Makan)
]

# Definitely NOT Israeli
NOT_ISRAELI_PATTERNS = [
    r'paradise hotel', r'bob esponja', r'construcciones',
    r'comunicaciones', r'arroyo grande', r'bac kan tv',
    r'baby shark', r'babyfirst', r'channel 9 melbourne',
    r'cosmote', r'donna shopping', r'eagle one',
    r'freedom love zone', r'global news', r'hadi tv',
    r'télé', r'television la brise', r'radio y telev',
    r'die sieben', r'millionen.*frau',
    r'tempe channel', r'the national channel 10',
    r'okanagan', r'finalveckan', r'pandoras ask', r'skolveckan',
    r'pantalones', r'cuadrados',
]

def is_likely_israeli(name):
    """Check if a channel name looks Israeli."""
    name_lower = name.lower().strip()
    for pat in ISRAELI_PATTERNS:
        if re.search(pat, name_lower):
            return True
    return False

def is_definitely_not_israeli(name):
    """Check if a channel is definitely not Israeli."""
    name_lower = name.lower().strip()
    for pat in NOT_ISRAELI_PATTERNS:
        if re.search(pat, name_lower):
            return True
    return False

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    channels = data.get('channels', data) if isinstance(data, dict) else data

    reclassified = []
    for ch in channels:
        if ch.get('country', '').lower() not in ('israel', 'il'):
            continue
        name = ch.get('name', '')
        if is_definitely_not_israeli(name):
            ch['country'] = 'Unknown'
            reclassified.append(name)
        elif not is_likely_israeli(name):
            # Check if it looks foreign
            name_lower = name.lower()
            # Non-Israeli indicators: Spanish, German, French, Swedish, etc.
            foreign_indicators = [
                'tv indonesian', 'melbourne', 'okanagan', 'eagle one',
                'donna', 'cosmote', 'freedom love', 'global news',
            ]
            if any(ind in name_lower for ind in foreign_indicators):
                ch['country'] = 'Unknown'
                reclassified.append(name)

    print(f"Reclassified {len(reclassified)} channels out of Israel:")
    for name in sorted(reclassified):
        print(f"  - {name}")

    # Save
    if isinstance(data, dict):
        data['channels'] = channels
    with open('channels.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    # Count remaining Israel
    israel_count = sum(1 for ch in channels if ch.get('country', '').lower() in ('israel', 'il'))
    print(f"\nRemaining Israel channels: {israel_count}")

if __name__ == '__main__':
    main()
