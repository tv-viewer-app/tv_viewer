"""Consolidate duplicate channels into single entries with multiple sources (urls array)."""
import json
import re
from collections import defaultdict

def normalize_name(name):
    """Normalize channel name for dedup matching."""
    norm = name.strip().lower()
    # Remove common prefixes
    for prefix in ['il: ', 'israel: ', 'il:', 'israel:', 'us: ', 'uk: ']:
        if norm.startswith(prefix):
            norm = norm[len(prefix):].strip()
    # Normalize whitespace
    norm = re.sub(r'\s+', ' ', norm)
    # Remove trailing HD/SD/FHD markers
    norm = re.sub(r'\s*(hd|sd|fhd|4k)\s*$', '', norm)
    return norm

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    channels = data.get('channels', data) if isinstance(data, dict) else data
    print(f"Starting channels: {len(channels)}")

    # Group by normalized name + country
    groups = defaultdict(list)
    for i, ch in enumerate(channels):
        name = ch.get('name', '').strip()
        country = ch.get('country', 'Unknown').strip()
        norm = normalize_name(name)
        key = (norm, country.lower())
        groups[key].append(i)

    # Count duplicates
    dupe_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Duplicate groups (same name+country): {len(dupe_groups)}")

    # Show top examples
    print("\nTop duplicates:")
    sorted_dupes = sorted(dupe_groups.items(), key=lambda x: -len(x[1]))
    for (norm, country), indices in sorted_dupes[:20]:
        names = [channels[i]['name'] for i in indices]
        print(f"  {norm} ({country}): {len(indices)} copies - {names[:3]}")

    # Consolidate: keep first entry, merge all URLs into urls[]
    consolidated = []
    seen_groups = set()

    for i, ch in enumerate(channels):
        name = ch.get('name', '').strip()
        country = ch.get('country', 'Unknown').strip()
        norm = normalize_name(name)
        key = (norm, country.lower())

        if key in seen_groups:
            continue  # Skip duplicates already processed
        seen_groups.add(key)

        group_indices = groups[key]
        if len(group_indices) == 1:
            # No duplicates - keep as-is
            consolidated.append(ch)
        else:
            # Merge: collect all unique URLs
            all_urls = []
            best_entry = None
            best_name = ''

            for idx in group_indices:
                entry = channels[idx]
                # Prefer entry with logo, or longest name, or first
                entry_name = entry.get('name', '')
                if best_entry is None:
                    best_entry = entry
                    best_name = entry_name
                elif entry.get('logo') and not best_entry.get('logo'):
                    best_entry = entry
                    best_name = entry_name
                elif len(entry_name) > len(best_name) and not best_entry.get('logo'):
                    best_entry = entry
                    best_name = entry_name

                # Collect URLs
                url = entry.get('url', '')
                urls = entry.get('urls', [])
                if url and url not in all_urls:
                    all_urls.append(url)
                for u in urls:
                    if u and u not in all_urls:
                        all_urls.append(u)

            # Build consolidated entry
            merged = dict(best_entry)
            merged['urls'] = all_urls
            if all_urls:
                merged['url'] = all_urls[0]
            consolidated.append(merged)

    print(f"\nAfter consolidation: {len(consolidated)} channels (removed {len(channels) - len(consolidated)} duplicates)")

    # Save
    if isinstance(data, dict):
        data['channels'] = consolidated
    with open('channels.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    print("Saved channels.json")

if __name__ == '__main__':
    main()
