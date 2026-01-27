# TV Viewer - Support Engineering Guide

**Document Version:** 1.0  
**Last Updated:** 2025-01-20  
**Application Version:** 1.0.0  
**Classification:** Support Team Internal

---

## 1. Supportability Assessment

### 1.1 Overall Supportability Score: **NEEDS WORK**

| Category | Score | Rating |
|----------|-------|--------|
| Documentation | 7/10 | Good |
| Error Messages | 6/10 | Needs Work |
| Logging & Diagnostics | 4/10 | Needs Work |
| Self-Service Capability | 5/10 | Needs Work |
| Configuration Options | 7/10 | Good |
| Recovery Mechanisms | 6/10 | Acceptable |
| **Overall** | **5.8/10** | **NEEDS WORK** |

### 1.2 Justification

**Strengths:**
- Comprehensive technical documentation (README, ARCHITECTURE, PERFORMANCE, API docs)
- Well-structured codebase with clear separation of concerns
- Good error handling in core modules (try/catch, graceful failures)
- Configuration options in `config.py` for tuning
- Thread-safe operations with proper resource cleanup
- Security-conscious design with URL validation

**Weaknesses:**
- **No structured logging system** - Uses `print()` statements only
- **Limited user-facing error messages** - Technical errors shown to users
- **No telemetry or crash reporting** - Blind to production issues
- **No log file persistence** - Logs lost when app closes
- **Missing health check endpoints** - Cannot verify app state remotely
- **No diagnostic mode** - Hard to collect debug info

### 1.3 Priority Improvements for Supportability

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| P0 | Add structured logging with file output | Medium | High |
| P0 | Improve user-facing error messages | Low | High |
| P1 | Add diagnostic/debug mode | Medium | Medium |
| P1 | Create in-app "Report Issue" feature | Medium | Medium |
| P2 | Add telemetry opt-in | High | Medium |
| P2 | Implement health check status | Low | Low |

---

## 2. Support Burden Estimate

### 2.1 Expected Ticket Volume (per 1,000 users/month)

| Issue Category | Estimated Tickets | % of Total |
|----------------|-------------------|------------|
| VLC Installation/Detection | 35-50 | 30% |
| Channels Not Playing | 25-35 | 22% |
| No Channels Loading | 15-25 | 17% |
| Performance Issues | 10-15 | 10% |
| UI/Display Issues | 8-12 | 8% |
| Network/Connectivity | 8-12 | 8% |
| Feature Requests | 5-10 | 5% |
| **Total** | **106-159** | 100% |

### 2.2 Ticket Distribution by Tier

| Tier | % of Tickets | Resolution Time | Description |
|------|--------------|-----------------|-------------|
| L1 (Self-Service) | 40% | < 5 min | FAQ, KB articles, in-app help |
| L1 (Agent) | 35% | < 15 min | Basic troubleshooting, known issues |
| L2 (Technical) | 20% | < 1 hour | Configuration, debug logs, complex issues |
| L3 (Engineering) | 5% | 1-5 days | Bugs, crashes, code-level issues |

### 2.3 Staffing Recommendations

| User Base | L1 FTEs | L2 FTEs | L3 Coverage |
|-----------|---------|---------|-------------|
| 1,000 | 0.1 (part-time) | 0 | Engineering on-call |
| 10,000 | 0.5 | 0.25 | 1 engineer assigned |
| 50,000 | 2 | 0.5 | 2 engineers assigned |
| 100,000+ | 4 | 1 | Dedicated team |

---

## 3. Common Issues & Solutions (Troubleshooting Playbook)

### 3.1 VLC Not Found / Not Working

**Symptoms:**
- "VLC is not available" error in player window
- Black screen when playing channels
- "Warning: python-vlc not installed" in console

**Root Causes:**
1. VLC Media Player not installed
2. VLC architecture mismatch (32-bit vs 64-bit)
3. python-vlc package not installed
4. VLC not in system PATH

