"""Shared normalization logic for categories and countries.

This module is the single source of truth for category and country naming.
All clients (Web/Docker, Desktop, Flutter) must produce identical results
for the same raw input. Flutter uses a Dart port of this logic.

Usage::

    from utils.normalize import normalize_category, normalize_country, CANONICAL_CATEGORIES
"""

from __future__ import annotations
import re

# ─── Canonical category list ─────────────────────────────────────────────────
# These are the ONLY categories that should appear in any client.
# Kept small and meaningful. Anything not mapping here goes to "General".
CANONICAL_CATEGORIES = sorted([
    "Documentary",
    "Education",
    "Entertainment",
    "General",
    "Kids",
    "Lifestyle",
    "Movies",
    "Music",
    "Nature",
    "News",
    "Radio",
    "Religious",
    "Shopping",
    "Sports",
])


# ─── Category normalization map ──────────────────────────────────────────────
# Maps raw category strings (lowercase) → canonical category name.
# Consolidated to 14 canonical categories only.
_CATEGORY_MAP: dict[str, str] = {
    # ── Xumous-prefixed ──
    "xumous: action & drama": "Movies",
    "xumous: animals & nature": "Nature",
    "xumous: automotive": "Lifestyle",
    "xumous: black voices. black stories.": "Entertainment",
    "xumous: classic tv": "Entertainment",
    "xumous: combat sports": "Sports",
    "xumous: comedy": "Entertainment",
    "xumous: crime tv": "Movies",
    "xumous: daytime tv": "Entertainment",
    "xumous: faith & family": "Religious",
    "xumous: food": "Lifestyle",
    "xumous: game shows": "Entertainment",
    "xumous: game show": "Entertainment",
    "xumous: history & learning": "Documentary",
    "xumous: home & design": "Lifestyle",
    "xumous: horror & sci-fi": "Movies",
    "xumous: kids": "Kids",
    "xumous: latino": "Entertainment",
    "xumous: local news": "News",
    "xumous: movies": "Movies",
    "xumous: music & radio": "Music",
    "xumous: music": "Music",
    "xumous: news": "News",
    "xumous: pop culture": "Entertainment",
    "xumous: reality tv": "Entertainment",
    "xumous: reality": "Entertainment",
    "xumous: sports": "Sports",
    "xumous: travel & lifestyle": "Lifestyle",
    "xumous: travel": "Lifestyle",
    "xumous: food & travel": "Lifestyle",
    "xumous: food+travel": "Lifestyle",
    "xumous: lifestyle": "Lifestyle",
    "xumous: documentary": "Documentary",
    "xumous: education": "Education",
    "xumous: shopping": "Shopping",
    "xumous: religious": "Religious",
    # ── Semicolon-delimited compounds ──
    "animation;entertainment": "Kids",
    "animation;kids": "Kids",
    "animation;kids;religious": "Kids",
    "culture;entertainment": "Entertainment",
    "news;entertainment": "News",
    "sports;entertainment": "Sports",
    "music;entertainment": "Music",
    "music;lifestyle": "Music",
    "documentary;education": "Documentary",
    "kids;education": "Kids",
    "movies;entertainment": "Movies",
    "movies;drama": "Movies",
    "lifestyle;entertainment": "Lifestyle",
    "food;lifestyle": "Lifestyle",
    "food;travel": "Lifestyle",
    "travel;lifestyle": "Lifestyle",
    # ── Messy values → canonical ──
    "undefined": "General",
    "other": "General",
    "uncategorized": "General",
    "general": "General",
    "none": "General",
    "n/a": "General",
    "tv": "General",
    # ── Merged: Action/Crime/Drama/Comedy/Series → Movies or Entertainment ──
    "action": "Movies",
    "action & drama": "Movies",
    "action sports": "Sports",
    "adventure": "Movies",
    "animation": "Kids",
    "animated": "Kids",
    "anime": "Kids",
    "classic": "Entertainment",
    "classic tv": "Entertainment",
    "classics": "Entertainment",
    "westerns + classics": "Entertainment",
    "western": "Entertainment",
    "comedy": "Entertainment",
    "comedy drama": "Entertainment",
    "crime": "Movies",
    "crime drama": "Movies",
    "crime tv": "Movies",
    "drama": "Movies",
    "fiction": "Movies",
    "horror": "Movies",
    "sci-fi": "Movies",
    "horror & sci-fi": "Movies",
    "series": "Entertainment",
    "reality": "Entertainment",
    "reality tv": "Entertainment",
    "talk": "Entertainment",
    "game shows": "Entertainment",
    "game show": "Entertainment",
    "daytime tv": "Entertainment",
    "pop culture": "Entertainment",
    # ── Merged: Cooking/Food/Travel/Auto/Culture/Health → Lifestyle ──
    "cooking": "Lifestyle",
    "food": "Lifestyle",
    "food & travel": "Lifestyle",
    "food+travel": "Lifestyle",
    "travel": "Lifestyle",
    "travel & lifestyle": "Lifestyle",
    "auto": "Lifestyle",
    "automotive": "Lifestyle",
    "culture": "Lifestyle",
    "culture + lifestyle": "Lifestyle",
    "home & design": "Lifestyle",
    "health": "Lifestyle",
    "relax": "Lifestyle",
    "outdoor": "Lifestyle",
    # ── Merged: Business/Technology/Science/Weather → Education ──
    "business": "Education",
    "bus./financial": "Education",
    "technology": "Education",
    "computers": "Education",
    "tech": "Education",
    "science": "Education",
    "weather": "Education",
    "gaming": "Education",
    # ── Movies ──
    "movies": "Movies",
    "cinema": "Movies",
    "film": "Movies",
    "vod movies (en)": "Movies",
    "vod italy": "Movies",
    "spain vod": "Movies",
    "usa vod": "Movies",
    # ── Kids ──
    "kids": "Kids",
    "family": "Kids",
    "children": "Kids",
    "children-music": "Kids",
    # ── Sports ──
    "sports": "Sports",
    "sport": "Sports",
    "baseball": "Sports",
    "basketball": "Sports",
    "boxing": "Sports",
    "bullfighting": "Sports",
    "football": "Sports",
    "soccer": "Sports",
    "tennis": "Sports",
    "cricket": "Sports",
    "golf": "Sports",
    "motorsport": "Sports",
    "wrestling": "Sports",
    "combat sports": "Sports",
    # ── Shopping ──
    "shop": "Shopping",
    "shopping": "Shopping",
    "auction": "Shopping",
    "teleshopping": "Shopping",
    # ── Documentary ──
    "documentary": "Documentary",
    "documentaries": "Documentary",
    "documentaries (ar)": "Documentary",
    "documentaries (en)": "Documentary",
    "history": "Documentary",
    "history & learning": "Documentary",
    # ── News ──
    "news": "News",
    "local news": "News",
    "legislative": "News",
    # ── Religious ──
    "religious": "Religious",
    "faith & family": "Religious",
    # ── Education ──
    "education": "Education",
    # ── Music ──
    "music": "Music",
    "music & radio": "Music",
    # ── Radio ──
    "radio": "Radio",
    # ── Nature ──
    "nature": "Nature",
    "animals": "Nature",
    "animals & nature": "Nature",
    "wildlife": "Nature",
    # ── Entertainment ──
    "entertainment": "Entertainment",
    # ── Lifestyle ──
    "lifestyle": "Lifestyle",
    # ── Regional variants ──
    "en español": "Entertainment",
    "en espa&ñol": "Entertainment",
    "en espaã±ol": "Entertainment",
    "latino": "Entertainment",
    # ── Adult → General (hidden but not broken) ──
    "adult": "General",
    "xxx": "General",
}

