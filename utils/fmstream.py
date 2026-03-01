"""FMStream.org radio directory parser utility.

This module provides functionality to fetch and parse radio stations from
FMStream.org directory, extracting station information including stream URLs,
names, countries, genres, and bitrates.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests library not available - FMStream functionality will be disabled")


# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 15  # seconds
MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB limit
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
MAX_STATIONS = 5000  # Limit for DoS prevention

# Common stream URL patterns
STREAM_PATTERNS = [
    r'https?://[^\s<>"]+\.pls',
    r'https?://[^\s<>"]+\.m3u',
    r'https?://[^\s<>"]+/stream[^\s<>"]*',
    r'https?://[^\s<>"]+:\d{4,5}(?:/[^\s<>"]*)?',  # Port-based streams
]

# Bitrate patterns
BITRATE_PATTERN = r'(\d+)\s*k(?:bps|b/s)?'


def fetch_fmstream_stations(
    url: str = 'http://fmstream.org',
    existing_channels: Optional[List[Dict[str, Any]]] = None,
    max_stations: int = MAX_STATIONS
) -> List[Dict[str, Any]]:
    """
    Fetch and parse radio stations from FMStream.org.
    
    Main entry point for retrieving radio station listings from FMStream.org
    directory. Handles fetching HTML, parsing station information, selecting
    best quality streams, and deduplicating against existing channels.
    
    Args:
        url: Base URL of FMStream.org or specific directory page
        existing_channels: List of existing channels to deduplicate against
        max_stations: Maximum number of stations to return (DoS prevention)
        
    Returns:
        List of channel dictionaries compatible with existing channel structure
        
    Example:
        >>> stations = fetch_fmstream_stations()
        >>> for station in stations:
        ...     print(f"{station['name']} - {station['bitrate']}bps")
    """
    if not REQUESTS_AVAILABLE:
        logger.error("requests library not available - cannot fetch FMStream stations")
        return []
    
    # Security: Validate URL
    if not url or not isinstance(url, str):
        logger.error("Invalid URL provided")
        return []
    
    if not url.lower().startswith(('http://', 'https://')):
        logger.error(f"Invalid URL scheme: {url}")
        return []
    
    # Initialize existing channels set for deduplication
    existing_urls = set()
    existing_names = set()
    if existing_channels:
        for ch in existing_channels:
            if ch.get('url'):
                existing_urls.add(ch['url'].strip().lower())
            if ch.get('name'):
                existing_names.add(ch['name'].strip().lower())
    
    try:
        logger.info(f"Fetching FMStream directory from: {url}")
        
        # Fetch HTML content
        response = requests.get(
            url,
            timeout=DEFAULT_TIMEOUT,
            headers={'User-Agent': USER_AGENT},
            allow_redirects=True,
            stream=True  # Stream to check content length
        )
        response.raise_for_status()
        
        # Security: Check content length
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > MAX_CONTENT_SIZE:
            logger.error(f"Content too large: {content_length} bytes")
            return []
        
        # Read content with size limit
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > MAX_CONTENT_SIZE:
                logger.error("Content exceeded size limit during download")
                return []
        
        html_content = content.decode('utf-8', errors='ignore')
        
        # Parse HTML and extract stations
        stations = parse_html(html_content, base_url=url)
        
        logger.info(f"Extracted {len(stations)} stations from HTML")
        
        # Group stations by name to select best quality
        stations_by_name = {}
        for station in stations:
            name = station.get('name', '').lower()
            if name:
                if name not in stations_by_name:
                    stations_by_name[name] = []
                stations_by_name[name].append(station)
        
        # Select best quality for each station
        selected_stations = []
        for name, station_group in stations_by_name.items():
            best_station = select_best_quality(station_group)
            if best_station:
                selected_stations.append(best_station)
        
        logger.info(f"Selected {len(selected_stations)} unique stations after quality selection")
        
        # Deduplicate against existing channels
        new_stations = []
        for station in selected_stations:
            station_url = station.get('url', '').strip().lower()
            station_name = station.get('name', '').strip().lower()
            
            # Skip if URL or name already exists
            if station_url in existing_urls:
                logger.debug(f"Skipping duplicate URL: {station_url}")
                continue
            if station_name in existing_names:
                logger.debug(f"Skipping duplicate name: {station_name}")
                continue
            
            new_stations.append(station)
            
            # Limit number of stations
            if len(new_stations) >= max_stations:
                logger.warning(f"Reached maximum station limit: {max_stations}")
                break
        
        logger.info(f"Returning {len(new_stations)} new stations after deduplication")
        return new_stations
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching FMStream from {url}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching FMStream from {url}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching FMStream: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching FMStream: {e}")
    
    return []


def parse_html(html_content: str, base_url: str = '') -> List[Dict[str, Any]]:
    """
    Parse HTML directory listing to extract station information.
    
    Uses regular expressions to parse HTML and extract station entries.
    Lightweight approach without requiring BeautifulSoup or lxml.
    
    Args:
        html_content: Raw HTML content from FMStream.org
        base_url: Base URL for resolving relative links
        
    Returns:
        List of station dictionaries with extracted information
    """
    stations = []
    
    # Security: Validate input
    if not html_content or not isinstance(html_content, str):
        return stations
    
    # Security: Limit content length
    if len(html_content) > MAX_CONTENT_SIZE:
        html_content = html_content[:MAX_CONTENT_SIZE]
    
    try:
        # Pattern 1: Look for anchor tags with stream URLs
        # Matches: <a href="stream_url">Station Name</a>
        anchor_pattern = r'<a[^>]+href=["\']([^"\']+\.(?:pls|m3u|stream)[^"\']*)["\'][^>]*>([^<]+)</a>'
        for match in re.finditer(anchor_pattern, html_content, re.IGNORECASE):
            stream_url = match.group(1).strip()
            station_name = match.group(2).strip()
            
            if stream_url and station_name:
                # Extract additional info from surrounding context
                # Get 200 chars before and after the match for context
                start = max(0, match.start() - 200)
                end = min(len(html_content), match.end() + 200)
                context = html_content[start:end]
                
                station = extract_station_info(
                    station_name=station_name,
                    stream_url=stream_url,
                    context=context,
                    base_url=base_url
                )
                if station:
                    stations.append(station)
        
        # Pattern 2: Look for direct stream URLs in hrefs
        # Matches URLs with common streaming ports or paths
        stream_url_pattern = r'href=["\'](' + '|'.join(STREAM_PATTERNS) + r')["\']'
        for match in re.finditer(stream_url_pattern, html_content, re.IGNORECASE):
            stream_url = match.group(1).strip()
            
            # Try to find associated name in nearby text
            start = max(0, match.start() - 300)
            end = min(len(html_content), match.end() + 100)
            context = html_content[start:end]
            
            # Look for text in tags near the URL
            name_match = re.search(r'>([^<>]{3,100})</(?:a|span|div|td|p)', context)
            station_name = name_match.group(1).strip() if name_match else 'Unknown Station'
            
            station = extract_station_info(
                station_name=station_name,
                stream_url=stream_url,
                context=context,
                base_url=base_url
            )
            if station:
                # Check if this station URL is not already added
                if not any(s.get('url') == station.get('url') for s in stations):
                    stations.append(station)
        
        # Pattern 3: Look for table rows with station data
        # Common format: <tr><td>Name</td><td>URL</td><td>Bitrate</td></tr>
        table_row_pattern = r'<tr[^>]*>(.*?)</tr>'
        for row_match in re.finditer(table_row_pattern, html_content, re.IGNORECASE | re.DOTALL):
            row_content = row_match.group(1)
            
            # Extract cells
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row_content, re.IGNORECASE | re.DOTALL)
            if len(cells) >= 2:
                # Try to find URL and name in cells
                stream_url = None
                station_name = None
                
                for cell in cells:
                    # Check for URL in cell
                    url_match = re.search(r'href=["\']([^"\']+)["\']', cell)
                    if url_match:
                        potential_url = url_match.group(1)
                        if _is_valid_stream_url(potential_url):
                            stream_url = potential_url
                    
                    # Extract text from cell (remove tags)
                    text = re.sub(r'<[^>]+>', '', cell).strip()
                    if text and len(text) > 2 and not station_name:
                        station_name = text
                
                if stream_url and station_name:
                    station = extract_station_info(
                        station_name=station_name,
                        stream_url=stream_url,
                        context=row_content,
                        base_url=base_url
                    )
                    if station:
                        # Check for duplicates
                        if not any(s.get('url') == station.get('url') for s in stations):
                            stations.append(station)
        
        logger.info(f"Parsed {len(stations)} stations from HTML")
        
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
    
    return stations


def extract_station_info(
    station_name: str,
    stream_url: str,
    context: str = '',
    base_url: str = ''
) -> Optional[Dict[str, Any]]:
    """
    Extract and structure station information from raw data.
    
    Args:
        station_name: Name of the radio station
        stream_url: URL of the stream
        context: HTML context around the station entry
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Dictionary with structured channel information or None if invalid
    """
    # Security: Validate inputs
    if not station_name or not stream_url:
        return None
    
    if not isinstance(station_name, str) or not isinstance(stream_url, str):
        return None
    
    # Sanitize and validate
    station_name = _sanitize_text(station_name)[:200]
    if not station_name or station_name == 'Unknown Station':
        return None
    
    # Resolve relative URLs
    if base_url and not stream_url.startswith(('http://', 'https://')):
        stream_url = urljoin(base_url, stream_url)
    
    # Validate stream URL
    if not _is_valid_stream_url(stream_url):
        logger.debug(f"Invalid stream URL: {stream_url}")
        return None
    
    # Extract additional information from context
    country = _extract_country(context, station_name)
    genre = _extract_genre(context, station_name)
    bitrate = _extract_bitrate(context)
    language = _extract_language(context, country)
    logo = _extract_logo(context, base_url)
    
    # Build channel dictionary
    channel = {
        'name': station_name,
        'url': stream_url,
        'category': genre or 'Music',  # Default to Music for radio
        'country': country or 'Unknown',
        'language': language or None,
        'logo': logo or None,
        'media_type': 'Radio',  # Always Radio for FMStream
        'bitrate': bitrate,
    }
    
    return channel


def select_best_quality(stations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Select the best quality stream from multiple versions of the same station.
    
    Prefers higher bitrate streams. If bitrates are equal or unknown,
    prefers streams with more complete metadata.
    
    Args:
        stations: List of station dictionaries (same station, different qualities)
        
    Returns:
        The best quality station dictionary or None if list is empty
    """
    if not stations:
        return None
    
    if len(stations) == 1:
        return stations[0]
    
    # Sort by bitrate (highest first), then by metadata completeness
    def quality_score(station: Dict[str, Any]) -> Tuple[int, int]:
        bitrate = station.get('bitrate', 0) or 0
        
        # Count non-empty metadata fields
        metadata_count = sum([
            1 if station.get('country') and station.get('country') != 'Unknown' else 0,
            1 if station.get('category') else 0,
            1 if station.get('language') else 0,
            1 if station.get('logo') else 0,
        ])
        
        return (bitrate, metadata_count)
    
    # Sort stations by quality score (descending)
    sorted_stations = sorted(stations, key=quality_score, reverse=True)
    
    best = sorted_stations[0]
    logger.debug(f"Selected best quality for '{best.get('name')}': {best.get('bitrate')}bps")
    
    return best


