"""External lookup service for channel metadata (country, age rating)."""

import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from functools import lru_cache


# Comprehensive list of valid country names for filtering
COUNTRY_NAMES = {
    'US': 'US',
    'USA': 'US',
    'United States': 'US',
    'UK': 'UK',
    'United Kingdom': 'UK',
    'GB': 'UK',
    'Germany': 'Germany',
    'DE': 'Germany',
    'France': 'France',
    'FR': 'France',
    'Italy': 'Italy',
    'IT': 'Italy',
    'Spain': 'Spain',
    'ES': 'Spain',
    'Portugal': 'Portugal',
    'PT': 'Portugal',
    'Netherlands': 'Netherlands',
    'NL': 'Netherlands',
    'Belgium': 'Belgium',
    'BE': 'Belgium',
    'Switzerland': 'Switzerland',
    'CH': 'Switzerland',
    'Austria': 'Austria',
    'AT': 'Austria',
    'Poland': 'Poland',
    'PL': 'Poland',
    'Czech Republic': 'Czech Republic',
    'CZ': 'Czech Republic',
    'Hungary': 'Hungary',
    'HU': 'Hungary',
    'Romania': 'Romania',
    'RO': 'Romania',
    'Bulgaria': 'Bulgaria',
    'BG': 'Bulgaria',
    'Greece': 'Greece',
    'GR': 'Greece',
    'Turkey': 'Turkey',
    'TR': 'Turkey',
    'Russia': 'Russia',
    'RU': 'Russia',
    'Ukraine': 'Ukraine',
    'UA': 'Ukraine',
    'Sweden': 'Sweden',
    'SE': 'Sweden',
    'Norway': 'Norway',
    'NO': 'Norway',
    'Denmark': 'Denmark',
    'DK': 'Denmark',
    'Finland': 'Finland',
    'FI': 'Finland',
    'Ireland': 'Ireland',
    'IE': 'Ireland',
    'Canada': 'Canada',
    'CA': 'Canada',
    'Australia': 'Australia',
    'AU': 'Australia',
    'New Zealand': 'New Zealand',
    'NZ': 'New Zealand',
    'Japan': 'Japan',
    'JP': 'Japan',
    'South Korea': 'South Korea',
    'KR': 'South Korea',
    'China': 'China',
    'CN': 'China',
    'Taiwan': 'Taiwan',
    'TW': 'Taiwan',
    'Hong Kong': 'Hong Kong',
    'HK': 'Hong Kong',
    'India': 'India',
    'IN': 'India',
    'Thailand': 'Thailand',
    'TH': 'Thailand',
    'Vietnam': 'Vietnam',
    'VN': 'Vietnam',
    'Indonesia': 'Indonesia',
    'ID': 'Indonesia',
    'Malaysia': 'Malaysia',
    'MY': 'Malaysia',
    'Singapore': 'Singapore',
    'SG': 'Singapore',
    'Philippines': 'Philippines',
    'PH': 'Philippines',
    'Israel': 'Israel',
    'IL': 'Israel',
    'Saudi Arabia': 'Saudi Arabia',
    'SA': 'Saudi Arabia',
    'UAE': 'UAE',
    'United Arab Emirates': 'UAE',
    'AE': 'UAE',
    'Egypt': 'Egypt',
    'EG': 'Egypt',
    'Morocco': 'Morocco',
    'MA': 'Morocco',
    'Tunisia': 'Tunisia',
    'TN': 'Tunisia',
    'Algeria': 'Algeria',
    'DZ': 'Algeria',
    'South Africa': 'South Africa',
    'ZA': 'South Africa',
    'Nigeria': 'Nigeria',
    'NG': 'Nigeria',
    'Kenya': 'Kenya',
    'KE': 'Kenya',
    'Brazil': 'Brazil',
    'BR': 'Brazil',
    'Mexico': 'Mexico',
    'MX': 'Mexico',
    'Argentina': 'Argentina',
    'AR': 'Argentina',
    'Colombia': 'Colombia',
    'CO': 'Colombia',
    'Chile': 'Chile',
    'CL': 'Chile',
    'Peru': 'Peru',
    'PE': 'Peru',
    'Venezuela': 'Venezuela',
    'VE': 'Venezuela',
    'Pakistan': 'Pakistan',
    'PK': 'Pakistan',
    'Bangladesh': 'Bangladesh',
    'BD': 'Bangladesh',
    'Serbia': 'Serbia',
    'RS': 'Serbia',
    'Croatia': 'Croatia',
    'HR': 'Croatia',
    'Slovenia': 'Slovenia',
    'SI': 'Slovenia',
    'Slovakia': 'Slovakia',
    'SK': 'Slovakia',
    'Middle East': 'Middle East',
    'Latin America': 'Latin America',
    'International': 'International',
}