# ─── Name-based classification patterns ──────────────────────────────────────
# Used when category is "General"/"Other" to infer category from channel name.
_NAME_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Radio", re.compile(
        r'(?:\b\d{2,3}\.\d\s)|(?:\b(?:fm|radio)\b)',
        re.IGNORECASE
    )),
    ("Music", re.compile(
        r'\b(?:hits|jazz|rock|oldies|hitz|reggae|hip.?hop|r&b|soul|blues|'
        r'techno|edm|salsa|symphony|orchestra|mizrahi|mizrahit|playlist|'
        r'classic rock|smooth jazz|country music|pop music)\b',
        re.IGNORECASE
    )),
    ("News", re.compile(
        r'\b(?:news|noticias|cnn|bbc news|fox news|msnbc|cnbc|al.?jazeera|'
        r'headline|infowars)\b',
        re.IGNORECASE
    )),
    ("Sports", re.compile(
        r'\b(?:sport|soccer|football|basketball|tennis|cricket|golf|racing|'
        r'boxing|ufc|mma|nba|nfl|mlb|nhl|espn|bein|dazn)\b',
        re.IGNORECASE
    )),
    ("Religious", re.compile(
        r'(?:\b(?:church|gospel|prayer|faith|islam|quran|torah|kabbalah|'
        r'breslov|christian|bible|kol chai)\b|ברסלב|הלכ|דף יומי|שיעור|הרב)',
        re.IGNORECASE
    )),
    ("Kids", re.compile(
        r'\b(?:kids|cartoon|nick|disney|toon|boomerang|pbs kids|sesame)\b',
        re.IGNORECASE
    )),
    ("Shopping", re.compile(
        r'\b(?:qvc|hsn|teleshopping|shop\s*tv|my\s*shop)\b',
        re.IGNORECASE
    )),
]