def _sanitize_text(text: str) -> str:
    """
    Sanitize text to prevent injection attacks and clean up formatting.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ''
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&#39;': "'",
        '&nbsp;': ' ',
    }
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    # Remove control characters except newlines/tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Basic XSS prevention
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    return text.strip()


def _is_valid_stream_url(url: str) -> bool:
    """
    Validate stream URL for security and correctness.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid and safe, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Security: Length check
    if len(url) > 2000:
        return False
    
    url_lower = url.lower().strip()
    
    # Allow common streaming protocols
    allowed_schemes = ('http://', 'https://', 'rtmp://', 'rtsp://', 'mms://', 'mmsh://')
    if not url_lower.startswith(allowed_schemes):
        return False
    
    # Block dangerous schemes
    dangerous = ('javascript:', 'data:', 'file://', 'vbscript:', 'about:')
    if any(d in url_lower for d in dangerous):
        return False
    
    # Validate URL structure
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False
        
        # Block localhost and private IPs (basic check)
        if parsed.netloc.startswith(('localhost', '127.', '10.', '192.168.', '169.254.')):
            return False
            
    except Exception:
        return False
    
    return True


def _extract_country(context: str, station_name: str) -> str:
    """
    Extract country information from context or station name.
    
    Args:
        context: HTML context around station
        station_name: Name of the station
        
    Returns:
        Country name or 'Unknown'
    """
    if not context and not station_name:
        return 'Unknown'
    
    combined = f"{context} {station_name}".lower()
    
    # Common country patterns
    country_patterns = {
        'US': [r'\b(usa|united states|america|american)\b', r'\.us[/:]'],
        'UK': [r'\b(uk|united kingdom|british|britain|england)\b', r'\.uk[/:]'],
        'Germany': [r'\b(germany|german|deutsch|deutschland)\b', r'\.de[/:]'],
        'France': [r'\b(france|french|français)\b', r'\.fr[/:]'],
        'Spain': [r'\b(spain|spanish|españa|español)\b', r'\.es[/:]'],
        'Italy': [r'\b(italy|italian|italia|italiano)\b', r'\.it[/:]'],
        'Canada': [r'\b(canada|canadian)\b', r'\.ca[/:]'],
        'Australia': [r'\b(australia|australian)\b', r'\.au[/:]'],
        'Netherlands': [r'\b(netherlands|dutch|holland)\b', r'\.nl[/:]'],
        'Brazil': [r'\b(brazil|brasil|brazilian)\b', r'\.br[/:]'],
        'Russia': [r'\b(russia|russian|россия)\b', r'\.ru[/:]'],
        'Japan': [r'\b(japan|japanese|日本)\b', r'\.jp[/:]'],
        'China': [r'\b(china|chinese|中国)\b', r'\.cn[/:]'],
        'India': [r'\b(india|indian)\b', r'\.in[/:]'],
        'Mexico': [r'\b(mexico|mexican|méxico)\b', r'\.mx[/:]'],
        'Poland': [r'\b(poland|polish|polska)\b', r'\.pl[/:]'],
        'Sweden': [r'\b(sweden|swedish|sverige)\b', r'\.se[/:]'],
        'Norway': [r'\b(norway|norwegian|norge)\b', r'\.no[/:]'],
        'Denmark': [r'\b(denmark|danish|danmark)\b', r'\.dk[/:]'],
        'Finland': [r'\b(finland|finnish|suomi)\b', r'\.fi[/:]'],
        'Austria': [r'\b(austria|austrian|österreich)\b', r'\.at[/:]'],
        'Switzerland': [r'\b(switzerland|swiss|schweiz)\b', r'\.ch[/:]'],
        'Belgium': [r'\b(belgium|belgian|belgique)\b', r'\.be[/:]'],
        'Greece': [r'\b(greece|greek|ελλάδα)\b', r'\.gr[/:]'],
        'Turkey': [r'\b(turkey|turkish|türkiye)\b', r'\.tr[/:]'],
        'Israel': [r'\b(israel|israeli|hebrew|ישראל)\b', r'\.il[/:]'],
        'Argentina': [r'\b(argentina|argentinian)\b', r'\.ar[/:]'],
        'Chile': [r'\b(chile|chilean)\b', r'\.cl[/:]'],
        'Portugal': [r'\b(portugal|portuguese)\b', r'\.pt[/:]'],
        'Ireland': [r'\b(ireland|irish)\b', r'\.ie[/:]'],
    }
    
    for country, patterns in country_patterns.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return country
    
    return 'Unknown'


