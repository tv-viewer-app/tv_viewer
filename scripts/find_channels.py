#!/usr/bin/env python3
"""
find_channels.py — TV Viewer Channel Agent
===========================================

Called by GitHub Actions to process channel-request issues.

Workflow:
  1. Parse the GitHub issue body (markdown from issue forms)
  2. Fetch available channels from iptv-org M3U playlists
  3. Fuzzy-match requested channel names against available streams
  4. Check which channels already exist in channels_config.json
  5. Validate stream health (HTTP HEAD, 5 s timeout)
  6. Output structured JSON + formatted markdown comment

Usage:
  python find_channels.py \\
      --issue-body path/to/issue_body.md \\
      --config path/to/channels_config.json \\
      --output-dir path/to/output/

  # Or pass the body as a string directly (useful in CI):
  python find_channels.py \\
      --issue-body-text "### Country / Region\\nUnited Kingdom\\n..." \\
      --config ../channels_config.json

Dependencies: Python 3.9+ stdlib only (no pip packages).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging — all diagnostic output goes to stderr so CI can capture it
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger("find_channels")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_CHANNELS_PER_REQUEST = 50
HEALTH_CHECK_TIMEOUT = 5        # seconds
HEALTH_CHECK_WORKERS = 10       # max concurrent HEAD requests
FETCH_TIMEOUT = 15              # seconds for M3U playlist downloads
USER_AGENT = "TVViewer-ChannelAgent/1.0"

IPTV_ORG_COUNTRY_URL = "https://iptv-org.github.io/iptv/countries/{code}.m3u"
IPTV_ORG_INDEX_URL = "https://iptv-org.github.io/iptv/index.m3u"

# Minimum ratio of matched channels before we also search the global index
COUNTRY_MATCH_THRESHOLD = 0.5

# ---------------------------------------------------------------------------
# Country code mapping — common names / abbreviations → ISO 3166-1 alpha-2
# ---------------------------------------------------------------------------
COUNTRY_MAP: dict[str, str] = {
    # United Kingdom
    "uk": "gb", "united kingdom": "gb", "england": "gb",
    "britain": "gb", "great britain": "gb", "gb": "gb",
    # United States
    "us": "us", "usa": "us", "united states": "us", "america": "us",
    # Europe
    "spain": "es", "france": "fr", "germany": "de", "italy": "it",
    "portugal": "pt", "netherlands": "nl", "poland": "pl",
    "sweden": "se", "norway": "no", "denmark": "dk",
    "greece": "gr", "czech republic": "cz", "czechia": "cz",
    "romania": "ro", "hungary": "hu", "austria": "at",
    "switzerland": "ch", "belgium": "be", "ireland": "ie",
    "finland": "fi", "ukraine": "ua", "croatia": "hr",
    "serbia": "rs",
    # Middle East
    "israel": "il", "turkey": "tr", "saudi arabia": "sa",
    "uae": "ae", "united arab emirates": "ae", "qatar": "qa",
    "egypt": "eg",
    # Americas
    "brazil": "br", "mexico": "mx", "canada": "ca",
    "argentina": "ar", "colombia": "co", "chile": "cl", "peru": "pe",
    # Asia
    "india": "in", "japan": "jp", "china": "cn",
    "south korea": "kr", "korea": "kr", "thailand": "th",
    "indonesia": "id", "malaysia": "my", "philippines": "ph",
    "vietnam": "vn",
    # Oceania
    "australia": "au", "new zealand": "nz",
    # Russia
    "russia": "ru",
    # Africa
    "south africa": "za", "nigeria": "ng", "kenya": "ke",
}

# Common channel-name variations: digit ↔ word, "HD"/"FHD" suffixes, etc.
_DIGIT_WORDS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
    "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen",
}
_WORD_DIGITS = {v: k for k, v in _DIGIT_WORDS.items()}


# ========================== Data Classes ==================================

@dataclass
class ChannelRequest:
    """Parsed user request from a GitHub issue body."""
    country_raw: str = ""
    country_code: str = ""
    channels: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class M3UChannel:
    """A single channel entry parsed from an M3U playlist."""
    name: str = ""
    url: str = ""
    category: str = ""
    country: str = ""
    tvg_id: str = ""
    tvg_logo: str = ""


@dataclass
class FoundChannel:
    """A channel matched to a user request."""
    name: str
    url: str
    category: str
    country: str
    healthy: bool = False
    already_exists: bool = False
    matched_query: str = ""       # the original user query that matched


@dataclass
class SearchResults:
    """Complete results of a channel search."""
    request: dict = field(default_factory=dict)
    found: list[dict] = field(default_factory=list)
    not_found: list[str] = field(default_factory=list)
    already_available: list[str] = field(default_factory=list)
    summary: str = ""


# ========================== Issue Body Parser =============================

def parse_issue_body(body: str) -> ChannelRequest:
    """
    Parse a GitHub issue form body (markdown with ### headers).

    Expected format:
        ### Country / Region
        United Kingdom

        ### Channels you'd like added
        BBC One
        ITV
        ...

        ### Genres you're interested in
        News, Sports

        ### Additional notes
        ...
    """
    req = ChannelRequest()

    # Split by H3 headers; each section starts with "### <Label>"
    sections: dict[str, str] = {}
    current_key = ""
    current_lines: list[str] = []

    for line in body.splitlines():
        if line.startswith("### "):
            # Save previous section
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = line[4:].strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    # Don't forget the last section
    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    log.debug("Parsed sections: %s", list(sections.keys()))

    # --- Country ---
    for key in ("country / region", "country", "country/region", "region"):
        if key in sections:
            raw = sections[key].strip().splitlines()[0].strip()
            req.country_raw = raw
            req.country_code = resolve_country_code(raw)
            break

    # --- Channels ---
    for key in ("channels you'd like added", "channels", "channel names",
                 "requested channels"):
        if key in sections:
            lines = sections[key].strip().splitlines()
            req.channels = [
                ln.strip().lstrip("-•*").strip()
                for ln in lines
                if ln.strip() and not ln.strip().startswith("<!--")
            ]
            break

    # Cap at MAX_CHANNELS_PER_REQUEST
    if len(req.channels) > MAX_CHANNELS_PER_REQUEST:
        log.warning(
            "Request contains %d channels; capping at %d.",
            len(req.channels), MAX_CHANNELS_PER_REQUEST,
        )
        req.channels = req.channels[:MAX_CHANNELS_PER_REQUEST]

    # --- Genres ---
    for key in ("genres you're interested in", "genres", "categories",
                 "genres/categories"):
        if key in sections:
            raw_genres = sections[key].strip()
            # Support both comma-separated and one-per-line
            if "," in raw_genres:
                req.genres = [g.strip() for g in raw_genres.split(",") if g.strip()]
            else:
                req.genres = [
                    ln.strip().lstrip("-•*").strip()
                    for ln in raw_genres.splitlines()
                    if ln.strip()
                ]
            break

    # --- Notes ---
    for key in ("additional notes", "notes", "additional details"):
        if key in sections:
            req.notes = sections[key].strip()
            break

    log.info(
        "Parsed request: country=%s (%s), %d channels, %d genres",
        req.country_raw, req.country_code,
        len(req.channels), len(req.genres),
    )
    return req


def resolve_country_code(raw: str) -> str:
    """
    Map a free-text country name to an ISO 3166-1 alpha-2 code.

    Falls back to the raw string lowered if it looks like a 2-letter code.
    """
    normalised = raw.strip().lower()

    # Direct lookup
    if normalised in COUNTRY_MAP:
        return COUNTRY_MAP[normalised]

    # Already a 2-letter code?
    if len(normalised) == 2 and normalised.isalpha():
        return normalised

    log.warning("Could not map country '%s' to a code; using as-is.", raw)
    return normalised


# ========================== M3U Fetcher / Parser ==========================

def _http_get(url: str, timeout: int = FETCH_TIMEOUT) -> Optional[str]:
    """Fetch a URL and return its text content, or None on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        log.warning("Failed to fetch %s: %s", url, exc)
        return None


def parse_m3u(text: str) -> list[M3UChannel]:
    """
    Parse an M3U/M3U8 playlist into a list of M3UChannel objects.

    Format:
        #EXTM3U
        #EXTINF:-1 tvg-id="..." tvg-country="..." group-title="...",Channel Name
        http://stream.url/path
    """
    channels: list[M3UChannel] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            ch = M3UChannel()

            # Extract attributes from the EXTINF line
            # tvg-id
            m = re.search(r'tvg-id="([^"]*)"', line)
            if m:
                ch.tvg_id = m.group(1)

            # tvg-country
            m = re.search(r'tvg-country="([^"]*)"', line)
            if m:
                ch.country = m.group(1)

            # tvg-logo
            m = re.search(r'tvg-logo="([^"]*)"', line)
            if m:
                ch.tvg_logo = m.group(1)

            # group-title (category)
            m = re.search(r'group-title="([^"]*)"', line)
            if m:
                ch.category = m.group(1)

            # Channel name is everything after the last comma in the EXTINF line
            comma_pos = line.rfind(",")
            if comma_pos != -1:
                ch.name = line[comma_pos + 1:].strip()

            # Next non-empty, non-comment line is the URL
            i += 1
            while i < len(lines):
                url_line = lines[i].strip()
                if url_line and not url_line.startswith("#"):
                    ch.url = url_line
                    break
                elif url_line.startswith("#EXTINF:"):
                    # Another EXTINF without a URL — skip back so outer loop
                    # re-processes this line
                    i -= 1
                    break
                i += 1

            if ch.name and ch.url:
                channels.append(ch)
        i += 1

    return channels


def fetch_channels_for_country(country_code: str) -> list[M3UChannel]:
    """
    Fetch M3U channels for a given country code from iptv-org.

    Returns channels from the country-specific playlist. If fewer than
    COUNTRY_MATCH_THRESHOLD of requested channels are found, the caller
    should also search the global index.
    """
    url = IPTV_ORG_COUNTRY_URL.format(code=country_code)
    log.info("Fetching country playlist: %s", url)
    text = _http_get(url)
    if text is None:
        log.warning("Country playlist not available for '%s'.", country_code)
        return []

    channels = parse_m3u(text)
    log.info("Parsed %d channels from country playlist (%s).", len(channels), country_code)
    return channels


def fetch_global_channels() -> list[M3UChannel]:
    """Fetch the full iptv-org global index as a fallback."""
    log.info("Fetching global index playlist: %s", IPTV_ORG_INDEX_URL)
    text = _http_get(IPTV_ORG_INDEX_URL)
    if text is None:
        log.warning("Global index playlist not available.")
        return []

    channels = parse_m3u(text)
    log.info("Parsed %d channels from global index.", len(channels))
    return channels


# ========================== Fuzzy Matching ================================

def _normalise(name: str) -> str:
    """
    Normalise a channel name for comparison.

    - Lower-case
    - Strip quality suffixes (HD, FHD, SD, 4K, UHD)
    - Replace digits ↔ word equivalents so "BBC 1" matches "BBC One"
    - Collapse whitespace
    """
    s = name.lower().strip()
    # Remove common quality / variant tags
    s = re.sub(r"\b(hd|fhd|sd|4k|uhd|hevc|h\.?265|h\.?264)\b", "", s, flags=re.IGNORECASE)
    # Remove parenthesised content (e.g. "(Israel)")
    s = re.sub(r"\([^)]*\)", "", s)
    # Replace word-digits with numeric digits for canonical form
    for word, digit in _WORD_DIGITS.items():
        s = re.sub(rf"\b{word}\b", digit, s)
    # Collapse whitespace / strip
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _name_matches(query: str, candidate: str) -> bool:
    """
    Determine whether *query* fuzzy-matches *candidate*.

    Strategy:
      1. Exact normalised match
      2. One is a substring of the other (after normalisation)
      3. All significant tokens of the query appear in the candidate
    """
    nq = _normalise(query)
    nc = _normalise(candidate)

    if not nq or not nc:
        return False

    # Exact match
    if nq == nc:
        return True

    # Substring (either direction)
    if nq in nc or nc in nq:
        return True

    # Token-based: every token in the query must appear in the candidate
    q_tokens = set(nq.split())
    c_tokens = set(nc.split())
    if q_tokens and q_tokens.issubset(c_tokens):
        return True

    return False


def match_channels(
    queries: list[str],
    available: list[M3UChannel],
) -> tuple[dict[str, list[M3UChannel]], list[str]]:
    """
    Match a list of user-requested channel names against available M3U entries.

    Returns:
        found: mapping of original query → list of matching M3UChannels
        not_found: list of queries with zero matches
    """
    found: dict[str, list[M3UChannel]] = {}
    not_found: list[str] = []

    for query in queries:
        matches = [ch for ch in available if _name_matches(query, ch.name)]
        if matches:
            found[query] = matches
        else:
            not_found.append(query)

    return found, not_found


# ========================== Duplicate Detection ===========================

def load_config(config_path: str | Path) -> dict:
    """Load channels_config.json and return its contents."""
    path = Path(config_path)
    if not path.exists():
        log.warning("Config file not found: %s — skipping duplicate check.", path)
        return {}

    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def check_already_exists(
    channel: M3UChannel,
    config: dict,
    country_code: str,
) -> bool:
    """
    Return True if *channel* is already represented in the config.

    Checks:
      - Whether the country M3U is already in ``repositories``
        (meaning all channels for that country are implicitly available).
      - Whether the channel name fuzzy-matches any ``custom_channels`` entry.
      - Whether the exact URL already appears in ``custom_channels``.
    """
    # Check repositories for the country playlist
    repos: list[str] = config.get("repositories", [])
    country_playlist_url = IPTV_ORG_COUNTRY_URL.format(code=country_code)
    if country_playlist_url in repos:
        return True

    # Check custom_channels by name or URL
    for cc in config.get("custom_channels", []):
        if _name_matches(channel.name, cc.get("name", "")):
            return True
        if channel.url and channel.url == cc.get("url", ""):
            return True

    return False


# ========================== Health Checking ===============================

def _check_stream_health(url: str) -> bool:
    """
    Check if a stream URL is responsive.

    Sends an HTTP HEAD request (with GET fallback) and considers 2xx / 3xx
    status codes as healthy.
    """
    headers = {"User-Agent": USER_AGENT}
    # Try HEAD first
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=HEALTH_CHECK_TIMEOUT) as resp:
                if 200 <= resp.status < 400:
                    return True
        except (urllib.error.HTTPError, urllib.error.URLError, OSError):
            if method == "HEAD":
                continue  # Retry with GET
            return False
    return False


