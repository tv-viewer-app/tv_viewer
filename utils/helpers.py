"""Helper utility functions for TV Viewer."""

import re
import json
import os
from typing import Dict, List, Any, Optional

# Import lookup functions
from .channel_lookup import (
    lookup_channel_by_name,
    lookup_country_by_url,
    lookup_country_by_language,
    lookup_age_by_category,
)


def parse_m3u(content: str) -> List[Dict[str, Any]]:
    """
    Parse M3U playlist content and extract channel information.
    
    Args:
        content: Raw M3U playlist content
        
    Returns:
        List of channel dictionaries with name, url, category, logo, etc.
    """
    channels = []
    
    # Security: Validate content is string
    if not isinstance(content, str):
        return channels
    
    # Security: Limit number of lines to prevent DoS
    lines = content.strip().split('\n')
    if len(lines) > 100000:  # Limit to 100k lines
        lines = lines[:100000]
    
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        
        # Security: Skip very long lines
        if len(line) > 10000:
            continue
        
        if line.startswith('#EXTINF:'):
            # Parse channel info
            current_channel = parse_extinf(line)
        elif line and not line.startswith('#'):
            # This is the URL - validate it
            url = line.strip()
            if url and _is_valid_stream_url(url):
                if current_channel:
                    current_channel['url'] = url
                    channels.append(current_channel)
                    current_channel = {}
    
    return channels


def _is_valid_stream_url(url: str) -> bool:
    """
    Validate stream URL for security.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid and safe
    """
    if not url or not isinstance(url, str):
        return False
    
    url_lower = url.lower().strip()
    
    # Allow common streaming protocols
    allowed_schemes = ('http://', 'https://', 'rtmp://', 'rtsp://', 'mms://', 'mmsh://')
    if not url_lower.startswith(allowed_schemes):
        return False
    
    # Block dangerous schemes
    dangerous = ('javascript:', 'data:', 'file://', 'vbscript:', 'about:')
    if url_lower.startswith(dangerous):
        return False
    
    return True


def parse_extinf(line: str) -> Dict[str, Any]:
    """
    Parse #EXTINF line to extract channel metadata.
    
    Args:
        line: The #EXTINF line from M3U file
        
    Returns:
        Dictionary with channel metadata
    """
    channel = {
        'name': 'Unknown',
        'category': 'Other',
        'logo': None,
        'language': None,
        'country': None,
    }
    
    # Security: Validate input
    if not line or not isinstance(line, str):
        return channel
    
    # Security: Limit line length
    if len(line) > 5000:
        line = line[:5000]
    
    # Extract attributes using regex
    # tvg-logo
    logo_match = re.search(r'tvg-logo="([^"]{0,500})"', line)
    if logo_match:
        logo_url = logo_match.group(1)
        # Security: Validate logo URL
        if logo_url.startswith(('http://', 'https://')):
            channel['logo'] = logo_url
    
    # tvg-name - sanitize to prevent XSS
    name_match = re.search(r'tvg-name="([^"]{0,200})"', line)
    if name_match:
        channel['name'] = _sanitize_text(name_match.group(1))
    
    # group-title (category)
    group_match = re.search(r'group-title="([^"]{0,100})"', line)
    if group_match:
        channel['category'] = _sanitize_text(group_match.group(1)) or 'Other'
    
    # tvg-language
    lang_match = re.search(r'tvg-language="([^"]{0,50})"', line)
    if lang_match:
        channel['language'] = _sanitize_text(lang_match.group(1))
    
    # tvg-country
    country_match = re.search(r'tvg-country="([^"]{0,50})"', line)
    if country_match:
        channel['country'] = _sanitize_text(country_match.group(1))
    
    # Extract name from end of line if not found
    if channel['name'] == 'Unknown':
        # Name is typically after the last comma
        parts = line.split(',')
        if len(parts) > 1:
            channel['name'] = _sanitize_text(parts[-1].strip()[:200])
    
    return channel