def _extract_genre(context: str, station_name: str) -> str:
    """
    Extract genre/category from context or station name.
    
    Args:
        context: HTML context around station
        station_name: Name of the station
        
    Returns:
        Genre/category name
    """
    if not context and not station_name:
        return 'Music'
    
    combined = f"{context} {station_name}".lower()
    
    # Genre patterns (ordered by specificity)
    genre_patterns = {
        'News': [r'\b(news|noticias|actualités|nachrichten|nyheter)\b'],
        'Sports': [r'\b(sports?|deportes|foot|fußball|soccer)\b'],
        'Jazz': [r'\bjazz\b'],
        'Classical': [r'\b(classical|classic|classique|klassisch|clásica)\b'],
        'Rock': [r'\b(rock|alternative)\b'],
        'Pop': [r'\b(pop|top ?40|hits)\b'],
        'Electronic': [r'\b(electronic|techno|house|trance|edm|dance)\b'],
        'Hip Hop': [r'\b(hip.?hop|rap|urban)\b'],
        'Country': [r'\bcountry\b'],
        'Latin': [r'\b(latin|salsa|reggaeton|bachata)\b'],
        'World': [r'\b(world|ethnic|folk|traditional)\b'],
        'Talk': [r'\b(talk|talk radio|conversation)\b'],
        'Religious': [r'\b(religious|christian|gospel|church|catholic)\b'],
    }
    
    for genre, patterns in genre_patterns.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return genre
    
    # Default to Music for radio stations
    return 'Music'


