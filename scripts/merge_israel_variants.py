"""Second-pass consolidation for known Israeli channel variants."""
import json
import re

# Manual merge map: canonical name -> list of name patterns to merge into it
ISRAEL_MERGE_MAP = {
    "KAN Gimel": ["kan gimel", "כאן גימל"],
    "Galgalatz": ["galgalatz", "galatz 91"],
    "Channel 10 Business": ["channel 10 business"],
    "Channel 11": ["channel 11"],
    "Channel 13": ["channel 13"],
    "Channel 14": ["channel 14"],
    "KAN 11": ["kan 11"],
}

def matches_pattern(name, patterns):
    norm = name.lower().strip()
    for prefix in ['il: ', 'israel: ', 'il:', 'israel:']:
        if norm.startswith(prefix):
            norm = norm[len(prefix):].strip()
    for pat in patterns:
        if pat in norm:
            return True
    return False

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    channels = data.get('channels', data) if isinstance(data, dict) else data
    print(f"Starting: {len(channels)} channels")

    merged_count = 0
    for canonical, patterns in ISRAEL_MERGE_MAP.items():
        # Find all matching channels in Israel
        matching_indices = []
        for i, ch in enumerate(channels):
            if ch.get('country', '').lower() not in ('israel', 'il'):
                continue
            if matches_pattern(ch.get('name', ''), patterns):
                matching_indices.append(i)

        if len(matching_indices) <= 1:
            continue

        # Merge into first match (prefer one with logo or canonical name)
        best_idx = matching_indices[0]
        for idx in matching_indices:
            if channels[idx]['name'] == canonical:
                best_idx = idx
                break
            if channels[idx].get('logo') and not channels[best_idx].get('logo'):
                best_idx = idx

        # Collect all URLs from duplicates
        all_urls = list(channels[best_idx].get('urls', []))
        if channels[best_idx].get('url') and channels[best_idx]['url'] not in all_urls:
            all_urls.insert(0, channels[best_idx]['url'])

        to_remove = []
        for idx in matching_indices:
            if idx == best_idx:
                continue
            ch = channels[idx]
            url = ch.get('url', '')
            urls = ch.get('urls', [])
            if url and url not in all_urls:
                all_urls.append(url)
            for u in urls:
                if u and u not in all_urls:
                    all_urls.append(u)
            to_remove.append(idx)

        if to_remove:
            channels[best_idx]['urls'] = all_urls
            if all_urls:
                channels[best_idx]['url'] = all_urls[0]
            names_merged = [channels[i]['name'] for i in to_remove]
            print(f"  Merged into '{channels[best_idx]['name']}': {names_merged} -> {len(all_urls)} sources")
            merged_count += len(to_remove)

    # Remove merged entries (reverse order to preserve indices)
    to_remove_all = set()
    for canonical, patterns in ISRAEL_MERGE_MAP.items():
        matching_indices = []
        for i, ch in enumerate(channels):
            if ch.get('country', '').lower() not in ('israel', 'il'):
                continue
            if matches_pattern(ch.get('name', ''), patterns):
                matching_indices.append(i)
        if len(matching_indices) > 1:
            best_idx = matching_indices[0]
            for idx in matching_indices:
                if channels[idx]['name'] == canonical:
                    best_idx = idx
                    break
                if channels[idx].get('logo') and not channels[best_idx].get('logo'):
                    best_idx = idx
            for idx in matching_indices:
                if idx != best_idx:
                    to_remove_all.add(idx)

    channels = [ch for i, ch in enumerate(channels) if i not in to_remove_all]
    print(f"\nRemoved {len(to_remove_all)} duplicate entries")
    print(f"Final: {len(channels)} channels")

    if isinstance(data, dict):
        data['channels'] = channels
    with open('channels.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print("Saved.")

if __name__ == '__main__':
    main()