def _sanitize_text(text: str) -> str:
    """
    Sanitize text to prevent injection attacks.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ''
    
    # Remove control characters except newlines/tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Basic HTML entity encoding for display safety
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    return text.strip()


def load_json_file(filepath: str) -> Optional[Dict]:
    """Load JSON data from a file safely."""
    try:
        # Security: Validate filepath
        if not filepath or not isinstance(filepath, str):
            return None
        
        # Security: Check file exists and is a file
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            return None
        
        # Security: Check file size to prevent memory issues
        file_size = os.path.getsize(filepath)
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            print(f"File too large: {filepath}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"Error loading {filepath}: {e}")
    except Exception as e:
        print(f"Unexpected error loading {filepath}: {e}")
    return None


def save_json_file(filepath: str, data: Any) -> bool:
    """Save data to a JSON file safely."""
    try:
        # Security: Validate filepath
        if not filepath or not isinstance(filepath, str):
            return False
        
        # Write to temp file first, then rename (atomic operation)
        temp_filepath = filepath + '.tmp'
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Rename temp file to actual file (atomic on most systems)
        if os.path.exists(filepath):
            os.replace(temp_filepath, filepath)
        else:
            os.rename(temp_filepath, filepath)
        return True
    except IOError as e:
        print(f"Error saving {filepath}: {e}")
        # Clean up temp file if it exists
        if os.path.exists(filepath + '.tmp'):
            try:
                os.remove(filepath + '.tmp')
            except OSError:
                pass
    except Exception as e:
        print(f"Unexpected error saving {filepath}: {e}")
    return False


def categorize_channel(channel: Dict[str, Any]) -> str:
    """
    Determine the best category for a channel based on its metadata.
    Uses external lookup for known channels when category is unclear.
    
    Args:
        channel: Channel dictionary
        
    Returns:
        Category string (one of DEFAULT_CATEGORIES)
    """
    from config import DEFAULT_CATEGORIES
    from .channel_lookup import COUNTRY_NAMES
    
    raw_category = channel.get('category', '') or ''
    name = channel.get('name', '').lower()
    
    # Clean up category: take first part if semicolon-separated (e.g., "auto;series" -> "auto")
    if ';' in raw_category:
        raw_category = raw_category.split(';')[0].strip()
    
    category = raw_category.lower()
    
    # Map common category names to standard categories
    category_mapping = {
        'news': 'News',
        'sports': 'Sports',
        'sport': 'Sports',
        'entertainment': 'Entertainment',
        'movies': 'Movies',
        'movie': 'Movies',
        'cinema': 'Movies',
        'film': 'Movies',
        'music': 'Music',
        'kids': 'Kids',
        'children': 'Kids',
        'infantil': 'Kids',
        'cartoon': 'Kids',
        'animation': 'Kids',
        'anime': 'Entertainment',
        'documentary': 'Documentary',
        'education': 'Education',
        'general': 'General',
        'comedy': 'Comedy',
        'classic': 'Classic',
        'series': 'Series',
        'lifestyle': 'Lifestyle',
        'cooking': 'Lifestyle',
        'food': 'Lifestyle',
        'travel': 'Lifestyle',
        'fashion': 'Lifestyle',
        'religious': 'Religious',
        'religion': 'Religious',
        'faith': 'Religious',
        'church': 'Religious',
        'weather': 'News',
        'business': 'News',
        'science': 'Documentary',
        'nature': 'Documentary',
        'history': 'Documentary',
        'cultura': 'Documentary',
        'culture': 'Documentary',
        'radio': 'Radio',
        'fm': 'Radio',
    }
    
    # Check category field first
    for key, value in category_mapping.items():
        if key in category:
            return value
    
    # Check name field for category hints
    name_category_keywords = {
        'News': ['news', 'noticias', 'notizie', 'actualités', 'nachrichten', 'nouvelles', 'haber', 
                 'cnn', 'bbc news', 'fox news', 'sky news', 'al jazeera', 'reuters'],
        'Sports': ['sport', 'sports', 'futbol', 'football', 'soccer', 'basketball', 'tennis', 
                   'golf', 'cricket', 'rugby', 'nfl', 'nba', 'mlb', 'espn', 'eurosport', 'bein',
                   'sport 5', 'sky sports', 'bt sport', 'dazn'],
        'Kids': ['kids', 'junior', 'cartoon', 'disney', 'nick', 'nickelodeon', 
                 'boomerang', 'cbeebies', 'cbbc', 'baby', 'pbs kids', 'hop!', 'luli', 'hop ',
                 'junior', 'kika', 'gulli', 'clan', 'boing'],
        'Movies': ['movie', 'cinema', 'film', 'hbo', 'cinemax', 'starz', 'showtime', 
                   'sundance', 'tcm', 'amc', 'yes action', 'hot cinema', 'film4'],
        'Music': ['music', 'mtv', 'vh1', 'viva', 'trace', 'mezzo', 'music 24', 'vevo'],
        'Documentary': ['documentary', 'discovery', 'national geographic', 'nat geo', 
                       'history', 'science', 'animal planet', 'nature', 'arte', 'smithsonian'],
        'Entertainment': ['entertainment', 'variety', 'show', 'comedy', 'drama', 'series',
                         'fox', 'tbs', 'tnt', 'usa network', 'bravo', 'e!'],
        'Religious': ['religious', 'church', 'god', 'christian', 'catholic', 'islamic', 
                     'ewtn', 'daystar', 'tbn', 'god tv', 'prayer', 'bible', 'torah'],
        'Lifestyle': ['lifestyle', 'home', 'garden', 'hgtv', 'food', 'cooking', 'travel', 
                     'tlc', 'fashion', 'health', 'wellness'],
        'Radio': ['radio', ' fm', 'fm ', '.fm', '88fm', '99fm', '100fm', '103fm', 'galatz', 
                  'galgalatz', 'reshet bet', 'kol israel', 'army radio', 'bbc radio'],
    }
    
    for cat, keywords in name_category_keywords.items():
        for keyword in keywords:
            if keyword in name:
                return cat
    
    # If category from source data is valid (in DEFAULT_CATEGORIES and not a country), use it
    # First, normalize the raw category for comparison
    original_category = raw_category.strip() if raw_category else 'Other'
    
    # Check if it's a country name - if so, don't use it as category
    if original_category in COUNTRY_NAMES or original_category.upper() in COUNTRY_NAMES:
        return 'Other'
    
    # Check if it matches a default category (case-insensitive)
    for default_cat in DEFAULT_CATEGORIES:
        if original_category.lower() == default_cat.lower():
            return default_cat
    
    # Default to Other for uncategorized channels
    return 'Other'


def detect_media_type(channel: Dict[str, Any]) -> str:
    """
    Detect if a channel is TV or Radio based on name, category, URL.
    
    Args:
        channel: Channel dictionary
        
    Returns:
        'TV' or 'Radio'
    """
    name = channel.get('name', '').lower()
    category = channel.get('category', '').lower()
    url = channel.get('url', '').lower()
    
    radio_keywords = ['radio', ' fm', 'fm ', '.fm', '88fm', '99fm', '100fm', '103fm', 
                      'galatz', 'galgalatz', 'reshet bet', 'kol israel', 'army radio',
                      'bbc radio', 'npr', 'iheartradio', 'spotify', 'tunein',
                      'רדיו', 'גלצ', 'גלגלצ', 'רשת ב', 'קול ישראל']
    
    # Check if it's a radio station
    for keyword in radio_keywords:
        if keyword in name or keyword in category:
            return 'Radio'
    
    # Check URL patterns for radio
    radio_url_patterns = ['radio-browser', '/radio/', 'stream/radio', '.mp3', 'icecast']
    for pattern in radio_url_patterns:
        if pattern in url:
            return 'Radio'
    
    # Default to TV
    return 'TV'


def get_channel_country(channel: Dict[str, Any]) -> str:
    """
    Get the country for a channel, with fallback to external lookup.
    
    Args:
        channel: Channel dictionary
        
    Returns:
        Country string
    """
    import re
    
    # Check if country already set
    country = (channel.get('country') or '').strip()
    if country and country != 'Unknown':
        return country
    
    # Try lookup by channel name
    name = channel.get('name', '')
    name_lookup = lookup_channel_by_name(name)
    if name_lookup:
        return name_lookup[0]  # Return country from lookup
    
    # Try lookup by URL domain
    url = channel.get('url', '')
    url_country = lookup_country_by_url(url)
    if url_country:
        return url_country
    
    # Try lookup by language
    language = (channel.get('language') or '').lower()
    lang_country = lookup_country_by_language(language)
    if lang_country:
        return lang_country
    
    # Legacy fallback mapping
    if language:
        language_country_map = {
            'english': 'International',
            'spanish': 'Spain',
            'french': 'France',
            'german': 'Germany',
            'italian': 'Italy',
            'portuguese': 'Brazil',
            'russian': 'Russia',
            'arabic': 'Middle East',
            'chinese': 'China',
            'japanese': 'Japan',
            'korean': 'South Korea',
            'hindi': 'India',
            'hebrew': 'Israel',
            'turkish': 'Turkey',
            'dutch': 'Netherlands',
            'polish': 'Poland',
            'greek': 'Greece',
            'thai': 'Thailand',
            'vietnamese': 'Vietnam',
            'indonesian': 'Indonesia',
            'malay': 'Malaysia',
            'filipino': 'Philippines',
            'persian': 'Iran',
            'farsi': 'Iran',
            'tamil': 'India',
            'telugu': 'India',
            'bangla': 'India',
            'punjabi': 'India',
            'gujarati': 'India',
            'marathi': 'India',
            'kannada': 'India',
            'malayalam': 'India',
            'urdu': 'Pakistan',
            'pashto': 'Afghanistan',
        }
        for lang, ctry in language_country_map.items():
            if lang in language:
                return ctry
    
    # Try to infer country from channel name patterns (specific first)
    name_lower = name.lower()
    url_lower = url.lower()
    combined = name_lower + ' ' + url_lower
    
    # High confidence patterns with regex
    high_confidence_patterns = {
        'Israel': [
            r'\b(kan ?11|keshet ?12|reshet ?13|now ?14)\b',
            r'\b(i24 ?news|galgalatz|knesset|makan)\b',
            r'\bisrael\b',
            r'\bhebrew\b',
            r'\.il[:/]',
            r'[כקרעהספגמ]',  # Common Hebrew letters
        ],
        'US': [
            r'\b(cnn|msnbc|fox news|abc news|nbc news|cbs news)\b',
            r'\b(espn|nfl network|mlb network|nba tv)\b',
            r'\b(hbo|showtime|starz|cinemax|amc|fx|tnt|tbs)\b',
            r'\b(cartoon network|nickelodeon|disney channel)\b',
            r'\b(discovery|history channel|nat geo|animal planet)\b',
            r'\b(3abn|daystar|tbn|ewtn|pluto tv)\b',
            r'\b(filmrise)\b',
        ],
        'UK': [
            r'\b(bbc one|bbc two|bbc three|bbc four|bbc news)\b',
            r'\b(itv[1-4]?|channel 4|channel 5|sky)\b',
        ],
        'Germany': [
            r'\b(ard|zdf|rtl|sat\.?1|pro ?7|3sat)\b',
        ],
        'France': [
            r'\b(tf1|france ?[2-5]|canal\+?|bfm)\b',
        ],
        'Spain': [
            r'\b(tve|la ?[12]|antena ?3|telecinco|3cat)\b',
        ],
        'Italy': [
            r'\b(rai ?[1-5]|canale ?5|italia ?1|la ?7)\b',
        ],
        'Russia': [
            r'\b(russia ?[124]|россия|первый|нтв|стс)\b',
        ],
        'Japan': [
            r'\b(nhk|fuji|tv ?asahi|tbs japan)\b',
        ],
        'South Korea': [
            r'\b(kbs|mbc|sbs|tvn|jtbc)\b',
        ],
        'China': [
            r'\b(cctv|cgtn)\b',
        ],
        'India': [
            r'\b(zee|star ?plus|colors ?tv|sony ?tv|ndtv|dd ?national)\b',
            r'\b(9x|9xm)\b',
        ],
        'Australia': [
            r'\b(abc ?australia|9gem|9go|9life)\b',
        ],
        'Greece': [
            r'\b(cosmote|ert ?[123]?|ant1|alpha|skai)\b',
        ],
    }
    
    for ctry, patterns in high_confidence_patterns.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return ctry
    
    # Check URL TLD
    tld_match = re.search(r'https?://[^/]*\.([a-z]{2})[:/]', url_lower)
    if tld_match:
        tld = tld_match.group(1)
        tld_countries = {
            'us': 'US', 'uk': 'UK', 'de': 'Germany', 'fr': 'France',
            'es': 'Spain', 'it': 'Italy', 'ru': 'Russia', 'jp': 'Japan',
            'kr': 'South Korea', 'cn': 'China', 'in': 'India', 'br': 'Brazil',
            'mx': 'Mexico', 'ca': 'Canada', 'au': 'Australia', 'tr': 'Turkey',
            'nl': 'Netherlands', 'pl': 'Poland', 'il': 'Israel', 'ae': 'UAE',
            'sa': 'Saudi Arabia', 'eg': 'Egypt', 'ar': 'Argentina', 'cl': 'Chile',
            'gr': 'Greece', 'ua': 'Ukraine', 'ro': 'Romania', 'hu': 'Hungary',
            'cz': 'Czech Republic', 'th': 'Thailand', 'vn': 'Vietnam',
        }
        if tld in tld_countries:
            return tld_countries[tld]
    
    # Lower confidence name patterns
    name_country_patterns = {
        'US': ['usa', 'america', 'american'],
        'UK': ['british', 'britain'],
        'Germany': ['german', 'deutsch'],
        'France': ['french'],
        'Spain': ['spanish', 'spain', 'españa'],
        'Italy': ['italian', 'italia'],
        'Russia': ['russian'],
        'Japan': ['japan', 'japanese'],
        'South Korea': ['korea', 'korean'],
        'China': ['china', 'chinese'],
        'India': ['india', 'indian', 'hindi', 'tamil', 'telugu'],
        'Brazil': ['brazil', 'brasil'],
        'Mexico': ['mexico', 'mexican'],
        'Turkey': ['turkey', 'turkish', 'türk'],
        'UAE': ['dubai', 'abu dhabi', 'uae', 'emirates'],
        'Saudi Arabia': ['saudi'],
        'Qatar': ['qatar', 'al jazeera'],
        'Australia': ['australia', 'australian'],
        'Canada': ['canada', 'canadian'],
    }
    
    for ctry, patterns in name_country_patterns.items():
        for pattern in patterns:
            if pattern in name_lower:
                return ctry
    
    return 'Unknown'


def get_minimum_age(channel: Dict[str, Any]) -> int:
    """
    Determine the recommended minimum age for a channel based on its content.
    Uses external lookup for known channels.
    
    Args:
        channel: Channel dictionary
        
    Returns:
        Minimum recommended age (0, 7, 13, 16, 18)
    """
    # Check if we have a lookup result
    lookup_age = channel.get('lookup_age')
    
    # Try name-based lookup for known channels
    name = channel.get('name', '')
    name_lookup = lookup_channel_by_name(name)
    if name_lookup:
        return name_lookup[1]  # Return age from lookup
    
    category = (channel.get('category') or '').lower()
    name_lower = name.lower()
    
    # Try category-based lookup
    category_age = lookup_age_by_category(category)
    if category_age is not None:
        return category_age
    
    # Kids channels - all ages (0+)
    kids_keywords = ['kids', 'children', 'cartoon', 'disney', 'nick', 'junior',
                     'baby', 'sesame', 'pbs kids', 'cbbc', 'cbeebies', 'boomerang',
                     'pogo', 'hungama', 'clan', 'boing', 'gulli', 'tiji', 'kika',
                     'super rtl', 'france 4']
    for keyword in kids_keywords:
        if keyword in category or keyword in name_lower:
            return 0
    
    # Adult/mature content (18+)
    adult_keywords = ['adult', 'xxx', '18+', 'erotic', 'playboy', 'mature']
    for keyword in adult_keywords:
        if keyword in category or keyword in name_lower:
            return 18
    
    # Action/violence potential (16+)
    mature_keywords = ['action', 'thriller', 'horror', 'crime', 'war']
    for keyword in mature_keywords:
        if keyword in category or keyword in name_lower:
            return 16
    
    # Teen content (13+)
    teen_keywords = ['drama', 'reality', 'music', 'mtv', 'vh1', 'comedy']
    for keyword in teen_keywords:
        if keyword in category or keyword in name_lower:
            return 13
    
    # Family/general content (7+)
    family_keywords = ['family', 'entertainment', 'general', 'lifestyle']
    for keyword in family_keywords:
        if keyword in category or keyword in name_lower:
            return 7
    
    # News, sports, documentary - general audience (7+)
    general_keywords = ['news', 'sports', 'sport', 'documentary', 'education',
                        'weather', 'travel', 'nature', 'science', 'history']
    for keyword in general_keywords:
        if keyword in category or keyword in name_lower:
            return 7
    
    # Movies - default to teen (13+) as content varies
    if 'movie' in category or 'cinema' in category or 'film' in category:
        return 13
    
    # Use lookup age if available
    if lookup_age is not None:
        return lookup_age
    
    # Default to 7+ for unclassified content
    return 7


def format_age_rating(age: int) -> str:
    """
    Format age rating for display.
    
    Args:
        age: Minimum age number
        
    Returns:
        Formatted age rating string
    """
    if age == 0:
        return "All Ages"
    return f"{age}+"


def format_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
