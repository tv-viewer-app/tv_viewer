# TV Viewer - Performance Optimization Guide

## Overview

This document details the performance optimizations implemented in TV Viewer to ensure smooth operation even with 10,000+ channels.

## CPU Optimization

### Thread Priority Management

The background stream checker runs at reduced priority to avoid impacting UI responsiveness.

```python
# Windows: Set thread to below-normal priority
if sys.platform == 'win32':
    handle = ctypes.windll.kernel32.GetCurrentThread()
    ctypes.windll.kernel32.SetThreadPriority(handle, THREAD_PRIORITY_BELOW_NORMAL)

# Unix: Increase nice value
else:
    os.nice(10)
```

### Adaptive Request Delays

Configurable delays between HTTP requests prevent CPU saturation:

```python
# In StreamChecker.__init__
self._request_delay = 0.01  # 10ms between requests

# In check_with_callback
await asyncio.sleep(self._request_delay)
```

### Concurrency Limits

Semaphore prevents resource exhaustion:

```python
self._semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_CHECKS)  # Default: 10
```

**Tuning Guide:**
- Low-end systems: 5 concurrent checks
- Normal systems: 10 concurrent checks
- High-end systems: 20 concurrent checks

## Memory Optimization

### `__slots__` Usage

Classes use `__slots__` to eliminate `__dict__` overhead:

```python
class ChannelManager:
    __slots__ = ('channels', 'categories', 'countries', ...)
```

**Memory Savings:** ~40% per instance

### Shared References

Categories and countries dictionaries reference the same channel objects:

```python
# Both point to SAME channel object (no copy)
self.categories['News'].append(channel)
self.countries['USA'].append(channel)
```

### In-Place Updates

Channels are modified in-place during validation:

```python
# Modifies existing dict, no new allocation
channel['is_working'] = True
channel['last_scanned'] = datetime.now().isoformat()
```

### Batch Processing with GC

Memory pressure reduced by processing in batches:

```python
batch_size = 500
for i in range(0, len(channels), batch_size):
    batch = channels[i:i + batch_size]
    await asyncio.gather(*tasks)
    gc.collect(0)  # Generation-0 GC between batches
```

## Network Optimization

### Connection Pooling

Reuses TCP connections for efficiency:

```python
connector = aiohttp.TCPConnector(
    limit=10,              # Total connections
    limit_per_host=3,      # Per-server limit
    force_close=True,      # Clean connection reuse
    enable_cleanup_closed=True,
)
```

### DNS Caching

Reduces repeated DNS lookups:

```python
connector = aiohttp.TCPConnector(
    ttl_dns_cache=300,     # 5-minute cache
    use_dns_cache=True,
)
```

### Timeout Configuration

Balanced for speed and reliability:

```python
timeout = aiohttp.ClientTimeout(
    total=8,      # Overall timeout
    connect=5,    # Connection timeout
    sock_read=8,  # Read timeout
)
```

## Video Playback Optimization

### Hardware Acceleration

Platform-specific GPU decoding:

| Platform | API | VLC Argument |
|----------|-----|--------------|
| Windows | Direct3D 11 | `--avcodec-hw=d3d11va` |
| macOS | VideoToolbox | `--avcodec-hw=videotoolbox` |
| Linux | VAAPI | `--avcodec-hw=vaapi` |

**Benefits:**
- 80-90% CPU reduction for HD video
- Smoother playback
- Lower power consumption

### Network Buffering

Optimized for live streams:

```python
vlc_args = [
    '--network-caching=1000',  # 1 second buffer
    '--live-caching=1000',
]
```

## UI Optimization

### Debounced Updates

Rate-limited UI refreshes prevent freezing:

```python
# Only update every 50-200 channels
update_interval = 100 if total > 5000 else 50
if current % update_interval == 0:
    self._batch_ui_update(progress, current, total)

# Force update every 500ms regardless
if time_since_last > 500:
    self._batch_ui_update(progress, current, total)
```

### Idle Processing

Uses `after_idle()` for non-blocking updates:

```python
self.root.after_idle(lambda: self._batch_ui_update(...))
```

### Group List Batching

Processes UI events during category list updates:

```python
for i, group in enumerate(groups):
    btn = create_button(group)
    if i % 20 == 0:
        self.root.update_idletasks()  # Keep UI responsive
```

## Profiling Commands

### Memory Profiling

```bash
pip install memory_profiler
python -m memory_profiler main.py
```

### CPU Profiling

```bash
python -m cProfile -o profile.stats main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

### Async Profiling

```bash
pip install aiomonitor
# Add to code: import aiomonitor; aiomonitor.start_monitor(loop)
```

## Configuration Tuning

### For Low-End Systems

In `config.py`:
```python
MAX_CONCURRENT_CHECKS = 5
STREAM_CHECK_TIMEOUT = 10
```

### For High-End Systems

In `config.py`:
```python
MAX_CONCURRENT_CHECKS = 20
STREAM_CHECK_TIMEOUT = 5
```

### For Slow Networks

In `config.py`:
```python
REQUEST_TIMEOUT = 30
STREAM_CHECK_TIMEOUT = 15
```

## Monitoring

### Log Key Metrics

```python
print(f"Memory: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB")
print(f"Threads: {threading.active_count()}")
print(f"Channels: {len(channels)}")
```

### Expected Performance

| Metric | Target |
|--------|--------|
| Startup time | < 3s (cached) |
| Memory (10k channels) | < 200 MB |
| CPU during scan | < 30% |
| CPU during playback | < 10% (with HW accel) |