def normalize_category(raw: str | None, channel_name: str | None = None) -> str:
    """Normalize a raw category string to a canonical category name.

    Rules (in order):
    1. Direct map lookup (case-insensitive)
    2. Strip "Xumous:" or similar vendor prefixes → re-lookup
    3. Split on semicolons → take first part → re-lookup
    4. Split on " + " → take first part → re-lookup
    5. If result is still "General" and channel_name given, try name patterns
    6. Default to "General"

    Args:
        raw: The raw category string from M3U/database.
        channel_name: Optional channel name for name-based inference.
    """
    if not raw or not raw.strip():
        result = "General"
    else:
        cat = raw.strip()
        key = cat.lower()

        # Direct lookup
        mapped = _CATEGORY_MAP.get(key)
        if mapped:
            result = mapped
        else:
            # Strip vendor prefix (e.g., "Xumous: Comedy" → "Comedy")
            if ':' in key:
                after_colon = cat.split(':', 1)[1].strip()
                mapped = _CATEGORY_MAP.get(after_colon.lower())
                if mapped:
                    result = mapped
                else:
                    cat = after_colon
                    key = cat.lower()

            if not mapped:
                # Semicolon split → first part
                if ';' in cat:
                    first = cat.split(';')[0].strip()
                    mapped = _CATEGORY_MAP.get(first.lower())
                    if mapped:
                        result = mapped
                    else:
                        cat = first
                        key = cat.lower()

            if not mapped:
                # " + " split → first part
                if ' + ' in cat:
                    first = cat.split(' + ')[0].strip()
                    mapped = _CATEGORY_MAP.get(first.lower())
                    if mapped:
                        result = mapped
                    else:
                        cat = first

            if not mapped:
                # Check if it matches a canonical name
                title = cat.title() if (cat == cat.lower() or cat == cat.upper()) else cat
                if title in CANONICAL_CATEGORIES:
                    result = title
                else:
                    result = "General"

    # Name-based inference when category is General and we have a name
    if result == "General" and channel_name:
        name = channel_name.strip()
        if name:
            for cat_name, pattern in _NAME_PATTERNS:
                if pattern.search(name):
                    result = cat_name
                    break

    return result