**Diagnostic Steps:**
```
Step 1: Verify VLC installation
  Windows: Check "C:\Program Files\VideoLAN\VLC\vlc.exe" exists
  Linux: Run "which vlc" in terminal
  macOS: Check "/Applications/VLC.app" exists

Step 2: Check architecture match
  - 64-bit Python requires 64-bit VLC
  - Run "python -c 'import struct; print(struct.calcsize('P')*8)'" to check Python bits

Step 3: Verify python-vlc
  - Run "pip show python-vlc"
  - If missing: "pip install python-vlc"

Step 4: Check VLC path
  - Windows: VLC should be in Program Files
  - Add VLC to PATH if using custom location
```

**Resolution Scripts:**
```powershell
# Windows - Check VLC and reinstall python-vlc
$vlcPath = "C:\Program Files\VideoLAN\VLC\vlc.exe"
if (Test-Path $vlcPath) {
    Write-Host "VLC found at $vlcPath"
    pip uninstall python-vlc -y
    pip install python-vlc
} else {
    Write-Host "VLC NOT FOUND - Please install from videolan.org"
}
```

```bash
# Linux/macOS - Check VLC
which vlc || echo "VLC not installed - run: sudo apt install vlc"
pip3 show python-vlc || pip3 install python-vlc
```

**Escalation Criteria:**
- VLC installed correctly but still fails → L2
- Error message shows VLC version conflict → L2
- Crashes on specific OS version → L3

---

### 3.2 No Channels Loading

**Symptoms:**
- Empty category list
- "Starting..." status never changes
- "0/0" shown in all categories
- Error messages about fetching repositories

**Root Causes:**
1. No internet connection
2. Repository URLs blocked/unavailable
3. Firewall blocking IPTV repositories
4. Corrupted cache file
5. DNS resolution failure

**Diagnostic Steps:**
```
Step 1: Check internet connectivity
  - ping google.com
  - Check if other apps can access internet

Step 2: Test repository access
  - Browser: Open https://iptv-org.github.io/iptv/index.m3u
  - Should see M3U playlist content

Step 3: Check for proxy/VPN issues
  - Disable VPN temporarily
  - Check corporate proxy settings

Step 4: Clear cache
  - Delete channels.json in app directory
  - Restart application

Step 5: Check firewall
  - Allow python.exe through firewall
  - Allow VLC through firewall
```

**Resolution Steps:**
1. **Clear cache and restart:**
   ```
   1. Close TV Viewer completely
   2. Navigate to TV Viewer installation folder
   3. Delete "channels.json" file
   4. Restart TV Viewer
   ```

2. **Use File > Refresh Channels** menu option

3. **Check repository configuration:**
   - Open `channels_config.json`
   - Verify repositories array has valid URLs
   - Try different repository URL

**Escalation Criteria:**
- Repositories accessible in browser but not in app → L2
- Partial channel loading only → L2
- Error in console mentioning SSL/certificate → L2

---

### 3.3 Channels Not Playing

**Symptoms:**
- Channel selected but video stays black
- "Working" channels don't play
- Audio but no video (or vice versa)
- Buffering indefinitely

**Root Causes:**
1. Stream URL no longer valid
2. Geo-restricted content
3. Stream format not supported
4. Codec missing
5. Network timeout

**Diagnostic Steps:**
```
Step 1: Test with multiple channels
  - If ALL channels fail → VLC/network issue
  - If SOME channels fail → Stream-specific issue

Step 2: Check stream status
  - Look at "Status" column in channel list
  - Working = green, Failed = red, Checking = yellow

Step 3: Test stream externally
  - Copy channel URL (visible in preview panel)
  - Open URL directly in VLC player

Step 4: Check VLC console output
  - Watch console for error messages during playback

Step 5: Test different stream protocol
  - Try channels with different URL types (http vs https)
```

**Resolution Steps:**
1. **Try "Open in VLC" button** - Tests if stream works in standalone VLC
2. **Wait for stream validation** - Status shows "Checking" during scan
3. **Filter to "Working Only"** - View menu → Show Working Only
4. **Refresh channels** - File menu → Refresh Channels

