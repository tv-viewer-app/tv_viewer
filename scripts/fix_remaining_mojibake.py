"""Fix remaining mojibake edge cases and deduplicate."""
import json
import re

with open("channels.json", "r", encoding="utf-8") as f:
    data = json.load(f)

fixed = 0
for ch in data["channels"]:
    name = ch.get("name", "")
    orig = name
    # Fix Windows-1252 via Latin-1 mojibake patterns
    name = name.replace("\u0393\u00c7\u00aa", "\u2026")  # ellipsis
    name = name.replace("\u0393\u00c7\u00d6", "\u2019")  # right single quote
    name = name.replace("\u0393\u00c7\u00f4", "\u2013")  # en-dash
    name = name.replace("\u0393\u00c7\u00d2", "\u201c")  # left double quote
    name = name.replace("\u0393\u00c7\u00d3", "\u201d")  # right double quote
    # Fix partial ÃÄ → Óč (Óčko Expres, Óčko Gold)
    if "\u00c3\u00c4" in name:
        name = name.replace("\u00c3\u00c4", "\u00d3\u010d")
    if name != orig:
        ch["name"] = name
        fixed += 1

# Deduplicate by (name, url)
seen = set()
deduped = []
for ch in data["channels"]:
    key = (ch.get("name", ""), ch.get("url", ""))
    if key in seen:
        continue
    seen.add(key)
    deduped.append(ch)

removed = len(data["channels"]) - len(deduped)
data["channels"] = deduped

with open("channels.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Fixed {fixed} names, removed {removed} duplicates")
print(f"Total channels: {len(deduped)}")
