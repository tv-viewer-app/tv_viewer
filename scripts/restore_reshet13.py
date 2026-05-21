"""Restore Reshet 13 main channel."""
import json

with open("channels.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Known working Reshet 13 streams
reshet13_urls = [
    "https://d18b0e6mopany4.cloudfront.net/out/v1/08bc71621c1541b3a83ad498e2c409e8/index.m3u8",
    "https://stream.theyraonline.com/live/reshet13@live/index.m3u8",
]

existing_urls = {ch.get("url", "") for ch in data["channels"]}

# Add Reshet 13 if not present
added = False
for url in reshet13_urls:
    if url not in existing_urls:
        data["channels"].append({
            "name": "Reshet 13",
            "url": url,
            "category": "General",
            "country": "Israel",
            "logo": "https://upload.wikimedia.org/wikipedia/he/thumb/5/54/Reshet_13_Logo.svg/220px-Reshet_13_Logo.svg.png",
            "media_type": "TV",
            "status": "working",
        })
        added = True
        print(f"Added Reshet 13: {url}")

# Rename "Channel 13" to "Reshet 13" if it's an Israel channel
for ch in data["channels"]:
    if ch.get("name") == "Channel 13" and ch.get("country") == "Israel":
        ch["name"] = "Reshet 13"
        print(f"Renamed Channel 13 → Reshet 13")

with open("channels.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total: {len(data['channels'])} channels")