**Known Limitations:**
- Some streams are geo-restricted (country-specific)
- Live streams may be intermittently available
- Some HLS streams require specific VLC version

**Escalation Criteria:**
- All channels fail including known-working test streams → L2
- Specific stream types always fail (e.g., all RTMP) → L2
- Works in external VLC but not embedded → L3

---

### 3.4 Network Errors

**Symptoms:**
- "Timeout fetching" errors in console
- Channels marked as not working immediately
- Slow scanning progress
- "Connection error" messages

**Root Causes:**
1. Slow internet connection
2. Corporate proxy blocking
3. Firewall rules
4. DNS issues
5. Repository rate limiting

**Diagnostic Steps:**
```
Step 1: Test network speed
  - Run speed test
  - Minimum recommended: 5 Mbps download

Step 2: Check DNS resolution
  - nslookup iptv-org.github.io
  - Try using Google DNS (8.8.8.8) or Cloudflare (1.1.1.1)

Step 3: Check for proxy
  - View system proxy settings
  - Check environment variables: HTTP_PROXY, HTTPS_PROXY

Step 4: Test connectivity
  - curl -I https://iptv-org.github.io/iptv/index.m3u
  - Expected: HTTP 200 response
```

**Configuration Tuning:**
Edit `config.py` for slow networks:
```python
# Increase timeouts for slow connections
REQUEST_TIMEOUT = 30       # Default: 20
STREAM_CHECK_TIMEOUT = 15  # Default: 8

# Reduce concurrent checks to lower bandwidth
MAX_CONCURRENT_CHECKS = 5  # Default: 10
```

**Escalation Criteria:**
- Network tests pass but app still fails → L2
- Consistent timeout patterns → L2
- SSL/certificate errors → L2

---

### 3.5 UI Issues

**Symptoms:**
- Window not displaying correctly
- Buttons not responding
- Flickering display
- Incorrect scaling/DPI
- Dark theme not applied

**Root Causes:**
1. Display scaling issues (HiDPI)
2. Graphics driver problems
3. CustomTkinter rendering issues
4. Multiple monitor setup
5. OS theme conflicts

**Diagnostic Steps:**
```
Step 1: Check display settings
  - Note screen resolution and scaling %
  - Try 100% scaling

Step 2: Update graphics drivers
  - Windows: Check Device Manager > Display adapters
  - Update to latest drivers

Step 3: Test with different themes
  - Check if OS is set to dark/light mode
  - App uses "dark" mode by default

Step 4: Check Python version
  - "python --version"
  - Requires Python 3.8+
```

**Common Fixes:**
1. **Windows scaling fix:**
   - Right-click python.exe → Properties → Compatibility
   - Check "Override high DPI scaling behavior"
   - Set to "Application"

2. **Reset window position:**
   - Delete any window position cache
   - Restart app

3. **Update CustomTkinter:**
   ```
   pip install --upgrade customtkinter
   ```

**Escalation Criteria:**
- UI crash with traceback → L3
- Consistent issue on specific OS version → L3
- Accessibility-related issues → L2

---

### 3.6 Performance Issues

**Symptoms:**
- High CPU usage during scanning
- Slow UI response
- Memory usage growing over time
- App freezing during channel load

**Root Causes:**
1. Too many concurrent checks
2. Large number of channels
3. Memory leak (long sessions)
4. Slow system hardware
5. Background processes competing

**Diagnostic Steps:**
```
Step 1: Check resource usage
  - Open Task Manager (Windows) / Activity Monitor (macOS)
  - Note CPU % and Memory for python.exe/TV Viewer

Step 2: Check channel count
  - More than 10,000 channels increases memory/CPU

Step 3: Monitor during scan
  - CPU should spike during scan, then drop
  - If CPU stays high after scan → Issue

Step 4: Check scan settings
  - Review MAX_CONCURRENT_CHECKS in config.py
```

**Performance Tuning:**
Edit `config.py`:
```python
# For low-end systems
MAX_CONCURRENT_CHECKS = 5   # Reduce from default 10
STREAM_CHECK_TIMEOUT = 10   # Increase from default 8

# Expected results:
# - CPU usage during scan: < 30%
# - Memory (10k channels): < 200 MB
# - Startup time (cached): < 3 seconds
```

