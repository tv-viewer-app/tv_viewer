#!/usr/bin/env python3
"""Supabase Channel Health Scanner

Scans all channels from channels.json and uploads health status to Supabase.
Enables smart startup scanning for all clients by sharing channel validation data.

Usage:
    python scripts/supabase_health_scanner.py
"""

import asyncio
import aiohttp
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class SupabaseHealthScanner:
    def __init__(self):
        self.supabase_url = config.SUPABASE_URL
        self.supabase_key = config.SUPABASE_ANON_KEY
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates'
        }
        self.channels_file = config.CHANNELS_FILE
        self.batch_size = 75  # Batch uploads for efficiency
        self.max_concurrent = 100  # Concurrent stream tests
        self.timeout = 10  # Timeout per stream test
        self.progress_interval = 500  # Print progress every N channels
        
        self.total_scanned = 0
        self.total_working = 0
        self.total_failed = 0
        self.total_uploaded = 0
        self.start_time = None

    def compute_url_hash(self, url: str) -> str:
        """Compute SHA-256 hash of URL (matches Supabase url_hash column)."""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    async def test_channel(self, session: aiohttp.ClientSession, channel: dict) -> dict:
        """Test a single channel URL and return status result."""
        url = channel.get('url', '')
        url_hash = self.compute_url_hash(url)
        
        start_time = time.time()
        status = "failed"
        response_time_ms = None
        
        try:
            # Try HEAD request first (lighter)
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=self.timeout), 
                                   allow_redirects=True) as response:
                if response.status in (200, 301, 302, 307, 308):
                    status = "working"
                    response_time_ms = int((time.time() - start_time) * 1000)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            # HEAD failed, try GET
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout),
                                      allow_redirects=True) as response:
                    if response.status in (200, 301, 302, 307, 308):
                        status = "working"
                        response_time_ms = int((time.time() - start_time) * 1000)
            except:
                pass  # Already set to failed
        except Exception:
            pass  # Any other error, mark as failed
        
        return {
            'url_hash': url_hash,
            'status': status,
            'last_checked': datetime.now(timezone.utc).isoformat(),
            'response_time_ms': response_time_ms
        }

    async def upload_batch(self, session: aiohttp.ClientSession, batch: list, retry: bool = True) -> bool:
        """Upload a batch of results to Supabase."""
        endpoint = f"{self.supabase_url}/rest/v1/channel_status"
        
        try:
            async with session.post(endpoint, json=batch, headers=self.headers,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status in (200, 201, 204):
                    self.total_uploaded += len(batch)
                    return True
                elif response.status == 429:
                    # Rate limited
                    if retry:
                        await asyncio.sleep(5)  # Exponential backoff
                        return await self.upload_batch(session, batch, retry=False)
                    return False
                else:
                    text = await response.text()
                    print(f"  ⚠️  Upload failed with status {response.status}: {text[:200]}")
                    return False
        except Exception as e:
            print(f"  ⚠️  Upload error: {str(e)[:200]}")
            if retry:
                await asyncio.sleep(2)
                return await self.upload_batch(session, batch, retry=False)
            return False

    async def scan_and_upload(self):
        """Main scanning and upload logic."""
        # Load channels
        print(f"📂 Loading channels from {self.channels_file}...")
        with open(self.channels_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            channels = data.get('channels', [])
        
        print(f"✓ Loaded {len(channels)} channels\n")
        
        if not channels:
            print("❌ No channels found in channels.json")
            return
        
        self.start_time = time.time()
        
        # Security: SSL verification enabled (default) — do not set ssl=False
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            results_batch = []
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def test_with_semaphore(channel):
                async with semaphore:
                    result = await self.test_channel(session, channel)
                    self.total_scanned += 1
                    if result['status'] == 'working':
                        self.total_working += 1
                    else:
                        self.total_failed += 1
                    
                    # Print progress
                    if self.total_scanned % self.progress_interval == 0:
                        elapsed = time.time() - self.start_time
                        rate = self.total_scanned / elapsed if elapsed > 0 else 0
                        print(f"Progress: {self.total_scanned}/{len(channels)} channels | "
                              f"Working: {self.total_working} | Failed: {self.total_failed} | "
                              f"Rate: {rate:.1f} ch/s | Uploaded: {self.total_uploaded}")
                    
                    return result
            
            print("🔍 Starting channel health scan...\n")
            
            # Process channels in chunks to manage memory
            chunk_size = 1000
            for chunk_start in range(0, len(channels), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(channels))
                chunk = channels[chunk_start:chunk_end]
                
                # Test all channels in this chunk concurrently
                tasks = [test_with_semaphore(ch) for ch in chunk]
                results = await asyncio.gather(*tasks)
                
                # Batch upload results
                for result in results:
                    results_batch.append(result)
                    
                    if len(results_batch) >= self.batch_size:
                        success = await self.upload_batch(session, results_batch)
                        if not success:
                            print(f"  ⚠️  Batch upload failed, continuing...")
                        results_batch = []
            
            # Upload remaining results
            if results_batch:
                success = await self.upload_batch(session, results_batch)
                if not success:
                    print(f"  ⚠️  Final batch upload failed")
        
        # Final stats
        elapsed = time.time() - self.start_time
        print(f"\n{'='*70}")
        print(f"✓ Scan complete!")
        print(f"{'='*70}")
        print(f"Total channels scanned: {self.total_scanned}")
        print(f"Working channels:       {self.total_working} ({self.total_working*100//self.total_scanned if self.total_scanned else 0}%)")
        print(f"Failed channels:        {self.total_failed} ({self.total_failed*100//self.total_scanned if self.total_scanned else 0}%)")
        print(f"Uploaded to Supabase:   {self.total_uploaded}")
        print(f"Total time:             {elapsed:.1f}s ({self.total_scanned/elapsed:.1f} channels/sec)")
        print(f"{'='*70}")


def main():
    """Entry point."""
    print("\n" + "="*70)
    print("  Supabase Channel Health Scanner")
    print("="*70 + "\n")
    
    scanner = SupabaseHealthScanner()
    
    try:
        asyncio.run(scanner.scan_and_upload())
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