def check_health_batch(channels: list[FoundChannel]) -> None:
    """
    Run health checks for a batch of channels using a thread pool.

    Mutates each channel's ``healthy`` field in place.
    """
    if not channels:
        return

    log.info("Running health checks on %d streams (max %d workers)…",
             len(channels), HEALTH_CHECK_WORKERS)
    t0 = time.monotonic()

    with ThreadPoolExecutor(max_workers=HEALTH_CHECK_WORKERS) as pool:
        future_to_ch = {
            pool.submit(_check_stream_health, ch.url): ch
            for ch in channels
        }
        for future in as_completed(future_to_ch):
            ch = future_to_ch[future]
            try:
                ch.healthy = future.result()
            except Exception as exc:
                log.debug("Health check exception for %s: %s", ch.url, exc)
                ch.healthy = False

    elapsed = time.monotonic() - t0
    healthy_count = sum(1 for ch in channels if ch.healthy)
    log.info("Health checks done in %.1f s — %d/%d healthy.",
             elapsed, healthy_count, len(channels))


# ========================== Result Formatting =============================

def build_results(
    request: ChannelRequest,
    found_channels: list[FoundChannel],
    not_found: list[str],
) -> SearchResults:
    """Assemble the final SearchResults object."""
    new_channels = [ch for ch in found_channels if not ch.already_exists]
    already = [ch for ch in found_channels if ch.already_exists]

    summary_parts = []
    if new_channels:
        summary_parts.append(f"Found {len(new_channels)} new channel(s)")
    if already:
        summary_parts.append(f"{len(already)} already available")
    if not_found:
        summary_parts.append(f"{len(not_found)} not found")

    return SearchResults(
        request={
            "country": request.country_code,
            "country_raw": request.country_raw,
            "channels": request.channels,
            "genres": request.genres,
        },
        found=[
            {
                "name": ch.name,
                "url": ch.url,
                "category": ch.category,
                "country": ch.country,
                "healthy": ch.healthy,
                "already_exists": ch.already_exists,
                "matched_query": ch.matched_query,
            }
            for ch in found_channels
        ],
        not_found=not_found,
        already_available=[ch.matched_query or ch.name for ch in already],
        summary=", ".join(summary_parts) if summary_parts else "No results",
    )