**Quick Fixes:**
1. **Reduce scan concurrency** - Edit `config.py`, set MAX_CONCURRENT_CHECKS = 5
2. **Restart app** - Clears memory, resets state
3. **Wait for scan completion** - Performance normalizes after initial scan

**Escalation Criteria:**
- Memory usage exceeds 500MB → L2
- CPU stays at 100% after scan → L2
- App crashes with memory error → L3

---

## 4. Knowledge Base Articles

### KB001: Installing VLC for TV Viewer

**Title:** How to Install VLC Media Player for TV Viewer

**Applies To:** Windows, macOS, Linux

**Solution:**

**Windows:**
1. Download VLC from https://www.videolan.org/vlc/
2. **Important:** Choose 64-bit version if using 64-bit Python
3. Run installer with default options
4. Install to default location: `C:\Program Files\VideoLAN\VLC`
5. Restart TV Viewer

**macOS:**
1. Download VLC from https://www.videolan.org/vlc/
2. Open the DMG file
3. Drag VLC to Applications folder
4. Restart TV Viewer

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install vlc
pip3 install python-vlc
```

**Verification:**
Open terminal/command prompt and run:
```bash
pip show python-vlc
```
Should show package version 3.0+

---

### KB002: Clearing Channel Cache

**Title:** How to Clear and Refresh Channel Data

**Applies To:** All platforms

**Problem:** Outdated channel data, corrupted cache

**Solution:**
1. Close TV Viewer completely
2. Navigate to TV Viewer folder
3. Delete these files (if they exist):
   - `channels.json`
   - `channels.json.tmp`
4. Restart TV Viewer
5. Wait for channels to reload (may take 2-5 minutes)

**Alternative:** Use menu: File → Refresh Channels

---

### KB003: Configuring for Slow Networks

**Title:** Optimizing TV Viewer for Slow Internet Connections

**Problem:** Timeouts, channels marked as not working incorrectly

**Solution:**
1. Open `config.py` in text editor
2. Modify these settings:
   ```python
   REQUEST_TIMEOUT = 30        # Increase from 20
   STREAM_CHECK_TIMEOUT = 15   # Increase from 8
   MAX_CONCURRENT_CHECKS = 5   # Decrease from 10
   ```
3. Save file and restart TV Viewer

---

### KB004: Troubleshooting Geo-Restricted Channels

**Title:** Why Some Channels Show as Working but Won't Play

**Problem:** Channel validated as working but video won't load

**Explanation:**
- IPTV streams may be restricted by geographic location
- Validation check succeeds (URL responds) but content is blocked
- This is by design from the stream provider

**Solutions:**
1. Filter by country matching your location
2. Look for "International" category
3. Some channels work with VPN (not officially supported)

---

### KB005: Running TV Viewer on Low-End Systems

**Title:** Performance Settings for Older Computers

**Problem:** High CPU, slow UI, freezing

**Minimum Requirements:**
- 2 GB RAM
- Dual-core CPU
- Python 3.8+

**Solution:**
Edit `config.py`:
```python
MAX_CONCURRENT_CHECKS = 3    # Minimal concurrent checks
STREAM_CHECK_TIMEOUT = 12    # More time per check
```

Filter to specific category (don't load "All Channels")

---

### KB006: Using Custom Channel Sources

**Title:** Adding Custom IPTV Repositories or Channels

**Solution:**
1. Create/edit `channels_config.json` in TV Viewer folder
2. Add your repositories or custom channels:
   ```json
   {
     "repositories": [
       "https://iptv-org.github.io/iptv/index.m3u",
       "https://your-custom-playlist.m3u"
     ],
     "custom_channels": [
       {
         "name": "My Local Stream",
         "url": "http://192.168.1.100:8080/stream",
         "category": "Custom"
       }
     ]
   }
   ```
3. Restart TV Viewer

---

### KB007: Keyboard Shortcuts

**Title:** TV Viewer Keyboard Shortcuts Reference

**Player Window:**
| Shortcut | Action |
|----------|--------|
| Space | Play/Pause |
| F | Toggle Fullscreen |
| M | Toggle Mute |
| Escape | Exit Fullscreen |

**Main Window:**
| Shortcut | Action |
|----------|--------|
| Enter | Play selected channel |
| Double-click | Play channel |

---

### KB008: Understanding Channel Status

**Title:** What Do Channel Status Colors Mean?

| Status | Color | Meaning |
|--------|-------|---------|
| Working | Green | Stream validated and accessible |
| Failed | Red | Stream did not respond or returned error |
| Checking | Yellow | Currently being validated |
| Pending | Gray | Not yet checked |

**Note:** "Working" status means the URL responded - it doesn't guarantee playback will work (geo-restrictions may apply)

---

### KB009: Firewall Configuration

**Title:** Configuring Firewall for TV Viewer

**Required Access:**
- Outbound HTTP (port 80)
- Outbound HTTPS (port 443)
- Outbound RTMP (port 1935) - for some streams
- Outbound UDP (various ports) - for video streams

**Windows Firewall:**
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Find `python.exe` or `TV Viewer` and allow both Private and Public

**Corporate Firewalls:**
May need to allowlist:
- `*.github.io`
- `*.githubusercontent.com`
- Various IPTV stream hosts

---

### KB010: Reporting Bugs

**Title:** How to Report Issues with TV Viewer

**Information to Collect:**
1. Operating System and version
2. Python version (`python --version`)
3. VLC version (Help > About in VLC)
4. Steps to reproduce the issue
5. Console output (copy text from terminal)
6. Screenshot if UI issue

**How to Get Console Output:**
- Run TV Viewer from terminal: `python main.py`
- Copy all text output when error occurs

**Report To:** [Support contact or GitHub Issues URL]

---

## 5. Diagnostic Guide

### 5.1 Collecting System Information

```powershell
# Windows - Run in PowerShell
Write-Host "=== System Info ===" 
[System.Environment]::OSVersion
Write-Host "`n=== Python Version ==="
python --version
Write-Host "`n=== Installed Packages ==="
pip list | Select-String -Pattern "vlc|customtkinter|aiohttp|pillow"
Write-Host "`n=== VLC Location ==="
Get-Command vlc -ErrorAction SilentlyContinue | Select-Object Source
Write-Host "`n=== TV Viewer Files ==="
Get-ChildItem *.json, config.py | Select-Object Name, Length, LastWriteTime
```

```bash
# Linux/macOS - Run in Terminal
echo "=== System Info ==="
uname -a
echo -e "\n=== Python Version ==="
python3 --version
echo -e "\n=== Installed Packages ==="
pip3 list | grep -E "vlc|customtkinter|aiohttp|pillow"
echo -e "\n=== VLC Location ==="
which vlc
echo -e "\n=== TV Viewer Files ==="
ls -la *.json config.py 2>/dev/null
```

### 5.2 Running in Debug Mode

Currently, there's no built-in debug mode. Use this workaround:

```bash
# Capture all console output to file
python main.py 2>&1 | tee tv_viewer_debug.log
```

### 5.3 Key Log Messages to Look For

| Message | Meaning | Severity |
|---------|---------|----------|
| "VLC library found" | VLC successfully loaded | Info |
| "Warning: python-vlc not installed" | VLC binding missing | Critical |
| "Loaded X channels from cache" | Cache loaded successfully | Info |
| "Timeout fetching URL" | Network timeout | Warning |
| "Error fetching URL: X" | Network/HTTP error | Warning |
| "Error in background stream check" | Scan failure | Error |
| "Failed to create VLC instance" | VLC initialization failed | Critical |

### 5.4 Reproducing Issues

**For Channel Loading Issues:**
1. Delete `channels.json`
2. Run `python main.py` from terminal
3. Capture all console output
4. Note time to first channel appears

**For Playback Issues:**
1. Note exact channel name and URL
2. Test URL in standalone VLC
3. Compare results

**For Performance Issues:**
1. Note Task Manager CPU/Memory before starting
2. Start TV Viewer, wait for scan
3. Note CPU/Memory during and after scan
4. Record total channels loaded

### 5.5 Health Check Script

```python
#!/usr/bin/env python3
"""TV Viewer Health Check Script"""
import sys
import os