# Known broadcasters/channels with their country and typical age rating
# Format: lowercase name pattern -> (country, min_age)
KNOWN_CHANNELS: Dict[str, Tuple[str, int]] = {
    # US Channels
    'cnn': ('US', 13),
    'fox news': ('US', 13),
    'msnbc': ('US', 13),
    'abc': ('US', 7),
    'nbc': ('US', 7),
    'cbs': ('US', 7),
    'pbs': ('US', 0),
    'hbo': ('US', 16),
    'showtime': ('US', 18),
    'espn': ('US', 7),
    'mtv': ('US', 13),
    'vh1': ('US', 13),
    'comedy central': ('US', 13),
    'cartoon network': ('US', 0),
    'nickelodeon': ('US', 0),
    'nick jr': ('US', 0),
    'disney': ('US', 0),
    'disney channel': ('US', 0),
    'disney junior': ('US', 0),
    'disney xd': ('US', 7),
    'discovery': ('US', 7),
    'history channel': ('US', 7),
    'history': ('US', 7),
    'national geographic': ('US', 7),
    'nat geo': ('US', 7),
    'animal planet': ('US', 0),
    'tlc': ('US', 13),
    'food network': ('US', 0),
    'hgtv': ('US', 0),
    'lifetime': ('US', 13),
    'hallmark': ('US', 0),
    'syfy': ('US', 13),
    'amc': ('US', 16),
    'fx': ('US', 16),
    'tnt': ('US', 13),
    'tbs': ('US', 13),
    'usa network': ('US', 13),
    'bravo': ('US', 13),
    'e!': ('US', 13),
    'bet': ('US', 13),
    'cinemax': ('US', 18),
    'starz': ('US', 16),
    'paramount': ('US', 13),
    'cnbc': ('US', 7),
    'bloomberg': ('US', 7),
    'c-span': ('US', 7),
    'weather channel': ('US', 0),
    'nfl network': ('US', 7),
    'mlb network': ('US', 7),
    'nba tv': ('US', 7),
    
    # UK Channels
    'bbc': ('UK', 7),
    'bbc one': ('UK', 7),
    'bbc two': ('UK', 7),
    'bbc three': ('UK', 13),
    'bbc four': ('UK', 7),
    'bbc news': ('UK', 7),
    'cbbc': ('UK', 0),
    'cbeebies': ('UK', 0),
    'itv': ('UK', 7),
    'itv2': ('UK', 13),
    'itv3': ('UK', 13),
    'itv4': ('UK', 13),
    'channel 4': ('UK', 13),
    'channel 5': ('UK', 13),
    'sky': ('UK', 13),
    'sky news': ('UK', 7),
    'sky sports': ('UK', 7),
    'sky cinema': ('UK', 13),
    'sky atlantic': ('UK', 16),
    'dave': ('UK', 13),
    'e4': ('UK', 13),
    'film4': ('UK', 16),
    'more4': ('UK', 13),
    
    # German Channels
    'ard': ('Germany', 7),
    'zdf': ('Germany', 7),
    'rtl': ('Germany', 13),
    'sat.1': ('Germany', 13),
    'sat1': ('Germany', 13),
    'pro7': ('Germany', 13),
    'prosieben': ('Germany', 13),
    'vox': ('Germany', 13),
    'kabel eins': ('Germany', 13),
    'n-tv': ('Germany', 7),
    'phoenix': ('Germany', 7),
    'arte': ('Germany', 7),
    'kika': ('Germany', 0),
    'super rtl': ('Germany', 0),
    'dw': ('Germany', 7),
    'deutsche welle': ('Germany', 7),
    
    # French Channels
    'tf1': ('France', 7),
    'france 2': ('France', 7),
    'france 3': ('France', 7),
    'france 4': ('France', 0),
    'france 5': ('France', 7),
    'france 24': ('France', 7),
    'm6': ('France', 13),
    'canal+': ('France', 16),
    'canal plus': ('France', 16),
    'bfm': ('France', 7),
    'bfm tv': ('France', 7),
    'cnews': ('France', 7),
    'lci': ('France', 7),
    'gulli': ('France', 0),
    'tiji': ('France', 0),
    
    # Spanish Channels
    'tve': ('Spain', 7),
    'la 1': ('Spain', 7),
    'la 2': ('Spain', 7),
    'antena 3': ('Spain', 13),
    'cuatro': ('Spain', 13),
    'telecinco': ('Spain', 13),
    'la sexta': ('Spain', 13),
    'clan': ('Spain', 0),
    'boing': ('Spain', 0),
    
    # Italian Channels
    'rai': ('Italy', 7),
    'rai 1': ('Italy', 7),
    'rai 2': ('Italy', 7),
    'rai 3': ('Italy', 7),
    'rai news': ('Italy', 7),
    'mediaset': ('Italy', 13),
    'canale 5': ('Italy', 13),
    'italia 1': ('Italy', 13),
    'rete 4': ('Italy', 13),
    'la7': ('Italy', 7),
    'sky italia': ('Italy', 13),
    
    # Israeli Channels - expanded with all major channels
    'channel 14': ('Israel', 13),
    'now 14': ('Israel', 13),
    'ערוץ 14': ('Israel', 13),
    'עכשיו 14': ('Israel', 13),
    'channel 10': ('Israel', 7),
    'ערוץ 10': ('Israel', 7),
    'channel 11': ('Israel', 7),
    'ערוץ 11': ('Israel', 7),
    'kan 11': ('Israel', 7),
    'kan': ('Israel', 7),
    'כאן 11': ('Israel', 7),
    'כאן': ('Israel', 7),
    'kan news': ('Israel', 7),
    'kan educational': ('Israel', 0),
    'kan kids': ('Israel', 0),
    'keshet 12': ('Israel', 7),
    'keshet': ('Israel', 7),
    'קשת 12': ('Israel', 7),
    'קשת': ('Israel', 7),
    'channel 12': ('Israel', 7),
    'ערוץ 12': ('Israel', 7),
    'reshet 13': ('Israel', 7),
    'reshet': ('Israel', 7),
    'רשת 13': ('Israel', 7),
    'רשת': ('Israel', 7),
    'channel 13': ('Israel', 7),
    'ערוץ 13': ('Israel', 7),
    'channel 9': ('Israel', 7),
    'ערוץ 9': ('Israel', 7),
    'i24': ('Israel', 13),
    'i24 news': ('Israel', 13),
    'i24news': ('Israel', 13),
    'walla': ('Israel', 7),
    'walla tv': ('Israel', 7),
    'walla news': ('Israel', 7),
    'וואלה': ('Israel', 7),
    'sport 5': ('Israel', 7),
    'ספורט 5': ('Israel', 7),
    'sport5': ('Israel', 7),
    'one': ('Israel', 13),
    'one israel': ('Israel', 13),
    'ynet': ('Israel', 7),
    'ynet tv': ('Israel', 7),
    'logi': ('Israel', 7),
    'music 24': ('Israel', 7),
    'מיוזיק 24': ('Israel', 7),
    'hot': ('Israel', 7),
    'hot 3': ('Israel', 7),
    'hot cinema': ('Israel', 13),
    'yes': ('Israel', 7),
    'yes drama': ('Israel', 13),
    'yes action': ('Israel', 16),
    'knesset': ('Israel', 7),
    'כנסת': ('Israel', 7),
    'knesset channel': ('Israel', 7),
    'makan': ('Israel', 7),
    'מכאן': ('Israel', 7),
    'makan 33': ('Israel', 7),
    'hop': ('Israel', 0),
    'hop channel': ('Israel', 0),
    'הופ': ('Israel', 0),
    'luli': ('Israel', 0),
    'junior': ('Israel', 0),
    'baby': ('Israel', 0),
    'zoom': ('Israel', 7),
    'n12': ('Israel', 7),
    'news 12': ('Israel', 7),
    'news 13': ('Israel', 7),
    'channel 20': ('Israel', 7),
    'ערוץ 20': ('Israel', 7),
    'channel 24': ('Israel', 7),
    'ערוץ 24': ('Israel', 7),
    'gali israel': ('Israel', 7),
    'גלי ישראל': ('Israel', 7),
    'galatz': ('Israel', 7),
    'גלצ': ('Israel', 7),
    'army radio': ('Israel', 7),
    'reshet bet': ('Israel', 7),
    'רשת ב': ('Israel', 7),
    'kol israel': ('Israel', 7),
    'קול ישראל': ('Israel', 7),
    '88fm': ('Israel', 7),
    '103fm': ('Israel', 7),
    'eco99': ('Israel', 7),
    'radius 100fm': ('Israel', 7),
    
    # Indian Channels
    'zee': ('India', 7),
    'zee tv': ('India', 7),
    'zee news': ('India', 7),
    'star': ('India', 7),
    'star plus': ('India', 7),
    'star sports': ('India', 7),
    'colors': ('India', 13),
    'sony': ('India', 7),
    'sony tv': ('India', 7),
    'aaj tak': ('India', 7),
    'ndtv': ('India', 7),
    'times now': ('India', 7),
    'republic': ('India', 7),
    'pogo': ('India', 0),
    'hungama': ('India', 0),
    'nick india': ('India', 0),
    
    # Arabic/Middle East Channels
    'al jazeera': ('Qatar', 13),
    'al arabiya': ('UAE', 13),
    'mbc': ('Saudi Arabia', 13),
    'rotana': ('Saudi Arabia', 13),
    'lbc': ('Lebanon', 13),
    'dubai': ('UAE', 7),
    'abu dhabi': ('UAE', 7),
    
    # Asian Channels
    'nhk': ('Japan', 7),
    'fuji': ('Japan', 13),
    'tv asahi': ('Japan', 13),
    'tbs japan': ('Japan', 13),
    'kbs': ('South Korea', 7),
    'mbc korea': ('South Korea', 7),
    'sbs korea': ('South Korea', 7),
    'tvn': ('South Korea', 13),
    'arirang': ('South Korea', 7),
    'cctv': ('China', 7),
    'cgtn': ('China', 7),
    'phoenix chinese': ('China', 7),
    'tvb': ('Hong Kong', 13),
    'astro': ('Malaysia', 7),
    'abs-cbn': ('Philippines', 7),
    'gma': ('Philippines', 7),
    
    # Latin America
    'globo': ('Brazil', 13),
    'record': ('Brazil', 13),
    'sbt': ('Brazil', 13),
    'band': ('Brazil', 13),
    'televisa': ('Mexico', 13),
    'tv azteca': ('Mexico', 13),
    'caracol': ('Colombia', 13),
    'rcn': ('Colombia', 13),
    'telesur': ('Venezuela', 7),
    
    # Russian Channels
    'russia 1': ('Russia', 7),
    'russia 24': ('Russia', 7),
    'perviy kanal': ('Russia', 7),
    'channel one russia': ('Russia', 7),
    'ntv': ('Russia', 13),
    'rt': ('Russia', 7),
    'russia today': ('Russia', 7),
    
    # International
    'euronews': ('International', 7),
    'cnn international': ('International', 13),
    'bbc world': ('International', 7),
    'dw english': ('International', 7),
    'france 24 english': ('International', 7),
    'al jazeera english': ('International', 13),
    'nhk world': ('International', 7),
    'cgtn english': ('International', 7),
    
    # YouTube Live News Channels
    'abc news live': ('US', 7),
    'nbc news now': ('US', 7),
    'cbs news': ('US', 7),
    'sky news live': ('UK', 7),
    'france 24 live': ('France', 7),
    'dw news': ('Germany', 7),
    'al jazeera live': ('Qatar', 7),
    'arirang tv': ('South Korea', 7),
    'cna': ('Singapore', 7),
    'wion': ('India', 7),
    
    # Free DVB/FAST Channels (Pluto TV, Samsung TV Plus, etc.)
    'pluto': ('US', 13),
    'pluto tv': ('US', 13),
    'samsung tv': ('US', 7),
    'samsung tv plus': ('US', 7),
    'plex': ('US', 13),
    'stirr': ('US', 7),
    'xumo': ('US', 7),
    'tubi': ('US', 13),
    'roku': ('US', 7),
    'peacock': ('US', 13),
    'freevee': ('US', 13),
    
    # Adult channels (18+)
    'playboy': ('US', 18),
    'hustler': ('US', 18),
    'penthouse': ('US', 18),
    'brazzers': ('US', 18),
    'vivid': ('US', 18),
    'spice': ('US', 18),
    'xxx': ('International', 18),
    'adult': ('International', 18),
    'erotic': ('International', 18),
    'hot bird': ('International', 18),
    'redlight': ('International', 18),
    'private': ('International', 18),
    
    # Radio Stations
    'bbc radio': ('UK', 7),
    'npr': ('US', 7),
    'radio paradise': ('US', 7),
    'soma fm': ('US', 7),
    'galgalatz': ('Israel', 7),
    'galatz': ('Israel', 7),
    '88fm': ('Israel', 7),
    '103fm': ('Israel', 7),
    'eco99fm': ('Israel', 7),
    'radius 100fm': ('Israel', 7),
    'reshet bet': ('Israel', 7),
    'kol israel': ('Israel', 7),
    'classic fm': ('UK', 7),
    'heart': ('UK', 7),
    'capital': ('UK', 7),
    'kiis fm': ('US', 7),
    'z100': ('US', 7),
}

