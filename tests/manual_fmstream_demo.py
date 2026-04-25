"""Manual GUI test - not part of automated test suite.

CLI demo script for FMStream radio directory parser.
This script tests the FMStream utility by fetching a sample of radio stations
and displaying their information.

Usage:
    python tests/manual_fmstream_demo.py
    python tests/manual_fmstream_demo.py --url http://fmstream.org
    python tests/manual_fmstream_demo.py --max 50
"""

import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fmstream import fetch_fmstream_stations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test FMStream radio parser')
    parser.add_argument('--url', default='http://fmstream.org', help='FMStream URL')
    parser.add_argument('--max', type=int, default=100, help='Max stations to fetch')
    parser.add_argument('--country', help='Filter by country')
    parser.add_argument('--genre', help='Filter by genre')
    parser.add_argument('--min-bitrate', type=int, help='Minimum bitrate (kbps)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        logger.info(f"Fetching radio stations from {args.url}")
        logger.info(f"Max stations: {args.max}")
        
        # Fetch stations
        stations = fetch_fmstream_stations(
            url=args.url,
            max_stations=args.max
        )
        
        if not stations:
            logger.warning("No stations found!")
            return
        
        logger.info(f"Found {len(stations)} radio stations")
        
        # Apply filters
        filtered_stations = stations
        
        if args.country:
            filtered_stations = [
                s for s in filtered_stations 
                if s.get('country', '').lower() == args.country.lower()
            ]
            logger.info(f"Filtered to {len(filtered_stations)} stations from {args.country}")
        
        if args.genre:
            filtered_stations = [
                s for s in filtered_stations 
                if s.get('category', '').lower() == args.genre.lower()
            ]
            logger.info(f"Filtered to {len(filtered_stations)} {args.genre} stations")
        
        if args.min_bitrate:
            min_bps = args.min_bitrate * 1000
            filtered_stations = [
                s for s in filtered_stations 
                if s.get('bitrate', 0) >= min_bps
            ]
            logger.info(f"Filtered to {len(filtered_stations)} stations with bitrate >= {args.min_bitrate}kbps")
        
        # Display stations
        print("\n" + "=" * 80)
        print(f"RADIO STATIONS ({len(filtered_stations)} found)")
        print("=" * 80)
        
        for i, station in enumerate(filtered_stations, 1):
            print(f"\n{i}. {station['name']}")
            print(f"   URL: {station['url']}")
            print(f"   Country: {station.get('country', 'Unknown')}")
            print(f"   Genre: {station.get('category', 'Unknown')}")
            
            if station.get('bitrate'):
                bitrate_kbps = station['bitrate'] / 1000
                print(f"   Bitrate: {bitrate_kbps:.0f} kbps")
            
            if station.get('language'):
                print(f"   Language: {station['language']}")
            
            if station.get('logo'):
                print(f"   Logo: {station['logo']}")
        
        print("\n" + "=" * 80)
        
        # Statistics
        print("\nSTATISTICS:")
        print(f"Total stations: {len(stations)}")
        print(f"After filters: {len(filtered_stations)}")
        
        # Country distribution
        countries = {}
        for s in stations:
            country = s.get('country', 'Unknown')
            countries[country] = countries.get(country, 0) + 1
        
        print(f"\nCountries ({len(countries)}):")
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {country}: {count}")
        
        # Genre distribution
        genres = {}
        for s in stations:
            genre = s.get('category', 'Unknown')
            genres[genre] = genres.get(genre, 0) + 1
        
        print(f"\nGenres ({len(genres)}):")
        for genre, count in sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {genre}: {count}")
        
        # Bitrate distribution
        bitrates = [s.get('bitrate', 0) for s in stations if s.get('bitrate')]
        if bitrates:
            avg_bitrate = sum(bitrates) / len(bitrates)
            max_bitrate = max(bitrates)
            min_bitrate = min(bitrates)
            print(f"\nBitrates:")
            print(f"  Average: {avg_bitrate/1000:.0f} kbps")
            print(f"  Range: {min_bitrate/1000:.0f} - {max_bitrate/1000:.0f} kbps")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