def check_python():
    print(f"Python: {sys.version}")
    return sys.version_info >= (3, 8)

def check_vlc():
    try:
        import vlc
        print(f"python-vlc: {vlc.__version__ if hasattr(vlc, '__version__') else 'installed'}")
        return True
    except ImportError:
        print("python-vlc: NOT INSTALLED")
        return False

def check_dependencies():
    deps = ['customtkinter', 'aiohttp', 'PIL']
    results = []
    for dep in deps:
        try:
            __import__(dep)
            print(f"{dep}: OK")
            results.append(True)
        except ImportError:
            print(f"{dep}: MISSING")
            results.append(False)
    return all(results)

def check_cache():
    cache_file = "channels.json"
    if os.path.exists(cache_file):
        size = os.path.getsize(cache_file)
        print(f"Cache: {size:,} bytes")
        return size > 0
    print("Cache: NOT FOUND")
    return True  # Not critical

def main():
    print("=== TV Viewer Health Check ===\n")
    checks = [
        ("Python 3.8+", check_python()),
        ("VLC Library", check_vlc()),
        ("Dependencies", check_dependencies()),
        ("Cache File", check_cache()),
    ]
    print("\n=== Results ===")
    all_pass = True
    for name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
        all_pass = all_pass and result
    
    print(f"\nOverall: {'HEALTHY' if all_pass else 'ISSUES DETECTED'}")
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 6. Escalation Paths