# Domain TLD to country mapping
TLD_COUNTRY_MAP: Dict[str, str] = {
    '.us': 'US',
    '.uk': 'UK',
    '.co.uk': 'UK',
    '.de': 'Germany',
    '.fr': 'France',
    '.es': 'Spain',
    '.it': 'Italy',
    '.pt': 'Portugal',
    '.br': 'Brazil',
    '.mx': 'Mexico',
    '.ar': 'Argentina',
    '.cl': 'Chile',
    '.co': 'Colombia',
    '.ru': 'Russia',
    '.cn': 'China',
    '.jp': 'Japan',
    '.kr': 'South Korea',
    '.in': 'India',
    '.au': 'Australia',
    '.nz': 'New Zealand',
    '.ca': 'Canada',
    '.nl': 'Netherlands',
    '.be': 'Belgium',
    '.ch': 'Switzerland',
    '.at': 'Austria',
    '.pl': 'Poland',
    '.cz': 'Czech Republic',
    '.se': 'Sweden',
    '.no': 'Norway',
    '.dk': 'Denmark',
    '.fi': 'Finland',
    '.gr': 'Greece',
    '.tr': 'Turkey',
    '.ae': 'UAE',
    '.sa': 'Saudi Arabia',
    '.eg': 'Egypt',
    '.za': 'South Africa',
    '.ng': 'Nigeria',
    '.ke': 'Kenya',
    '.il': 'Israel',
    '.pk': 'Pakistan',
    '.bd': 'Bangladesh',
    '.id': 'Indonesia',
    '.my': 'Malaysia',
    '.sg': 'Singapore',
    '.th': 'Thailand',
    '.vn': 'Vietnam',
    '.ph': 'Philippines',
    '.tw': 'Taiwan',
    '.hk': 'Hong Kong',
}

