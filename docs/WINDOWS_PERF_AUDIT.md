# Windows Performance & Dependency Audit (Issue #168)

**Status:** v2.9.0 — initial baseline.
**Scope:** Native-feel performance, AV-friendliness, and startup time on
the Windows desktop build (PyInstaller-onedir, Python 3.12).

## 1. Cold-start measurements (laptop, i7-1165G7, NVMe)

| Phase                                  | v2.7.x | v2.8.0 | v2.9.0 (target) |
|----------------------------------------|--------|--------|-----------------|
| Process spawn → first paint            | ~2.4 s | ~1.2 s | ≤ 1.0 s         |
| First paint → first row populated      | ~3.1 s | ~1.5 s | ≤ 1.5 s         |
| First playback (channel decoded)       | ~2.0 s | ~1.4 s | ≤ 1.4 s (HW)    |

Improvements since v2.7:
- Async analytics init in daemon thread (v2.8 / #163)
- Persistent file logging (v2.8.1 / #176) is non-blocking
- Spring-physics scroll uses critically-damped integration (v2.9 / #175)

## 2. Antivirus / heuristic friendliness

| Vendor        | v2.7.x onefile | v2.8.x onedir | v2.9.0 onedir signed |
|---------------|----------------|----------------|----------------------|
| Defender      | flagged 1× FP  | clean          | clean (target)       |
| Kaspersky     | clean          | clean          | clean                |
| Norton 360    | flagged 1× FP  | clean          | clean                |
| Avast         | clean          | clean          | clean                |

Decisions:
- Stay on **PyInstaller --onedir** (avoid onefile because of UPX-style
  decompression triggering Defender heuristics).
- Strip unused hidden imports — the spec file should not pull in
  `numpy`, `scipy`, `matplotlib`, or `pandas` (none are runtime deps).
- Keep `customtkinter` *out* of the hot path; v2.8 already moved root
  window to `tk.Tk()` for reliable rendering inside frozen builds.
- v2.9: investigate **EV signing certificate** so first-run SmartScreen
  is silent. (Tracked separately — needs purchasing decision.)

## 3. Dependency audit (active runtime deps)

| Package         | Version pin   | Notes                               |
|-----------------|---------------|-------------------------------------|
| customtkinter   | >= 5.2.0      | UI shell only; not used in hotpath  |
| Pillow          | >= 10.0.0     | Image decoding for logos            |
| aiohttp         | >= 3.9.0      | Channel fetch; HTTP/2 ready         |
| requests        | >= 2.31.0     | Sync HTTP fallback                  |
| python-vlc      | >= 3.0.18122  | Optional. HW decode chain (v2.8)    |
| pychromecast    | >= 13.0.0     | Optional Cast support               |
| ttkbootstrap    | >= 1.10.0     | Optional theming                    |

**Removed / not bundled:** numpy, scipy, matplotlib, pandas,
opencv-python, mediapipe, transformers, torch — none are imported at
runtime.  PyInstaller spec must explicitly exclude them.

## 4. Native / DirectX evaluation

We considered replacing tk + customtkinter widgets with WinUI3 /
WebView2 for hotpath rendering.  Conclusion for v2.9:

- **Keep tk.Canvas** for the row grid — it already gives us the smooth
  spring scroll (v2.9 / #175) and is GPU-accelerated where the driver
  supports it.
- **Keep VLC for video** — it already binds to the canvas hwnd and
  renders via D3D11VA when HW accel is available (v2.8 / #166).
- **Use ctypes/user32** for window chrome and DPI awareness (already
  done in `tv_mode.py:174`).
- **WinUI3 / WebView2 swap** would require a complete rewrite and is
  not justified by current bottleneck data.  Re-evaluate if startup
  budget tightens to <500 ms.

## 5. Concrete v2.9 changes

- Spring physics for scroll (#175) reduces visual jank during
  arrow-key navigation; replaces linear easing with critically-damped
  spring (`stiffness=0.18`, `damping=0.55`).
- Privacy / consent gating (#170) makes telemetry opt-in **before**
  any network call, eliminating the false-positive risk of
  uninstrumented analytics.
- Filter UI (#160) is a tk.Toplevel — no new dependencies; uses native
  Listbox.
- First-run tooltip tour (#162) is also native tk; no asset downloads.

## 6. Open follow-ups

| Item                                | Owner | Tracking |
|-------------------------------------|-------|----------|
| EV code-signing certificate         | TBD   | (new)    |
| `py-spy record` flamegraph capture  | TBD   | (new)    |
| WinUI3 spike (deferred from v2.9)   | TBD   | post v3.0 |
| Strip PyInstaller hidden imports    | CI    | #174     |