### 6.1 Support Tier Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        L1 - Front Line                          │
│  Scope: Known issues, KB articles, basic troubleshooting       │
│  Tools: This guide, KB articles, FAQ                           │
│  SLA: Response < 4 hours, Resolution < 24 hours                │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Escalate if:
                    - Issue not in playbook
                    - Requires config changes
                    - Customer requests technical help
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     L2 - Technical Support                      │
│  Scope: Configuration, log analysis, advanced troubleshooting  │
│  Tools: Debug mode, system diagnostics, config editing         │
│  SLA: Response < 2 hours, Resolution < 48 hours                │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Escalate if:
                    - Suspected bug
                    - Requires code changes
                    - Crash/data loss
                    - Security concern
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     L3 - Engineering                            │
│  Scope: Bug fixes, code investigation, architecture issues     │
│  Tools: Source code, debugger, profiler                        │
│  SLA: Triage < 24 hours, Fix varies by severity                │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Escalation Criteria

**L1 → L2:**
- Issue not covered in troubleshooting playbook
- Requires editing config files
- Involves log analysis beyond basic messages
- Customer requests technical deep-dive
- Issue persists after standard troubleshooting

**L2 → L3:**
- Confirmed bug (reproducible, unexpected behavior)
- Application crash with traceback
- Data corruption or loss
- Security vulnerability suspected
- Performance issue with no config workaround
- Feature request requiring code changes

### 6.3 Escalation Template

```
TICKET ID: [Number]
SEVERITY: [Critical/High/Medium/Low]
ESCALATION REASON: [Bug/Performance/Security/Feature/Other]

CUSTOMER IMPACT:
- Users affected: [Number/All]
- Workaround available: [Yes/No]

ISSUE SUMMARY:
[2-3 sentences describing the problem]

REPRODUCTION STEPS:
1. [Step 1]
2. [Step 2]
3. [Expected result]
4. [Actual result]

TROUBLESHOOTING DONE:
- [List all steps attempted]
- [Include any diagnostic output]

ENVIRONMENT:
- OS: [Windows 10/11, macOS version, Linux distro]
- Python: [version]
- VLC: [version]
- App Version: [1.0.0]

ATTACHMENTS:
- [ ] Console/debug log
- [ ] Screenshot
- [ ] config.py (sanitized)
- [ ] channels.json sample
```