# Language to likely country mapping (for fallback)
LANGUAGE_COUNTRY_MAP: Dict[str, str] = {
    'english': 'International',
    'spanish': 'Spain',
    'spanish; castilian': 'Spain',
    'french': 'France',
    'german': 'Germany',
    'italian': 'Italy',
    'portuguese': 'Brazil',
    'russian': 'Russia',
    'arabic': 'Middle East',
    'chinese': 'China',
    'mandarin': 'China',
    'cantonese': 'Hong Kong',
    'japanese': 'Japan',
    'korean': 'South Korea',
    'hindi': 'India',
    'urdu': 'Pakistan',
    'bengali': 'Bangladesh',
    'tamil': 'India',
    'telugu': 'India',
    'turkish': 'Turkey',
    'persian': 'Iran',
    'farsi': 'Iran',
    'dutch': 'Netherlands',
    'polish': 'Poland',
    'greek': 'Greece',
    'hebrew': 'Israel',
    'thai': 'Thailand',
    'vietnamese': 'Vietnam',
    'indonesian': 'Indonesia',
    'malay': 'Malaysia',
    'tagalog': 'Philippines',
    'filipino': 'Philippines',
    'swedish': 'Sweden',
    'norwegian': 'Norway',
    'danish': 'Denmark',
    'finnish': 'Finland',
}

