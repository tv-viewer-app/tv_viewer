# TV Viewer - L1 Support Playbook
**Version:** 1.0  
**Last Updated:** December 2024  
**Target Audience:** Level 1 Support Agents

---

## 📋 TABLE OF CONTENTS

1. [Quick Reference](#quick-reference)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Troubleshooting Workflows](#troubleshooting-workflows)
4. [Escalation Procedures](#escalation-procedures)
5. [Canned Responses](#canned-responses)
6. [Tools & Resources](#tools--resources)

---

## 🎯 QUICK REFERENCE

### Top 10 Issues (80% of tickets)

| Issue | % of Tickets | Avg Resolution Time | First Response |
|-------|--------------|---------------------|----------------|
| Video won't play | 35% | 10 min | Ask for error code, check network |
| How to use feature | 25% | 5 min | Send help guide link |
| App crashes | 15% | 15 min | Request logs, check version |
| Slow performance | 10% | 12 min | Check device specs, clear cache |
| How to add channels | 8% | 5 min | Explain current limitation |
| External player issue | 7% | 8 min | Verify player installed |

### Quick Diagnostic Questions

**Always Ask First:**
1. What device are you using? (Make/model)
2. What Android version?
3. What exactly happened? (Step by step)
4. Any error message shown? (Get exact text or screenshot)
5. When did this start happening?

### Escalation Criteria

**Escalate to L2 if:**
- Issue persists after standard troubleshooting
- Technical error logs needed
- Potential app bug
- Requires code-level investigation
- User waited >24 hours

**Escalate to L3 if:**
- Critical app crash affecting multiple users
- Security concern
- Data loss
- Server/infrastructure issue

---

## 🔧 COMMON ISSUES & SOLUTIONS

### Issue 1: Video Won't Play (35% of tickets)

**Ticket Examples:**
- "Video doesn't start"
- "Stuck on loading"
- "Black screen when playing"
- "Error message appears"

**Common Causes:**
1. No internet connection (40%)
2. Stream is offline/broken (35%)
3. Network blocking IPTV (15%)
4. App bug (10%)

**Resolution Steps:**

**Step 1: Verify Internet Connection (30 seconds)**
```
Agent: "Let's first check your internet connection. Can you:
1. Open a web browser and visit google.com
2. Try playing a YouTube video
Does that work?"
```

If YES → Go to Step 2
If NO → **Internet Issue** - Advise:
- Check WiFi/mobile data enabled
- Restart router
- Try different network
- Contact ISP if persistent

**Step 2: Try Different Channel (30 seconds)**
```
Agent: "Let's test if other channels work. Can you:
1. Go back to the channel list
2. Try playing 2-3 different channels
Do any of them work?"
```

If YES → **Single Channel Issue**
```
"The specific channel you tried may be temporarily offline. 
This is normal for free IPTV streams. Try:
1. Use the 'Scan Channels' feature (refresh icon)
2. Choose channels with green checkmark
3. Try again in a few hours"
```
✅ Close ticket

If NO → Go to Step 3

**Step 3: Check for Error Message (1 minute)**
```
Agent: "Do you see any error message? If yes, can you:
1. Take a screenshot
2. Or write down the exact message
3. Look for an 'Error Code' (like ERR_NET_001)"
```

**Common Error Codes:**
- **ERR_NET_001** (No Internet) → Back to Step 1
- **ERR_NET_002** (Timeout) → Network too slow, try WiFi
- **ERR_PLAY_001** (Stream unavailable) → Use external player
- **ERR_PLAY_002** (Format unsupported) → Use external player

**Step 4: Try External Player (2 minutes)**
```
Agent: "Let's try opening the stream in an external player:
1. Tap the channel again
2. Look for the 'Open in New' icon (top right)
3. Select VLC or MX Player
4. If you don't have these, download VLC from Play Store (free)"
```

If works in external player → ✅ Workaround provided
If doesn't work → **Stream is dead** - Close ticket

**Step 5: Clear Cache (3 minutes)**
```
Agent: "Let's clear the app cache:
1. Go to Android Settings
2. Tap 'Apps' or 'Applications'
3. Find and tap 'TV Viewer'
4. Tap 'Storage'
5. Tap 'Clear Cache' (NOT Clear Data)
6. Restart the app

Does it work now?"
```

If YES → ✅ Issue resolved
If NO → **Escalate to L2** with logs

**Script for Ticket Close:**
```
"Great! I'm glad we could resolve this. Quick tips for the future:
- Use the Scan Channels feature to find working channels
- Channels with green checkmarks are verified working
- External players (VLC) often work better for tricky streams

Is there anything else I can help you with today?"
```

**Average Resolution Time:** 10 minutes
**Success Rate:** 85%

---

### Issue 2: "How Do I...?" Questions (25% of tickets)

**Common Questions:**

**Q: How do I add my own channels/playlist?**
```
A: "Currently, TV Viewer doesn't support adding custom playlists. 
The app automatically discovers free IPTV channels from public 
repositories. This feature may be added in a future update.

Would you like help finding specific types of channels in our 
current catalog?"
```
✅ Close ticket

**Q: What does 'Scan Channels' do?**
```
A: "'Scan Channels' checks which streams are currently working. 

Here's how it works:
1. Tap the refresh icon (top right on home screen)
2. The app tests each channel (takes 5-10 minutes)
3. Working channels get a green checkmark ✓
4. Failed channels get a red X

Tip: Scan once per day for best results. Many streams change 
frequently."
```
✅ Close ticket

**Q: How do I filter channels?**
```
A: "You can filter channels in three ways:

1. By Type (TV/Radio): Dropdown at top - select 'TV' or 'Radio'
2. By Category: Dropdown - choose like 'News', 'Sports', 'Movies'
3. By Country: Dropdown - select specific country
4. Search: Type channel name in search box

You can combine filters! For example:
- Type: TV
- Category: Sports  
- Country: US
→ Shows only US sports TV channels"
```
✅ Close ticket

**Q: How do I cast to my TV?**
```
A: "Native casting isn't built into TV Viewer yet, but here's a workaround:

Option 1: External Player with Cast
1. Tap a channel
2. Tap 'Open in New' icon
3. Open in VLC Player
4. Use VLC's cast feature

Option 2: Screen Mirroring
1. Enable 'Cast Screen' on your Android device
2. Select your Chromecast/Smart TV
3. Play video in TV Viewer
4. Your whole screen will appear on TV

Official cast support is planned for a future update."
```
✅ Close ticket

**Q: Why are some channels not working?**
```
A: "Great question! Here's why:

TV Viewer uses free IPTV streams from the internet. These streams:
- Are maintained by third parties (not us)
- Can go offline anytime
- Change URLs frequently
- May be geographically restricted

This is normal! Here's what to do:
1. Use 'Scan Channels' daily to find working ones
2. Look for green checkmarks ✓
3. Have backup channels you like
4. Try external player if built-in doesn't work

The app automatically updates the channel list from public 
repositories to give you the best available streams."
```
✅ Close ticket

**Average Resolution Time:** 5 minutes
**Success Rate:** 99%

---

### Issue 3: App Crashes (15% of tickets)

**Ticket Examples:**
- "App closes suddenly"
- "Keeps crashing"
- "Won't open"
- "Crashes when playing video"

**Resolution Steps:**

**Step 1: Gather Information (1 minute)**
```
Agent: "I'll help you fix the crashes. First, some quick questions:
1. When does it crash? (On startup, when playing, randomly?)
2. Does it happen every time or occasionally?
3. What's your device model and Android version?
4. Did it ever work, or always crashed?"
```

**Step 2: Check App Version (1 minute)**
```
Agent: "Let's make sure you have the latest version:
1. Open Google Play Store
2. Search 'TV Viewer'
3. If it says 'Update', tap it
4. If it says 'Open', you're on the latest version

What version do you have?"
```

If outdated → Update and test
If latest → Go to Step 3

**Step 3: Check Device Storage (2 minutes)**
```
Agent: "Low storage can cause crashes. Let's check:
1. Go to Settings
2. Storage
3. How much free space do you have?

You need at least 1GB free for smooth operation."
```

If <500MB free → Advise to free space
If >1GB → Go to Step 4

**Step 4: Clear App Data (3 minutes)**
```
Agent: "Let's clear the app's data (this will reset the app):
1. Settings → Apps → TV Viewer
2. Storage → Clear Data (Yes, Clear Data not just Cache)
3. Go back and tap 'Force Stop'
4. Restart your phone
5. Open TV Viewer

Does it still crash?"
```

If NO crashes → ✅ Issue resolved
If still crashes → Go to Step 5

**Step 5: Request Crash Logs (2 minutes)**
```
Agent: "I need to get technical logs to investigate further:

If the app opens at all:
1. Open TV Viewer
2. Tap menu (three dots)
3. Tap 'Help'
4. Tap 'View Logs'
5. Tap 'Share' or 'Export'
6. Send to: https://github.com/tv-viewer-app/tv_viewer/issues

If the app won't open:
1. Download 'Logcat Reader' from Play Store
2. Open it
3. Look for 'TV Viewer' crashes
4. Tap 'Share'
5. Send to: https://github.com/tv-viewer-app/tv_viewer/issues

I'll escalate this to our technical team. You should hear back 
within 24 hours."
```

**Escalate to L2** with:
- Device model
- Android version
- App version
- Crash logs
- Steps to reproduce

**Average Resolution Time:** 15 minutes
**L2 Escalation Rate:** 30%

---

### Issue 4: Slow Performance (10% of tickets)

**Ticket Examples:**
- "App is laggy"
- "Takes forever to load"
- "Freezing"
- "Stuttering video"

**Quick Diagnosis:**
- If channel list loads slowly → Network/server issue
- If video stutters → Network bandwidth issue
- If UI is laggy → Device performance issue

**Resolution Steps:**

**Step 1: Check Device Specs (1 minute)**
```
Agent: "Let's check if your device meets minimum requirements:
- Android 5.0 or higher
- 2GB RAM minimum (4GB recommended)
- 1Ghz+ processor

What device model do you have?"
```

Search device specs online.

If below requirements:
```
"Your device is below the recommended specifications. The app 
may not perform optimally. Recommendations:
- Close other apps while using TV Viewer
- Use external player (VLC) which is more optimized
- Consider using a newer device if available"
```

**Step 2: Network Speed Test (2 minutes)**
```
Agent: "Let's test your internet speed. Please:
1. Open speedtest.net in your browser
2. Run the test
3. Tell me your Download speed (in Mbps)

What's the result?"
```

- <3 Mbps → Streaming will struggle
- 3-10 Mbps → SD quality okay
- 10+ Mbps → HD should work fine

If <3 Mbps:
```
"Your internet speed is too slow for smooth streaming:
- Required: At least 3 Mbps for SD quality
- Recommended: 10+ Mbps for HD
- Your speed: X Mbps

Try:
1. Move closer to WiFi router
2. Use mobile data if faster
3. Lower video quality in external player
4. Contact your ISP about slow speeds"
```

**Step 3: Clear Cache and Data (3 minutes)**
```
Agent: "Let's clear the app's cache to free up resources:
1. Settings → Apps → TV Viewer
2. Storage → Clear Cache
3. If still slow, tap 'Clear Data' (resets app)
4. Restart your phone

Test again - is it faster?"
```

**Step 4: Reduce Load (2 minutes)**
```
Agent: "Some tips to improve performance:
1. Don't run 'Scan Channels' while browsing
   - It tests hundreds of streams simultaneously
   - Very resource intensive
   - Let it complete before using app
   
2. Close other apps:
   - Hold home button
   - Swipe away unused apps
   
3. Use filters:
   - Instead of scrolling all channels
   - Filter by category/country
   - Reduces rendering load

4. Consider external player:
   - VLC and MX Player are highly optimized
   - Often perform better than built-in player"
```

**Average Resolution Time:** 12 minutes
**Success Rate:** 75%

---

### Issue 5: External Player Won't Open (7% of tickets)

**Ticket Examples:**
- "VLC won't open"
- "Can't use external player"
- "Nothing happens when I tap"

**Resolution Steps:**

**Step 1: Verify Player Installed (1 minute)**
```
Agent: "First, let's make sure you have a compatible player:

Supported players:
- VLC for Android (recommended)
- MX Player
- MPV Player
- Just Player

Please check Play Store:
1. Search for 'VLC Player'
2. Is it installed? (says 'Open' not 'Install')"
```

If NOT installed → Guide to install
If installed → Go to Step 2

**Step 2: Try Opening Manually (2 minutes)**
```
Agent: "Let's try manually opening the stream:
1. In TV Viewer, find the channel
2. Tap and hold on the channel (long press)
3. Look for 'Copy URL' option
4. Copy the URL
5. Open VLC Player
6. Tap three-dot menu
7. Select 'Open Network Stream'
8. Paste the URL
9. Tap Play

Does it work this way?"
```

If YES → Workaround provided, report bug
If NO → Stream is dead or format issue

**Step 3: Check Permissions (2 minutes)**
```
Agent: "The app may need permission to open other apps:
1. Settings → Apps → TV Viewer
2. Permissions
3. Make sure all permissions are enabled
4. Restart TV Viewer
5. Try opening external player again"
```

**Step 4: Update Both Apps (3 minutes)**
```
Agent: "Make sure both apps are updated:
1. Open Play Store
2. Search 'TV Viewer' → Update if available
3. Search 'VLC Player' → Update if available
4. Restart device
5. Test again"
```

If still not working → **Escalate to L2** (potential app bug)

**Average Resolution Time:** 8 minutes
**L2 Escalation Rate:** 15%

---

## 🔄 TROUBLESHOOTING WORKFLOWS

### Workflow 1: Video Playback Issues

```
START: User reports "video won't play"
  ↓
[Check Internet]
  ├─ Working → Continue
  └─ Not working → FIX INTERNET → END
  ↓
[Try Different Channels]
  ├─ Others work → SPECIFIC CHANNEL DOWN → END
  └─ None work → Continue
  ↓
[Check Error Message]
  ├─ ERR_NET_XXX → Network troubleshooting
  ├─ ERR_PLAY_XXX → External player option
  └─ No error → Continue
  ↓
[Clear Cache]
  ├─ Fixed → END
  └─ Not fixed → Continue
  ↓
[Try External Player]
  ├─ Works → Workaround provided → END
  └─ Doesn't work → ESCALATE TO L2 → END
```

### Workflow 2: App Crash Investigation

```
START: User reports app crashing
  ↓
[When does it crash?]
  ├─ On startup → Check version/reinstall
  ├─ When playing video → Network/stream issue
  └─ Randomly → Memory/device issue
  ↓
[Check App Version]
  ├─ Outdated → UPDATE → Test → END if fixed
  └─ Latest → Continue
  ↓
[Check Storage Space]
  ├─ <500MB → FREE SPACE → Test → END if fixed
  └─ >1GB → Continue
  ↓
[Clear Data & Restart]
  ├─ Fixed → END
  └─ Not fixed → Continue
  ↓
[Get Logs & ESCALATE TO L2]
```

### Workflow 3: Performance Issues

```
START: User reports slow/laggy app
  ↓
[What's slow?]
  ├─ Channel list loading → Network issue
  ├─ Video stuttering → Bandwidth issue
  └─ UI laggy → Device issue
  ↓
[Check Device Specs]
  ├─ Below minimum → Explain limitations → Suggest external player
  └─ Meets requirements → Continue
  ↓
[Network Speed Test]
  ├─ <3 Mbps → Explain need for faster internet
  └─ >3 Mbps → Continue
  ↓
[Clear Cache]
  ├─ Improved → Give performance tips → END
  └─ Still slow → Continue
  ↓
[Recommend External Player]
  └─ VLC performs better → END
```

---

## 📈 ESCALATION PROCEDURES

### When to Escalate to L2

**Immediate Escalation (within 1 hour):**
- App won't open after reinstall
- Crash with error logs
- Suspected app bug
- Data loss or corruption
- Multiple users reporting same issue

**Standard Escalation (within 24 hours):**
- Issue not resolved after all L1 steps
- User requests technical explanation
- Needs log analysis
- External player integration issues
- Performance issues on high-end devices

**What to Include in Escalation:**

```
Subject: [L2] [Category] Brief description
Priority: High/Medium/Low
Ticket #: 12345

User Information:
- Device: Samsung Galaxy S21
- Android Version: 13
- App Version: 1.5.0
- Connection Type: WiFi/4G

Issue Description:
[Clear, concise description of problem]

Steps Already Taken:
1. Checked internet connection - OK
2. Tried different channels - same issue
3. Cleared cache - no change
4. Reinstalled app - still crashes

Logs Attached:
- User screenshot: [link]
- App logs: [attached]
- Crash report: [attached]

Expected Behavior:
[What should happen]

Actual Behavior:
[What actually happens]

Reproducibility:
- Always / Sometimes / Once
- Steps to reproduce:
  1. [Step 1]
  2. [Step 2]

User Impact:
- Cannot use app at all / Feature broken / Minor annoyance

Agent Notes:
[Any additional observations]
```

### Escalation SLAs

| Priority | L1 → L2 | L2 → L3 | Total Resolution |
|----------|---------|---------|------------------|
| Critical | 15 min | 1 hour | 4 hours |
| High | 2 hours | 4 hours | 24 hours |
| Medium | 24 hours | 48 hours | 5 days |
| Low | 48 hours | 1 week | 2 weeks |

---

## 💬 CANNED RESPONSES

### Response 1: Acknowledging Ticket

```
Subject: Re: [Issue Description] - Ticket #12345

Hi [Name],

Thank you for contacting TV Viewer Support! I'm [Agent Name] and I'll 
be helping you today.

I understand you're experiencing [brief issue description]. I'll do my 
best to resolve this quickly.

To help diagnose the issue, could you please provide:
1. Your device make and model (e.g., Samsung Galaxy S20)
2. Android version (Settings → About Phone)
3. Any error messages you're seeing (screenshot if possible)

I'll wait for your reply and get back to you within [X hours].

Best regards,
[Agent Name]
TV Viewer Support Team
```

### Response 2: Issue Resolved

```
Subject: Re: [Issue Description] - Ticket #12345 [RESOLVED]

Hi [Name],

Great news! I'm glad we could resolve your issue with [brief solution].

To recap, here's what fixed it:
- [Solution step 1]
- [Solution step 2]

Here are some tips to prevent this in the future:
- [Tip 1]
- [Tip 2]

If you have any other questions or concerns, please don't hesitate to 
reach out. We're here to help!

Was I able to fully resolve your issue today?
[Link to satisfaction survey]

Best regards,
[Agent Name]
TV Viewer Support Team
```

### Response 3: Escalated to Technical Team

```
Subject: Re: [Issue Description] - Ticket #12345 [ESCALATED]

Hi [Name],

Thank you for your patience while I investigated your issue.

I've escalated your case to our technical team for further investigation. 
Here's what happens next:

1. Our L2 technical team will review the details
2. They may reach out if they need more information
3. You should hear back within [timeframe]
4. Your ticket number remains: #12345

In the meantime, here's a workaround you can try:
[Workaround if available]

I'll personally follow up with you within [timeframe] to ensure this 
gets resolved.

Thank you for your understanding!

Best regards,
[Agent Name]
TV Viewer Support Team
```

### Response 4: Feature Not Available

```
Subject: Re: Feature Request - Ticket #12345

Hi [Name],

Thank you for reaching out and for your interest in this feature!

Currently, [feature name] is not available in TV Viewer. I understand 
this would be useful for [use case].

Good news: Your feedback has been forwarded to our product team! We're 
always looking to improve the app based on user needs.

While this feature isn't available yet, here's an alternative approach:
[Workaround or alternative]

Want to stay updated? Follow us:
- Twitter: @tvviewer
- Email updates: [signup link]

Is there anything else I can help you with today?

Best regards,
[Agent Name]
TV Viewer Support Team
```

### Response 5: Known Issue

```
Subject: Re: [Issue Description] - Ticket #12345

Hi [Name],

Thank you for reporting this issue. We're aware of this problem and 
our team is actively working on a fix.

What we know:
- Issue: [Description]
- Affected: [Who/what]
- Status: [Being investigated / Fix in progress / Fix in next release]
- Expected Fix: [Timeline if known]

In the meantime, here's a workaround:
1. [Workaround step 1]
2. [Workaround step 2]

We appreciate your patience! I'll update you as soon as the fix is 
released.

Best regards,
[Agent Name]
TV Viewer Support Team
```

---

## 🛠️ TOOLS & RESOURCES

### Internal Tools

1. **Ticketing System**
   - URL: [ticketing-system-url]
   - Login: Use your company credentials
   - Create ticket: Document all interactions

2. **Knowledge Base**
   - URL: [kb-url]
   - Search before responding
   - Update if you find new solutions

3. **Log Analyzer**
   - URL: [log-analyzer-url]
   - Paste user logs
   - Auto-identifies common errors

4. **Device Compatibility Checker**
   - URL: [device-checker-url]
   - Enter device model
   - Shows if supported

### External Resources

1. **Test Streams**
   - Sample working stream: [url]
   - Use to verify network/player

2. **Android Version History**
   - [Link to version reference]
   - Helps identify OS limitations

3. **VLC Documentation**
   - [vlc-docs-url]
   - For advanced external player questions

### Quick Reference Links

- User Guide: [link]
- FAQ: [link]
- Troubleshooting: [link]
- Error Code Reference: [link]
- Video Tutorials: [youtube-playlist]
- System Requirements: [link]

### Support Contacts

- L1 Team Lead: [email/slack]
- L2 Technical Support: [email/slack]
- Engineering On-Call: [phone]
- Product Manager: [email]

---

## 📊 METRICS & KPIs

### Track These Metrics

**Personal Metrics:**
- Tickets handled per day (Target: 15-20)
- Average response time (Target: <30 min)
- Average resolution time (Target: <15 min)
- First contact resolution rate (Target: >70%)
- Customer satisfaction score (Target: >4.0/5)
- Escalation rate (Target: <15%)

**Team Metrics:**
- Total daily tickets
- Top issue categories
- Peak hours
- Resolution rate by category

### End-of-Day Report

Fill out daily:
- Tickets handled: [number]
- Resolved: [number]
- Escalated: [number]
- Most common issue today: [description]
- Challenges faced: [notes]
- Suggestions for improvement: [notes]

---

## 📝 NOTES & TIPS

### Communication Best Practices

1. **Be Empathetic**
   - Acknowledge frustration
   - Use "I understand..." statements
   - Never blame the user

2. **Be Clear**
   - Use simple language
   - Number your steps
   - Confirm understanding

3. **Be Professional**
   - Friendly but professional tone
   - Proper grammar and spelling
   - No slang or abbreviations

4. **Set Expectations**
   - Give realistic timeframes
   - Under-promise, over-deliver
   - Follow up when promised

### Common Pitfalls to Avoid

❌ DON'T:
- Make promises you can't keep
- Blame other teams or users
- Share unconfirmed information
- Give up too quickly
- Forget to follow up

✅ DO:
- Document everything
- Ask clarifying questions
- Test solutions yourself
- Learn from escalations
- Update knowledge base

### Agent Self-Care

- Take breaks between difficult tickets
- Ask for help when needed
- Share wins with team
- Learn from mistakes
- Celebrate successes

---

**End of L1 Support Playbook**

**Questions?** Contact your team lead or L2 support.

**Feedback?** Help improve this playbook! Send suggestions to: [feedback-email]

**Last Updated:** December 2024  
**Next Review:** Monthly

---