def write_json(results: SearchResults, output_path: Path) -> None:
    """Write structured JSON results to *output_path*."""
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(asdict(results), fh, indent=2, ensure_ascii=False)
    log.info("Wrote JSON results to %s", output_path)


def _status_icon(ch: dict) -> str:
    """Return a status emoji for a channel dict."""
    if ch.get("already_exists"):
        return "ℹ️ Exists"
    return "🟢 Live" if ch.get("healthy") else "🔴 Down"


def write_markdown(results: SearchResults, output_path: Path) -> None:
    """Write a formatted GitHub comment to *output_path*."""
    lines: list[str] = []

    country_display = results.request.get("country_raw", results.request.get("country", ""))
    channel_list = ", ".join(results.request.get("channels", [])[:8])
    if len(results.request.get("channels", [])) > 8:
        channel_list += ", …"

    lines.append("## 🤖 Channel Agent Results\n")
    lines.append(f"**Request:** {country_display} channels — {channel_list}\n")

    # --- New channels found ---
    new_channels = [ch for ch in results.found if not ch.get("already_exists")]
    if new_channels:
        lines.append(f"### ✅ New Channels Found ({len(new_channels)})\n")
        lines.append("| Channel | Category | Status | URL |")
        lines.append("|---------|----------|--------|-----|")
        for ch in new_channels:
            status = "🟢 Live" if ch.get("healthy") else "🔴 Down"
            url_display = f"`{ch['url'][:80]}{'…' if len(ch['url']) > 80 else ''}`"
            lines.append(
                f"| {ch['name']} | {ch.get('category', '—')} | {status} | {url_display} |"
            )
        lines.append("")

    # --- Already available ---
    already = [ch for ch in results.found if ch.get("already_exists")]
    if already:
        lines.append(f"### ℹ️ Already Available ({len(already)})\n")
        lines.append("These channels are already in TV Viewer's database:\n")
        for ch in already:
            query = ch.get("matched_query", ch["name"])
            lines.append(
                f"- **{query}** — matched as *{ch['name']}* "
                f"(via {results.request.get('country_raw', 'configured')} playlist)"
            )
        lines.append("")

    # --- Not found ---
    if results.not_found:
        lines.append(f"### ❌ Not Found ({len(results.not_found)})\n")
        for name in results.not_found:
            lines.append(f"- **{name}** — no matching stream found in public sources")
        lines.append("")

    # --- Footer ---
    lines.append("---")
    lines.append(
        "*Channels marked 🟢 Live passed health checks. "
        "A PR will be created to add new channels.*"
    )
    lines.append("*This is an automated response from the TV Viewer Channel Agent.*\n")

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    log.info("Wrote markdown comment to %s", output_path)