def _extract_bitrate(context: str) -> int:
    """
    Extract bitrate information from context.
    
    Args:
        context: HTML context around station
        
    Returns:
        Bitrate in bps (e.g., 128000) or 0 if not found
    """
    if not context:
        return 0
    
    # Look for bitrate patterns like "128kbps", "320 kbps", "128k"
    match = re.search(BITRATE_PATTERN, context, re.IGNORECASE)
    if match:
        try:
            bitrate_kbps = int(match.group(1))
            # Convert to bps
            bitrate_bps = bitrate_kbps * 1000
            
            # Sanity check (typical radio bitrates: 32kbps - 320kbps)
            if 32000 <= bitrate_bps <= 320000:
                return bitrate_bps
        except (ValueError, IndexError):
            pass
    
    return 0


def _extract_language(context: str, country: str) -> Optional[str]:
    """
    Extract or infer language from context or country.
    
    Args:
        context: HTML context around station
        country: Country of the station
        
    Returns:
        Language name or None
    """
    if context:
        combined = context.lower()
        
        # Language patterns
        language_patterns = {
            'English': [r'\b(english|en)\b'],
            'Spanish': [r'\b(spanish|español|es)\b'],
            'French': [r'\b(french|français|fr)\b'],
            'German': [r'\b(german|deutsch|de)\b'],
            'Italian': [r'\b(italian|italiano|it)\b'],
            'Portuguese': [r'\b(portuguese|português|pt)\b'],
            'Russian': [r'\b(russian|русский|ru)\b'],
            'Chinese': [r'\b(chinese|中文|zh)\b'],
            'Japanese': [r'\b(japanese|日本語|ja)\b'],
            'Arabic': [r'\b(arabic|عربي|ar)\b'],
            'Dutch': [r'\b(dutch|nederlands|nl)\b'],
            'Polish': [r'\b(polish|polski|pl)\b'],
            'Swedish': [r'\b(swedish|svenska|sv)\b'],
            'Turkish': [r'\b(turkish|türkçe|tr)\b'],
            'Hebrew': [r'\b(hebrew|עברית|he)\b'],
        }
        
        for language, patterns in language_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return language
    
    # Infer from country
    country_to_language = {
        'US': 'English',
        'UK': 'English',
        'Canada': 'English',
        'Australia': 'English',
        'Ireland': 'English',
        'Germany': 'German',
        'Austria': 'German',
        'Switzerland': 'German',
        'France': 'French',
        'Belgium': 'French',
        'Spain': 'Spanish',
        'Mexico': 'Spanish',
        'Argentina': 'Spanish',
        'Chile': 'Spanish',
        'Italy': 'Italian',
        'Brazil': 'Portuguese',
        'Portugal': 'Portuguese',
        'Russia': 'Russian',
        'Japan': 'Japanese',
        'China': 'Chinese',
        'Netherlands': 'Dutch',
        'Poland': 'Polish',
        'Sweden': 'Swedish',
        'Turkey': 'Turkish',
        'Israel': 'Hebrew',
    }
    
    return country_to_language.get(country)