---

## 7. Training Plan

### 7.1 L1 Support Training (4 hours)

**Module 1: Product Overview (1 hour)**
- Application purpose and features
- Target user base
- Technology stack overview
- Installation walkthrough

**Module 2: Common Issues (2 hours)**
- VLC installation scenarios (hands-on)
- Network troubleshooting basics
- Using the troubleshooting playbook
- KB article navigation

**Module 3: Tools & Processes (1 hour)**
- Collecting system info script
- Reading console output
- Escalation process
- Ticket documentation

**Assessment:** Resolve 5 test scenarios from playbook

### 7.2 L2 Support Training (8 hours)

**Module 1: Architecture Deep Dive (2 hours)**
- Review ARCHITECTURE.md
- Threading model explanation
- Data flow walkthrough
- Configuration options

**Module 2: Advanced Diagnostics (3 hours)**
- Running debug mode
- Log analysis patterns
- Performance profiling basics
- Network debugging (curl, ping, traceroute)

**Module 3: Configuration Mastery (2 hours)**
- All config.py options
- channels_config.json structure
- Performance tuning scenarios
- Security considerations

**Module 4: Escalation Management (1 hour)**
- Writing effective bug reports
- Communicating with engineering
- Severity classification

**Assessment:** Debug and document 3 complex scenarios

### 7.3 Ongoing Training

- Monthly: New KB articles review
- Quarterly: Product update briefing
- As needed: Post-incident reviews

---

## 8. Monitoring Recommendations

### 8.1 Key Metrics to Track (Future Implementation)

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| App startup time | < 3s | > 10s |
| Channel load success rate | > 95% | < 80% |
| Stream validation rate | > 70% working | < 50% |
| Memory usage | < 200MB | > 400MB |
| CPU during playback | < 10% | > 50% |
| Crash rate | < 0.1% sessions | > 1% |

### 8.2 Recommended Telemetry Events

**Opt-in Only (Privacy-Respecting):**
```
app_started: {os, python_version, vlc_available}
channels_loaded: {count, cache_hit, load_time_ms}
validation_complete: {total, working, failed, duration_s}
playback_started: {protocol_type: http|rtmp|hls}
playback_error: {error_type, has_vlc}
app_crash: {exception_type, stack_hash}
```

### 8.3 Proactive Support Indicators

**Early Warning Signs:**
- Spike in "VLC not found" errors → Update VLC installation KB
- Increase in validation failures → Check repository health
- Memory complaints increase → Review for memory leak
- Specific OS version issues → Note in KB, investigate

### 8.4 Repository Health Monitoring

Monitor these external dependencies:
- `https://iptv-org.github.io/iptv/index.m3u` - Main repository
- `https://iptv-org.github.io/iptv/index.country.m3u` - Country index

**Health Check:**
```bash
# Run periodically to verify repository availability
curl -sI https://iptv-org.github.io/iptv/index.m3u | head -1
# Expected: HTTP/2 200
```

---

## 9. Documentation Gaps

### 9.1 Missing User Documentation

| Document | Priority | Impact |
|----------|----------|--------|
| In-app help/tooltips | High | Would reduce L1 tickets by 20% |
| Video tutorial | High | Visual learners, installation help |
| FAQ page | Medium | Self-service for common questions |
| Glossary (IPTV terms) | Low | Reduces confusion |
| Localized documentation | Low | Non-English users |

### 9.2 Missing Technical Documentation

| Document | Priority | Impact |
|----------|----------|--------|
| Logging specification | High | Critical for debugging |
| Error code reference | High | Faster issue identification |
| Network requirements doc | Medium | Firewall/proxy issues |
| Troubleshooting decision tree | Medium | L1 efficiency |
| Release notes template | Low | Change communication |

### 9.3 Recommended Documentation Improvements

**README.md Additions:**
- Troubleshooting section expansion
- Minimum system requirements
- Known limitations list
- Error message reference