# ─── Country normalization ────────────────────────────────────────────────────
# Canonical country names — ISO 3166-1 alpha-2 → full name
COUNTRY_CODES: dict[str, str] = {
    "AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan",
    "AL": "Albania", "AM": "Armenia", "AO": "Angola", "AR": "Argentina",
    "AT": "Austria", "AU": "Australia", "AZ": "Azerbaijan", "BA": "Bosnia",
    "BD": "Bangladesh", "BE": "Belgium", "BG": "Bulgaria", "BH": "Bahrain",
    "BO": "Bolivia", "BR": "Brazil", "BY": "Belarus", "CA": "Canada",
    "CH": "Switzerland", "CL": "Chile", "CN": "China", "CO": "Colombia",
    "CR": "Costa Rica", "CU": "Cuba", "CY": "Cyprus", "CZ": "Czech Republic",
    "DE": "Germany", "DK": "Denmark", "DO": "Dominican Republic",
    "DZ": "Algeria", "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt",
    "ES": "Spain", "ET": "Ethiopia", "FI": "Finland", "FR": "France",
    "GB": "United Kingdom", "GE": "Georgia", "GH": "Ghana", "GR": "Greece",
    "GT": "Guatemala", "HK": "Hong Kong", "HN": "Honduras", "HR": "Croatia",
    "HU": "Hungary", "ID": "Indonesia", "IE": "Ireland", "IL": "Israel",
    "IN": "India", "IQ": "Iraq", "IR": "Iran", "IS": "Iceland", "IT": "Italy",
    "JM": "Jamaica", "JO": "Jordan", "JP": "Japan", "KE": "Kenya",
    "KR": "South Korea", "KW": "Kuwait", "KZ": "Kazakhstan", "LB": "Lebanon",
    "LK": "Sri Lanka", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia",
    "LY": "Libya", "MA": "Morocco", "MD": "Moldova", "ME": "Montenegro",
    "MK": "North Macedonia", "MM": "Myanmar", "MN": "Mongolia", "MX": "Mexico",
    "MY": "Malaysia", "NG": "Nigeria", "NL": "Netherlands", "NO": "Norway",
    "NP": "Nepal", "NZ": "New Zealand", "OM": "Oman", "PA": "Panama",
    "PE": "Peru", "PH": "Philippines", "PK": "Pakistan", "PL": "Poland",
    "PR": "Puerto Rico", "PS": "Palestine", "PT": "Portugal", "PY": "Paraguay",
    "QA": "Qatar", "RO": "Romania", "RS": "Serbia", "RU": "Russia",
    "SA": "Saudi Arabia", "SD": "Sudan", "SE": "Sweden", "SG": "Singapore",
    "SI": "Slovenia", "SK": "Slovakia", "SN": "Senegal", "SO": "Somalia",
    "SV": "El Salvador", "SY": "Syria", "TH": "Thailand", "TN": "Tunisia",
    "TR": "Turkey", "TT": "Trinidad", "TW": "Taiwan", "UA": "Ukraine",
    "US": "USA", "UY": "Uruguay", "UZ": "Uzbekistan", "VE": "Venezuela",
    "VN": "Vietnam", "YE": "Yemen", "ZA": "South Africa",
}

# Common aliases that appear in M3U data
_COUNTRY_ALIASES: dict[str, str] = {
    "uk": "United Kingdom",
    "us": "USA",
    "usa": "USA",
    "united states": "USA",
    "united states of america": "USA",
    "uae": "United Arab Emirates",
    "korea": "South Korea",
    "republic of korea": "South Korea",
    "czech": "Czech Republic",
    "czechia": "Czech Republic",
    "bosnia and herzegovina": "Bosnia",
    "trinidad and tobago": "Trinidad",
    "hong kong sar": "Hong Kong",
    "democratic republic of the congo": "Congo",
    "ivory coast": "Ivory Coast",
    "côte d'ivoire": "Ivory Coast",
}


def normalize_country(raw: str | None) -> str:
    """Normalize a raw country string to a canonical full country name.

    Rules:
    1. Empty/null → "Unknown"
    2. 2-letter ISO code → lookup in COUNTRY_CODES
    3. Known alias → canonical name
    4. Semicolon-separated → take first, re-normalize
    5. Otherwise return as-is (title-cased if all-lower/all-upper)
    """
    if not raw or not raw.strip() or raw.strip().lower() in ("unknown", "undefined", "n/a", ""):
        return "Unknown"

    country = raw.strip()

    # ISO 2-letter code
    if len(country) == 2 and country.isalpha():
        return COUNTRY_CODES.get(country.upper(), country.upper())

    # Alias lookup
    alias = _COUNTRY_ALIASES.get(country.lower())
    if alias:
        return alias

    # Semicolon-separated (iptv-org format) — take first
    if ';' in country:
        first = country.split(';')[0].strip()
        return normalize_country(first)

    # Already a known full name? (check values)
    if country in COUNTRY_CODES.values():
        return country

    # Title-case cleanup
    if country == country.lower() or country == country.upper():
        country = country.title()

    return country