def _extract_logo(context: str, base_url: str) -> Optional[str]:
    """
    Extract logo URL from context.
    
    Args:
        context: HTML context around station
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Logo URL or None
    """
    if not context:
        return None
    
    # Look for image tags
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    match = re.search(img_pattern, context, re.IGNORECASE)
    
    if match:
        logo_url = match.group(1).strip()
        
        # Resolve relative URLs
        if base_url and not logo_url.startswith(('http://', 'https://')):
            logo_url = urljoin(base_url, logo_url)
        
        # Validate logo URL
        if logo_url.lower().startswith(('http://', 'https://')):
            # Security: Length check
            if len(logo_url) <= 500:
                return logo_url
    
    return None


# Deduplication helper function
def deduplicate_stations(
    stations: List[Dict[str, Any]],
    existing_channels: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Remove duplicate stations based on URL and name matching.
    
    Args:
        stations: List of new stations to check
        existing_channels: List of existing channels to compare against
        
    Returns:
        List of unique stations not present in existing_channels
    """
    if not existing_channels:
        return stations
    
    # Build lookup sets
    existing_urls = {ch.get('url', '').strip().lower() for ch in existing_channels if ch.get('url')}
    existing_names = {ch.get('name', '').strip().lower() for ch in existing_channels if ch.get('name')}
    
    # Filter out duplicates
    unique_stations = []
    for station in stations:
        station_url = station.get('url', '').strip().lower()
        station_name = station.get('name', '').strip().lower()
        
        if station_url not in existing_urls and station_name not in existing_names:
            unique_stations.append(station)
    
    logger.info(f"Deduplicated {len(stations)} stations to {len(unique_stations)} unique entries")
    return unique_stations
