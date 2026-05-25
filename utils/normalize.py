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
    "Weather",
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
    # ── Merged: Business/Technology/Science → Education ──
    "business": "Education",
    "bus./financial": "Education",
    "technology": "Education",
    "computers": "Education",
    "tech": "Education",
    "science": "Education",
    "gaming": "Education",
    # ── Weather (its own category) ──
    "weather": "Weather",
    "weather & traffic": "Weather",
    "meteo": "Weather",
    "forecast": "Weather",
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
# Order matters — first match wins. Put specific/unambiguous patterns first.
#
# Word-boundary notes:
#   - \b only fires between word/non-word chars. It does NOT trigger between
#     lowercase and uppercase in CamelCase (e.g. "AccuWeather"), so for
#     compound brand names we use (?<![A-Za-z]) lookbehinds or omit the left \b.
_NAME_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Weather first — distinctive keywords, low false-positive risk
    ("Weather", re.compile(
        # Catches: Weather Channel, AccuWeather, WeatherNation, WeatherScan,
        # WeatherStar, Local Now Weather, BBC Weather, Météo, El Tiempo TV,
        # Wetter, Previsioni, Forecast
        r'(?:accuweather|weathernation|weatherscan|weatherstar|'
        r'\bweather\b|weather(?=[A-Z])|(?<=[a-z])weather|'
        r'\bm[eé]t[eé]o\b|\bmeteo(?:rolog|sat)|\bforecast\b|\bwetter\b|'
        r'\bprevisioni\b|\bel\s+tiempo\b)',
        re.IGNORECASE
    )),
    # Shopping — specific brands & generic terms
    ("Shopping", re.compile(
        r'\b(?:qvc|hsn\d?|teleshopping|telemarket|shop(?:ping)?\s*tv|'
        r'my\s*shop|gem\s+shopping|jewelry\s+(?:tv|television)|'
        r'shinsegae\s+shopping|gongyoung\s+shopping|kshopping|'
        r'home\s+shopping|donna\s+shopping)\b',
        re.IGNORECASE
    )),
    # Religious
    ("Religious", re.compile(
        r'(?:\b(?:church|gospel|prayer|faith|islam|quran|torah|kabbalah|'
        r'breslov|christian|bible|kol chai|tbn|godtv|hillsong|daystar|'
        r'3abn|ewtn|catholic)\b|ברסלב|הלכ|דף יומי|שיעור|הרב)',
        re.IGNORECASE
    )),
    # Kids
    ("Kids", re.compile(
        r'\b(?:kids|cartoon|cartoonito|nick(?:toons|jr)?|disney|toon|'
        r'boomerang|pbs\s*kids|sesame|babytv|baby\s*tv|pokemon|peppa|'
        r'paw\s*patrol|cocomelon|barbie|teletoon|dreamworks|moonbug)\b',
        re.IGNORECASE
    )),
    # Sports — brand + generic
    ("Sports", re.compile(
        r'\b(?:sport|soccer|football|basketball|tennis|cricket|golf|racing|'
        r'boxing|ufc|mma|nba|nfl|mlb|nhl|espn|bein\s*sports?|dazn|sportsnet|'
        r'wwe|fightbox|premier\s*league|champions\s*league|formula\s*1)\b',
        re.IGNORECASE
    )),
    # News — brand + generic + local US affiliates
    ("News", re.compile(
        r'(?:\b(?:news|noticias|noticieros|cnn|bbc\s*news|fox\s*news|msnbc|'
        r'cnbc|al.?jazeera|headline|infowars|newsmax|newsy|newsnation|'
        r'cheddar|bloomberg|reuters|sky\s*news|euronews|france\s*24|'
        r'dw\s*english|i24|democracy\s*now|oann)\b|'
        # US local-affiliate prefixes like "ABC 10", "FOX 5", "NBC Bay Area"
        r'\b(?:abc|cbs|nbc|fox|pbs)\s*(?:\d{1,3}|news|bay\s*area|denver|'
        r'chicago|boston|miami|atlanta|seattle|dallas|houston|phoenix|'
        r'philadelphia|orlando|tampa|portland|sacramento|cleveland|'
        r'wkbw|wcpo|wsbtv|kgo|wabc|kcal|wbtv|wfaa|wxyz|whas|kfor|wgme|'
        r'wbbm|wfor|wnbc|wcbs|kabc|knbc|kcbs|kxan|wbal)\b)',
        re.IGNORECASE
    )),
    # Documentary — true crime, history, science, biography
    ("Documentary", re.compile(
        r'(?:\b(?:nat\s*geo|national\s*geographic|smithsonian|history\s*channel|'
        r'discovery|animal\s*planet|investigation\s*discovery|biography|'
        r'forensic(?:\s*files)?|true\s*crime|crime\s*\+?\s*investigation|'
        r'a&e|cold\s*case|crime\s*360|60\s*days\s*in|'
        r'chaos\s*on\s*cam|documentary|docu\s*box|'
        r'killer|killers|murder|murders|evil|infamous|'
        r'mystery|mysteries|unsolved|paranormal|prison|jail|'
        r'detective|investigation|world\s*war|wwii|wwi)\b|'
        r'\bcrime\b(?!\s*news)|'  # "Crime" alone but not "Crime News"
        r'\b(?:american|world)\s+crimes?\b)',
        re.IGNORECASE
    )),
    # Movies — cinema brands and dedicated movie networks
    ("Movies", re.compile(
        r'\b(?:cinema|movies?\s*(?:channel|network|tv|box|max)?|'
        r'mgm\s*(?:presents|gold|movies?)|filmrise|cineplex|'
        r'action\s*hollywood|cinemax|hbo\s*(?:movie|max)|stirr\s*movies|'
        r'pluto\s*movies|tubi\s*movies|popcornflix|crackle\s*movies|'
        r'grit\s*xtra|hallmark\s*movies|lifetime\s*movies)\b',
        re.IGNORECASE
    )),
    # Lifestyle — cooking, travel, home, fashion
    ("Lifestyle", re.compile(
        r'\b(?:food\s*(?:network|tv|channel)?|cooking\s*(?:channel)?|'
        r'cuisine|chef\s*tv|tasty|kitchen(?:\s+nightmares)?|hells?\s*kitchen|'
        r'bake\s*off|baking|recipe|americas?\s*test\s*kitchen|'
        r'travel\s*(?:channel|tv|network)?|wanderlust|destination\s*tv|'
        r'fashion\s*(?:tv|one|channel)?|fashionbox|hgtv|magnolia|'
        r'home\s*(?:&|and)\s*garden|gardening|diy\s*network|design\s*network|'
        r'love\s*nature\s*lifestyle|lifestyle)\b',
        re.IGNORECASE
    )),
    # Music — brand + genre keywords (use \b to avoid MMTV-like false positives)
    ("Music", re.compile(
        r'\b(?:mtv(?:\s+\w+)?|vh1|vevo|music\s*box|stingray|trace\s*urban|'
        r'deluxe\s*music|kiss\s*tv|qmusic|nrj|hits|jazz|rock|oldies|hitz|'
        r'reggae|hip.?hop|r&b|soul|blues|techno|edm|salsa|symphony|orchestra|'
        r'mizrahi|mizrahit|playlist|classic\s*rock|smooth\s*jazz|'
        r'country\s*music|pop\s*music)\b',
        re.IGNORECASE
    )),
    # Radio — last, very broad pattern (genre keywords + US/CA call signs)
    ("Radio", re.compile(
        # Frequencies (e.g. "101.5 FM", "88.0", "107FM", "91 FM"),
        # FM/AM/radio keywords (with or without word boundary — catches
        # "107FM" where \bfm fails because 7→F has no \b),
        # US/CA call signs at start of name, station codes like "93X" "97X".
        r'(?:\b\d{2,3}\.\d\b)|'                # 101.5
        r'(?:\b\d{2,4}\s*(?:fm|am|xm)\b)|'    # "98 FM"
        r'(?:\d{2,4}fm\b)|'                    # 107FM
        r'(?:\b(?:fm|am|radio)\b)|'            # standalone keywords
        r'(?:^[WK][A-Z]{2,4}(?:[\s\-]|$))|'   # WBLS / KABC at start
        r'(?:\b\d{2,3}[XZJxzj]\b)',           # 93X, 97X, 90Z
        re.IGNORECASE
    )),
    # Education — TED talks, universities, learning channels
    ("Education", re.compile(
        r'\b(?:ted\s*talks?|ted\s*conferences?|\w*\s*university\s*tv|'
        r'college\s*tv|community\s*media\s*education|education\s*tv|'
        r'rta\s*education|learning\s*channel|science\s*channel|'
        r'documentary\s*education|how\s*to|crash\s*course|edutainment)\b',
        re.IGNORECASE
    )),
    # Public affairs / government — parliament, council, civic access
    ("News", re.compile(
        r'\b(?:parliament|council\s*channel|government\s*channel|'
        r'community\s*tv|civic\s*channel|municipal\s*tv|'
        r'public\s*access|legislature|senate|congress|cspan|c-span)\b',
        re.IGNORECASE
    )),
    # Entertainment — anime, drama, novela, sitcom, reality, comedy
    ("Entertainment", re.compile(
        r'\b(?:anime|telenovela|novela|k.?drama|sitcom|reality\s*tv|'
        r'comedy\s*central|stand.?up|game\s*show|talk\s*show|'
        r'soap\s*opera|drama\s*series|series\s*channel|xena|'
        r'mr\s*bean|tom\s*&?\s*jerry|looney\s*tunes)\b',
        re.IGNORECASE
    )),
    # Music — extended with artists, eras, dance styles, ambient
    ("Music", re.compile(
        r'\b(?:mtv(?:\s+\w+)?|vh1|vevo|music\s*box|stingray|trace\s*urban|'
        r'deluxe\s*music|kiss\s*tv|qmusic|nrj|hits|jazz|rock|oldies|hitz|'
        r'reggae|reggaeton|hip.?hop|r&b|soul|blues|techno|edm|salsa|mariachi|'
        r'symphony|orchestra|mizrahi|mizrahit|playlist|classic\s*rock|'
        r'classical|smooth\s*jazz|country\s*music|pop\s*music|songs?|melody|'
        r'k.?pop|j.?pop|disco|funk|funky|ambient|instrumental|lo.?fi|chill|'
        r'dance\s*classics?|exclusively\s*\w+|tilemousiki|'
        r'clapton|beatles|elvis|presley|sinatra|dylan|madonna|metallica|'
        r'dire\s*straits|bob\s*marley|pink\s*floyd|\d0s\s+(?:hits?|music|'
        r'songs?|funk|soul|disco))\b',
        re.IGNORECASE
    )),
    # === Last-resort catch-all ===
    # If a channel made it this far with NO category and a generic TV-broadcast
    # token in the name, classify it as Entertainment (catch-all for regional
    # general-interest TV networks).  Foreign-language tokens included.
    ("Entertainment", re.compile(
        r'(?:'
        # English/Latin generic broadcasting words (with prefix-tolerance for
        # compound CamelCase like "TeleMistretta", "Telever", "Canale5")
        r'\btele\w*\b|\bcanal\w*\b|\bkanal\w*\b|\bkanaal\w*\b|'
        r'\b(?:tv|television|televisi[oóón]|televisione|televizyon|televizia|'
        r'channel|chaine|cha[iî]ne|fernsehen|sender|emittente|emisora|'
        r'stazione|rete|chain|network|broadcasting|freetv|free\s*tv)\b|'
        # Substring-tv: matches MTV, CTV, ATV, TVR, TVP, HDTV, FreeTV, etc.
        r'\b\w*tv\w*\b|'
        # Common broadcaster acronyms (3-letter networks)
        r'\b(?:bbc|itv|rai|rtl|rti|mbc|cbc|pbs|rtv|rtp|rte|nhk|kbs|sbs|bfbs|'
        r'tbs|mnc|cnn|zdf|ard|ntv|jtv|otv|btv|stv|htv|dtv|ptv|ktv|etv|gtv|ftv|'
        r'omroep|antenne|antena|сts|стс|нтв|тнт|ren|tnt|pop|now|alt|heart|'
        r'vibes|deal|red\s*button|tweede\s*kamer|reelz|awe|nove|la\d|m\d|'
        r'action|atlantis|action!|popcorn|trve|trce|trv|trvl)\b|'
        # Geo-blocked regional channels — explicit "(US) Geo", "(IL) Geo"
        r'\(\s*[A-Z]{2}\s*\)\s*geo|'
        r'\bil:\s|\bkamer:|'
        # Italian/Spanish/Portuguese regional indicators
        r'\b(?:rete|provincia|regione|estado|paraguay|argentina|colombia|'
        r'brasil|brazil|portugal|italia|espa[nñ]ol|deutschland)\b|'
        # Non-Latin scripts (almost always a regional TV network)
        r'[\u0400-\u04ff]{2,}|'              # Cyrillic
        r'[\u4e00-\u9fff]|'                  # CJK Han
        r'[\u3040-\u309f\u30a0-\u30ff]|'     # Hiragana/Katakana
        r'[\u0590-\u05ff]{2,}|'              # Hebrew
        r'[\u0600-\u06ff]{2,}|'              # Arabic
        r'[\u0900-\u097f]{2,}|'              # Devanagari (Hindi)
        r'[\uac00-\ud7af]'                   # Korean Hangul
        r')',
        re.IGNORECASE
    )),
    # === True final fallback ===
    # Anything with a real (3+ alphanumeric) name and no other category signal:
    # classify as Entertainment.  Channels with only punctuation/symbols/very
    # short names stay in General as a "truly unknown" bucket.
    ("Entertainment", re.compile(r'[A-Za-z\u00c0-\u024f]{3,}', re.UNICODE)),
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
    # A
    "AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan",
    "AG": "Antigua and Barbuda", "AI": "Anguilla", "AL": "Albania",
    "AM": "Armenia", "AO": "Angola", "AQ": "Antarctica", "AR": "Argentina",
    "AS": "American Samoa", "AT": "Austria", "AU": "Australia",
    "AW": "Aruba", "AX": "Aland Islands", "AZ": "Azerbaijan",
    # B
    "BA": "Bosnia", "BB": "Barbados", "BD": "Bangladesh", "BE": "Belgium",
    "BF": "Burkina Faso", "BG": "Bulgaria", "BH": "Bahrain", "BI": "Burundi",
    "BJ": "Benin", "BL": "Saint Barthelemy", "BM": "Bermuda", "BN": "Brunei",
    "BO": "Bolivia", "BQ": "Caribbean Netherlands", "BR": "Brazil",
    "BS": "Bahamas", "BT": "Bhutan", "BV": "Bouvet Island", "BW": "Botswana",
    "BY": "Belarus", "BZ": "Belize",
    # C
    "CA": "Canada", "CC": "Cocos Islands", "CD": "Congo (DRC)",
    "CF": "Central African Republic", "CG": "Congo", "CH": "Switzerland",
    "CI": "Ivory Coast", "CK": "Cook Islands", "CL": "Chile", "CM": "Cameroon",
    "CN": "China", "CO": "Colombia", "CR": "Costa Rica", "CU": "Cuba",
    "CV": "Cape Verde", "CW": "Curacao", "CX": "Christmas Island",
    "CY": "Cyprus", "CZ": "Czech Republic",
    # D
    "DE": "Germany", "DJ": "Djibouti", "DK": "Denmark", "DM": "Dominica",
    "DO": "Dominican Republic", "DZ": "Algeria",
    # E
    "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt", "EH": "Western Sahara",
    "ER": "Eritrea", "ES": "Spain", "ET": "Ethiopia",
    # F
    "FI": "Finland", "FJ": "Fiji", "FK": "Falkland Islands",
    "FM": "Micronesia", "FO": "Faroe Islands", "FR": "France",
    # G
    "GA": "Gabon", "GB": "United Kingdom", "GD": "Grenada", "GE": "Georgia",
    "GF": "French Guiana", "GG": "Guernsey", "GH": "Ghana", "GI": "Gibraltar",
    "GL": "Greenland", "GM": "Gambia", "GN": "Guinea", "GP": "Guadeloupe",
    "GQ": "Equatorial Guinea", "GR": "Greece",
    "GS": "South Georgia", "GT": "Guatemala", "GU": "Guam",
    "GW": "Guinea-Bissau", "GY": "Guyana",
    # H
    "HK": "Hong Kong", "HM": "Heard Island", "HN": "Honduras", "HR": "Croatia",
    "HT": "Haiti", "HU": "Hungary",
    # I
    "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IM": "Isle of Man",
    "IN": "India", "IO": "British Indian Ocean Territory", "IQ": "Iraq",
    "IR": "Iran", "IS": "Iceland", "IT": "Italy",
    # J
    "JE": "Jersey", "JM": "Jamaica", "JO": "Jordan", "JP": "Japan",
    # K
    "KE": "Kenya", "KG": "Kyrgyzstan", "KH": "Cambodia", "KI": "Kiribati",
    "KM": "Comoros", "KN": "Saint Kitts and Nevis", "KP": "North Korea",
    "KR": "South Korea", "KW": "Kuwait", "KY": "Cayman Islands",
    "KZ": "Kazakhstan",
    # L
    "LA": "Laos", "LB": "Lebanon", "LC": "Saint Lucia", "LI": "Liechtenstein",
    "LK": "Sri Lanka", "LR": "Liberia", "LS": "Lesotho", "LT": "Lithuania",
    "LU": "Luxembourg", "LV": "Latvia", "LY": "Libya",
    # M
    "MA": "Morocco", "MC": "Monaco", "MD": "Moldova", "ME": "Montenegro",
    "MF": "Saint Martin", "MG": "Madagascar", "MH": "Marshall Islands",
    "MK": "North Macedonia", "ML": "Mali", "MM": "Myanmar", "MN": "Mongolia",
    "MO": "Macao", "MP": "Northern Mariana Islands", "MQ": "Martinique",
    "MR": "Mauritania", "MS": "Montserrat", "MT": "Malta", "MU": "Mauritius",
    "MV": "Maldives", "MW": "Malawi", "MX": "Mexico", "MY": "Malaysia",
    "MZ": "Mozambique",
    # N
    "NA": "Namibia", "NC": "New Caledonia", "NE": "Niger", "NF": "Norfolk Island",
    "NG": "Nigeria", "NI": "Nicaragua", "NL": "Netherlands", "NO": "Norway",
    "NP": "Nepal", "NR": "Nauru", "NU": "Niue", "NZ": "New Zealand",
    # O
    "OM": "Oman",
    # P
    "PA": "Panama", "PE": "Peru", "PF": "French Polynesia",
    "PG": "Papua New Guinea", "PH": "Philippines", "PK": "Pakistan",
    "PL": "Poland", "PM": "Saint Pierre and Miquelon", "PN": "Pitcairn Islands",
    "PR": "Puerto Rico", "PS": "Palestine", "PT": "Portugal", "PW": "Palau",
    "PY": "Paraguay",
    # Q
    "QA": "Qatar",
    # R
    "RE": "Reunion", "RO": "Romania", "RS": "Serbia", "RU": "Russia",
    "RW": "Rwanda",
    # S
    "SA": "Saudi Arabia", "SB": "Solomon Islands", "SC": "Seychelles",
    "SD": "Sudan", "SE": "Sweden", "SG": "Singapore", "SH": "Saint Helena",
    "SI": "Slovenia", "SJ": "Svalbard and Jan Mayen", "SK": "Slovakia",
    "SL": "Sierra Leone", "SM": "San Marino", "SN": "Senegal", "SO": "Somalia",
    "SR": "Suriname", "SS": "South Sudan", "ST": "Sao Tome and Principe",
    "SV": "El Salvador", "SX": "Sint Maarten", "SY": "Syria", "SZ": "Eswatini",
    # T
    "TC": "Turks and Caicos", "TD": "Chad", "TF": "French Southern Territories",
    "TG": "Togo", "TH": "Thailand", "TJ": "Tajikistan", "TK": "Tokelau",
    "TL": "Timor-Leste", "TM": "Turkmenistan", "TN": "Tunisia", "TO": "Tonga",
    "TR": "Turkey", "TT": "Trinidad", "TV": "Tuvalu", "TW": "Taiwan",
    "TZ": "Tanzania",
    # U
    "UA": "Ukraine", "UG": "Uganda", "UK": "United Kingdom",
    "UM": "US Minor Outlying Islands", "US": "USA", "UY": "Uruguay",
    "UZ": "Uzbekistan",
    # V
    "VA": "Vatican City", "VC": "Saint Vincent and the Grenadines",
    "VE": "Venezuela", "VG": "British Virgin Islands", "VI": "US Virgin Islands",
    "VN": "Vietnam", "VU": "Vanuatu",
    # W
    "WF": "Wallis and Futuna", "WS": "Samoa",
    # X (user-assigned / special)
    "XK": "Kosovo",
    # Y
    "YE": "Yemen", "YT": "Mayotte",
    # Z
    "ZA": "South Africa", "ZM": "Zambia", "ZW": "Zimbabwe",
}

