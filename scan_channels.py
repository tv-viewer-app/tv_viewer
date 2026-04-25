#!/usr/bin/env python3
"""
Channel validation script for TV Viewer v2.4.0
Scans all channels in channels.json and removes offline streams.
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import aiohttp


# Configuration
CHANNELS_FILE = Path(__file__).parent / "channels.json"
MAX_CONCURRENT = 100
CONNECT_TIMEOUT = 8
TOTAL_TIMEOUT = 12
PROGRESS_INTERVAL = 1000


class ChannelScanner:
    def __init__(self):
        self.total_checked = 0
        self.working_count = 0
        self.failed_count = 0
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
    async def check_channel(self, session, channel):
        """Check if a channel URL is accessible."""
        async with self.semaphore:
            url = channel.get('url', '')
            if not url:
                return False
            
            try:
                timeout = aiohttp.ClientTimeout(
                    total=TOTAL_TIMEOUT,
                    connect=CONNECT_TIMEOUT
                )
                
                # Try HEAD first, fall back to GET if needed
                async with session.head(url, timeout=timeout) as response:
                    if response.status == 200:
                        return True
                    elif response.status == 405:  # Method not allowed, try GET
                        pass
                    else:
                        # Try GET for other status codes
                        pass
                
                # Try GET request
                async with session.get(url, timeout=timeout) as response:
                    if response.status != 200:
                        return False
                    
                    # For HLS streams, check for #EXTM3U
                    if url.endswith('.m3u8') or '.m3u8' in url:
                        content = await response.text()
                        if '#EXTM3U' not in content:
                            return False
                    
                    return True
                    
            except asyncio.TimeoutError:
                return False
            except aiohttp.ClientError:
                return False
            except Exception:
                return False
    
    async def scan_channels(self, channels):
        """Scan all channels concurrently."""
        print(f"\n🔍 Starting channel validation...")
        print(f"📊 Total channels to check: {len(channels)}")
        print(f"⚡ Concurrent connections: {MAX_CONCURRENT}")
        print(f"⏱️  Timeouts: {CONNECT_TIMEOUT}s connect, {TOTAL_TIMEOUT}s total\n")
        
        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            current_timestamp = datetime.now(timezone.utc).isoformat()
            
            for idx, channel in enumerate(channels):
                task = self.process_channel(session, channel, idx, current_timestamp)
                tasks.append(task)
            
            # Process all channels
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return results
    
    async def process_channel(self, session, channel, idx, timestamp):
        """Process a single channel."""
        is_working = await self.check_channel(session, channel)
        
        # Update channel metadata
        channel['is_working'] = is_working
        channel['scan_status'] = 'scanned'
        channel['last_scanned'] = timestamp
        
        # Update counters
        self.total_checked += 1
        if is_working:
            self.working_count += 1
        else:
            self.failed_count += 1
        
        # Progress reporting
        if self.total_checked % PROGRESS_INTERVAL == 0:
            print(f"✓ Checked {self.total_checked} channels | "
                  f"Working: {self.working_count} | "
                  f"Failed: {self.failed_count}")
        
        return channel


def load_channels():
    """Load channels from JSON file."""
    print(f"📂 Loading channels from {CHANNELS_FILE}...")
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def save_channels(data):
    """Save channels to JSON file."""
    print(f"\n💾 Saving cleaned channels to {CHANNELS_FILE}...")
    with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Main entry point."""
    print("=" * 70)
    print("TV Viewer Channel Scanner v2.4.0")
    print("=" * 70)
    
    # Load existing data
    data = load_channels()
    original_count = len(data['channels'])
    
    # Run async scanner
    scanner = ChannelScanner()
    asyncio.run(scanner.scan_channels(data['channels']))
    
    # Filter out non-working channels
    print(f"\n🧹 Removing offline channels...")
    working_channels = [ch for ch in data['channels'] if ch.get('is_working', False)]
    removed_count = original_count - len(working_channels)
    
    # Update data structure
    data['channels'] = working_channels
    data['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    # Save cleaned data
    save_channels(data)
    
    # Final summary
    print("\n" + "=" * 70)
    print("📈 SCAN COMPLETE")
    print("=" * 70)
    print(f"Original channels:    {original_count:,}")
    print(f"Working channels:     {scanner.working_count:,}")
    print(f"Failed channels:      {scanner.failed_count:,}")
    print(f"Removed from list:    {removed_count:,}")
    print(f"Final channel count:  {len(working_channels):,}")
    print(f"Success rate:         {(scanner.working_count/original_count*100):.1f}%")
    print("=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