**New Document: TROUBLESHOOTING.md**
- Comprehensive issue guide
- Screenshot examples
- Step-by-step wizards

---

## 10. Self-Service Improvements

### 10.1 In-App Improvements

| Feature | Effort | Ticket Reduction |
|---------|--------|------------------|
| VLC setup wizard | Medium | 25-30% |
| Network diagnostic tool | Medium | 15-20% |
| "Report Issue" with auto-diagnostics | High | 10% (better quality) |
| First-run tutorial | Low | 10-15% |
| Status page for repositories | Low | 5-10% |
| Settings validation on save | Low | 5% |

### 10.2 Priority Implementation Recommendations

**P0 - Implement Immediately:**
1. **Better error messages** - Replace technical errors with actionable guidance
   ```python
   # Current
   "Warning: python-vlc not installed"
   
   # Improved
   "Video playback requires VLC Media Player.
    Please install VLC from videolan.org and restart TV Viewer.
    [Install VLC] [Help]"
   ```

2. **VLC detection with guidance** - On startup, detect VLC and show setup wizard if missing

**P1 - Implement Soon:**
3. **Network diagnostic** - Menu option to test connectivity to repositories
4. **Log file export** - "Help > Export Diagnostics" creates zip with logs and system info
5. **In-app help** - F1 key opens contextual help

**P2 - Future Improvements:**
6. **Auto-update checker** - Notify when new version available
7. **Crash reporter** - Opt-in crash reporting with stack trace
8. **Community forum** - Self-help between users

### 10.3 Error Message Improvements

| Current Message | Improved Message |
|-----------------|------------------|
| "VLC is not available" | "VLC Media Player is required for video playback. Click Help to install VLC, or click Skip to browse channels without video." |
| "Timeout fetching [URL]" | "Could not connect to channel source. Check your internet connection and try File > Refresh Channels." |
| "Error in fetch" | "Unable to load channels. This may be a temporary network issue. Try again in a few minutes." |
| Console-only errors | In-app notification bar with user-friendly messages |

### 10.4 Self-Service Feature Specifications

**VLC Setup Wizard:**
```
┌────────────────────────────────────────────┐
│   📺 TV Viewer Setup                        │
├────────────────────────────────────────────┤
│                                            │
│   VLC Media Player is required.            │
│                                            │
│   Status: ❌ Not detected                  │
│                                            │
│   [Download VLC]  [I've installed VLC]     │
│                                            │
│   [Skip for now]  [Help]                   │
│                                            │
└────────────────────────────────────────────┘
```

**Network Diagnostic Tool:**
```
┌────────────────────────────────────────────┐
│   🔍 Network Diagnostics                   │
├────────────────────────────────────────────┤
│                                            │
│   Internet Connection:    ✅ OK            │
│   DNS Resolution:         ✅ OK            │
│   Repository Access:      ❌ Failed        │
│     → iptv-org.github.io: Timeout         │
│                                            │
│   Recommendation:                          │
│   Check firewall settings or try a VPN.   │
│                                            │
│   [Copy Report]  [Close]                   │
│                                            │
└────────────────────────────────────────────┘
```

---

## Appendix A: Quick Reference Card

### Common Commands

| Task | Command/Action |
|------|----------------|
| Run TV Viewer | `python main.py` |
| Check VLC | `pip show python-vlc` |
| Install VLC binding | `pip install python-vlc` |
| Clear cache | Delete `channels.json` |
| Refresh channels | File menu → Refresh Channels |
| Debug output | `python main.py 2>&1 \| tee debug.log` |

### Key Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `config.py` | Configuration settings |
| `channels.json` | Cached channel data |
| `channels_config.json` | User repositories & custom channels |
| `thumbnails/` | Cached channel thumbnails |

### Support Contacts

| Issue Type | Contact |
|------------|---------|
| General Support | [L1 queue/email] |
| Technical Escalation | [L2 queue/email] |
| Bug Reports | [GitHub Issues or L3 queue] |
| Security Issues | [Security contact] |

---

*Document maintained by Support Engineering. Last review: 2025-01-20*