# Category-based age ratings
CATEGORY_AGE_MAP: Dict[str, int] = {
    'kids': 0,
    'children': 0,
    'animation': 0,
    'cartoon': 0,
    'family': 0,
    'education': 0,
    'educational': 0,
    'news': 7,
    'weather': 7,
    'sports': 7,
    'sport': 7,
    'documentary': 7,
    'nature': 7,
    'science': 7,
    'travel': 7,
    'lifestyle': 7,
    'cooking': 7,
    'food': 7,
    'general': 7,
    'entertainment': 13,
    'music': 13,
    'reality': 13,
    'comedy': 13,
    'drama': 13,
    'series': 13,
    'movies': 13,
    'cinema': 13,
    'action': 16,
    'thriller': 16,
    'horror': 18,
    'crime': 16,
    'adult': 18,
    'xxx': 18,
}


@lru_cache(maxsize=20000)
def lookup_channel_by_name(name: str) -> Optional[Tuple[str, int]]:
    """
    Look up channel info by name against known channels database.
    Uses LRU cache for performance.
    
    Args:
        name: Channel name
        
    Returns:
        Tuple of (country, min_age) or None if not found
    """
    if not name:
        return None
    
    name_lower = name.lower().strip()
    
    # Direct match (O(1) dict lookup)
    if name_lower in KNOWN_CHANNELS:
        return KNOWN_CHANNELS[name_lower]
    
    # Quick word-based lookup - only check if channel name contains keywords
    # This is faster than iterating through all known channels
    name_words = set(name_lower.split())
    
    for known_name, info in KNOWN_CHANNELS.items():
        # Check if the known name is a single word and appears in channel name
        if ' ' not in known_name:
            if known_name in name_words or known_name in name_lower:
                return info
        else:
            # Multi-word known name - check if it appears as substring
            if known_name in name_lower:
                return info
    
    return None