# ISO 3166-1 alpha-3 → alpha-2 (so the same lookup logic handles 3-letter codes).
# Only entries that actually appear in IPTV/EPG sources; extend as needed.
COUNTRY_CODES_ALPHA3: dict[str, str] = {
    "AFG": "AF", "ALB": "AL", "DZA": "DZ", "AND": "AD", "AGO": "AO",
    "ARG": "AR", "ARM": "AM", "AUS": "AU", "AUT": "AT", "AZE": "AZ",
    "BHS": "BS", "BHR": "BH", "BGD": "BD", "BRB": "BB", "BLR": "BY",
    "BEL": "BE", "BLZ": "BZ", "BEN": "BJ", "BMU": "BM", "BTN": "BT",
    "BOL": "BO", "BIH": "BA", "BWA": "BW", "BRA": "BR", "BRN": "BN",
    "BGR": "BG", "BFA": "BF", "BDI": "BI", "KHM": "KH", "CMR": "CM",
    "CAN": "CA", "CPV": "CV", "CAF": "CF", "TCD": "TD", "CHL": "CL",
    "CHN": "CN", "COL": "CO", "COM": "KM", "COG": "CG", "COD": "CD",
    "CRI": "CR", "CIV": "CI", "HRV": "HR", "CUB": "CU", "CYP": "CY",
    "CZE": "CZ", "DNK": "DK", "DJI": "DJ", "DMA": "DM", "DOM": "DO",
    "ECU": "EC", "EGY": "EG", "SLV": "SV", "GNQ": "GQ", "ERI": "ER",
    "EST": "EE", "ETH": "ET", "FRO": "FO", "FJI": "FJ", "FIN": "FI",
    "FRA": "FR", "GUF": "GF", "PYF": "PF", "GAB": "GA", "GMB": "GM",
    "GEO": "GE", "DEU": "DE", "GHA": "GH", "GIB": "GI", "GRC": "GR",
    "GRL": "GL", "GRD": "GD", "GLP": "GP", "GUM": "GU", "GTM": "GT",
    "GIN": "GN", "GNB": "GW", "GUY": "GY", "HTI": "HT", "HND": "HN",
    "HKG": "HK", "HUN": "HU", "ISL": "IS", "IND": "IN", "IDN": "ID",
    "IRN": "IR", "IRQ": "IQ", "IRL": "IE", "ISR": "IL", "ITA": "IT",
    "JAM": "JM", "JPN": "JP", "JOR": "JO", "KAZ": "KZ", "KEN": "KE",
    "KIR": "KI", "PRK": "KP", "KOR": "KR", "KWT": "KW", "KGZ": "KG",
    "LAO": "LA", "LVA": "LV", "LBN": "LB", "LSO": "LS", "LBR": "LR",
    "LBY": "LY", "LIE": "LI", "LTU": "LT", "LUX": "LU", "MAC": "MO",
    "MKD": "MK", "MDG": "MG", "MWI": "MW", "MYS": "MY", "MDV": "MV",
    "MLI": "ML", "MLT": "MT", "MHL": "MH", "MTQ": "MQ", "MRT": "MR",
    "MUS": "MU", "MEX": "MX", "FSM": "FM", "MDA": "MD", "MCO": "MC",
    "MNG": "MN", "MNE": "ME", "MAR": "MA", "MOZ": "MZ", "MMR": "MM",
    "NAM": "NA", "NPL": "NP", "NLD": "NL", "NCL": "NC", "NZL": "NZ",
    "NIC": "NI", "NER": "NE", "NGA": "NG", "NOR": "NO", "OMN": "OM",
    "PAK": "PK", "PLW": "PW", "PSE": "PS", "PAN": "PA", "PNG": "PG",
    "PRY": "PY", "PER": "PE", "PHL": "PH", "POL": "PL", "PRT": "PT",
    "PRI": "PR", "QAT": "QA", "REU": "RE", "ROU": "RO", "RUS": "RU",
    "RWA": "RW", "WSM": "WS", "SMR": "SM", "STP": "ST", "SAU": "SA",
    "SEN": "SN", "SRB": "RS", "SYC": "SC", "SLE": "SL", "SGP": "SG",
    "SVK": "SK", "SVN": "SI", "SLB": "SB", "SOM": "SO", "ZAF": "ZA",
    "SSD": "SS", "ESP": "ES", "LKA": "LK", "SDN": "SD", "SUR": "SR",
    "SWZ": "SZ", "SWE": "SE", "CHE": "CH", "SYR": "SY", "TWN": "TW",
    "TJK": "TJ", "TZA": "TZ", "THA": "TH", "TLS": "TL", "TGO": "TG",
    "TON": "TO", "TTO": "TT", "TUN": "TN", "TUR": "TR", "TKM": "TM",
    "TUV": "TV", "UGA": "UG", "UKR": "UA", "ARE": "AE", "GBR": "GB",
    "USA": "US", "URY": "UY", "UZB": "UZ", "VUT": "VU", "VAT": "VA",
    "VEN": "VE", "VNM": "VN", "YEM": "YE", "ZMB": "ZM", "ZWE": "ZW",
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
    2. 3-letter ISO alpha-3 → map to alpha-2 → lookup
    3. 2-letter ISO alpha-2 → lookup in COUNTRY_CODES (fallback to "Unknown" so
       unrecognised codes don't pollute the UI with bare codes like "FO")
    4. Known alias → canonical name
    5. Semicolon-separated → take first, re-normalize
    6. Otherwise return as-is (title-cased if all-lower/all-upper)
    """
    if not raw or not raw.strip() or raw.strip().lower() in ("unknown", "undefined", "n/a", ""):
        return "Unknown"

    country = raw.strip()

    # ISO 3-letter code → resolve to 2-letter then look up
    if len(country) == 3 and country.isalpha():
        alpha2 = COUNTRY_CODES_ALPHA3.get(country.upper())
        if alpha2:
            return COUNTRY_CODES.get(alpha2, "Unknown")

    # ISO 2-letter code — must be in the canonical map. If unknown, fold to
    # "Unknown" rather than show the bare code in the sidebar.
    if len(country) == 2 and country.isalpha():
        return COUNTRY_CODES.get(country.upper(), "Unknown")

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