# ========================== Main Orchestrator =============================

def run(
    issue_body: str,
    config_path: str | Path,
    output_dir: str | Path,
) -> SearchResults:
    """
    End-to-end channel search pipeline.

    1. Parse the issue body
    2. Fetch M3U playlists
    3. Match channels
    4. Check duplicates
    5. Health-check streams
    6. Write results
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # -- Step 1: Parse --------------------------------------------------------
    request = parse_issue_body(issue_body)
    if not request.country_code:
        log.error("Could not determine country from issue body.")
        # Still continue — we can try the global index
    if not request.channels:
        log.error("No channels found in issue body. Nothing to do.")
        empty = SearchResults(
            request={"country": request.country_code, "channels": [], "genres": []},
            summary="No channels requested",
        )
        write_json(empty, output_dir / "channel_results.json")
        write_markdown(empty, output_dir / "channel_comment.md")
        return empty

    # -- Step 2: Fetch M3U playlists ------------------------------------------
    country_channels: list[M3UChannel] = []
    if request.country_code:
        country_channels = fetch_channels_for_country(request.country_code)

    # Try matching against country playlist first
    found_map, not_found_names = match_channels(request.channels, country_channels)

    # If too many misses, also search the global index
    if request.channels and (
        len(not_found_names) / len(request.channels) > (1 - COUNTRY_MATCH_THRESHOLD)
    ):
        log.info(
            "%d/%d channels unmatched in country playlist; "
            "searching global index as fallback…",
            len(not_found_names), len(request.channels),
        )
        global_channels = fetch_global_channels()
        global_found, still_not_found = match_channels(not_found_names, global_channels)
        found_map.update(global_found)
        not_found_names = still_not_found

    # -- Step 3: Load config for duplicate detection --------------------------
    config = load_config(config_path)

    # -- Step 4: Build FoundChannel list (pick best match per query) ----------
    found_channels: list[FoundChannel] = []
    seen_urls: set[str] = set()

    for query, matches in found_map.items():
        # Prefer an exact normalised match, then shortest name (likely base channel)
        matches.sort(key=lambda c: (0 if _normalise(c.name) == _normalise(query) else 1, len(c.name)))
        best = matches[0]

        # Skip duplicate URLs (can happen when country + global overlap)
        if best.url in seen_urls:
            continue
        seen_urls.add(best.url)

        already = check_already_exists(best, config, request.country_code)
        found_channels.append(FoundChannel(
            name=best.name,
            url=best.url,
            category=best.category or "General",
            country=best.country or request.country_raw,
            already_exists=already,
            matched_query=query,
        ))

    # -- Step 5: Health checks (only for new channels) ------------------------
    new_channels = [ch for ch in found_channels if not ch.already_exists]
    check_health_batch(new_channels)

    # -- Step 6: Build & write results ----------------------------------------
    results = build_results(request, found_channels, not_found_names)

    write_json(results, output_dir / "channel_results.json")
    write_markdown(results, output_dir / "channel_comment.md")

    log.info("Done. %s", results.summary)
    return results


# ========================== CLI Entry Point ===============================

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="TV Viewer Channel Agent — process channel requests from GitHub issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument(
        "--issue-body",
        metavar="FILE",
        help="Path to a file containing the GitHub issue body (markdown).",
    )
    body_group.add_argument(
        "--issue-body-text",
        metavar="TEXT",
        help="The GitHub issue body as a literal string argument.",
    )

    parser.add_argument(
        "--config",
        metavar="FILE",
        default=str(Path(__file__).resolve().parent.parent / "channels_config.json"),
        help=(
            "Path to channels_config.json "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default=".",
        help="Directory for output files (default: current directory).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 1 on failure."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Read issue body
    if args.issue_body:
        body_path = Path(args.issue_body)
        if not body_path.exists():
            log.error("Issue body file not found: %s", body_path)
            return 1
        issue_body = body_path.read_text(encoding="utf-8")
    else:
        issue_body = args.issue_body_text

    if not issue_body or not issue_body.strip():
        log.error("Issue body is empty.")
        return 1

    try:
        results = run(issue_body, args.config, args.output_dir)
    except Exception:
        log.exception("Unhandled error during channel search.")
        return 1

    # Exit 0 even if nothing was found — the outputs describe the outcome
    return 0


if __name__ == "__main__":
    sys.exit(main())