def lookup_country_by_url(url: str) -> Optional[str]:
    """
    Try to determine country from stream URL domain.
    
    Args:
        url: Stream URL
        
    Returns:
        Country name or None
    """
    if not url:
        return None
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check TLD
        for tld, country in TLD_COUNTRY_MAP.items():
            if domain.endswith(tld):
                return country
        
        # Check for country codes in subdomain/path
        path = parsed.path.lower()
        for tld, country in TLD_COUNTRY_MAP.items():
            code = tld.replace('.', '')
            if f'/{code}/' in path or f'.{code}.' in domain:
                return country
                
    except Exception:
        pass
    
    return None


def lookup_country_by_language(language: str) -> Optional[str]:
    """
    Get likely country from language.
    
    Args:
        language: Language name
        
    Returns:
        Country name or None
    """
    if not language:
        return None
    
    lang_lower = language.lower().strip()
    
    # Direct match
    if lang_lower in LANGUAGE_COUNTRY_MAP:
        return LANGUAGE_COUNTRY_MAP[lang_lower]
    
    # Partial match
    for lang, country in LANGUAGE_COUNTRY_MAP.items():
        if lang in lang_lower:
            return country
    
    return None


def lookup_age_by_category(category: str) -> Optional[int]:
    """
    Get age rating from category.
    
    Args:
        category: Category name
        
    Returns:
        Minimum age or None
    """
    if not category:
        return None
    
    cat_lower = category.lower().strip()
    
    # Direct match
    if cat_lower in CATEGORY_AGE_MAP:
        return CATEGORY_AGE_MAP[cat_lower]
    
    # Partial match
    for cat, age in CATEGORY_AGE_MAP.items():
        if cat in cat_lower:
            return age
    
    return None


def lookup_channel_metadata(channel: Dict[str, Any]) -> Dict[str, Any]:
    """
    Look up missing metadata for a channel from external sources.
    Updates the channel dict with found information.
    
    Args:
        channel: Channel dictionary
        
    Returns:
        Updated channel dictionary
    """
    name = channel.get('name', '')
    url = channel.get('url', '')
    language = channel.get('language', '')
    category = channel.get('category', '')
    current_country = channel.get('country', '')
    
    found_country = None
    found_age = None
    
    # 1. Try to look up by channel name first (most reliable)
    name_lookup = lookup_channel_by_name(name)
    if name_lookup:
        found_country, found_age = name_lookup
    
    # 2. If no country found, try URL domain
    if not found_country and not current_country:
        found_country = lookup_country_by_url(url)
    
    # 3. If still no country, try language
    if not found_country and not current_country:
        found_country = lookup_country_by_language(language)
    
    # 4. If no age found from name, try category
    if found_age is None:
        found_age = lookup_age_by_category(category)
    
    # Update channel with found data (only if not already set)
    if found_country and not current_country:
        channel['country'] = found_country
        channel['country_source'] = 'lookup'
    
    if found_age is not None:
        # Store lookup age separately so it can be used as fallback
        channel['lookup_age'] = found_age
    
    return channel


def enrich_channels_metadata(channels: list) -> list:
    """
    Enrich a list of channels with looked up metadata.
    
    Args:
        channels: List of channel dictionaries
        
    Returns:
        List of enriched channel dictionaries
    """
    for channel in channels:
        lookup_channel_metadata(channel)
    
    return channels
