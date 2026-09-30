# LG Content Store submission status

**Prepared:** September 30, 2026  
**App:** TV Viewer  
**Package ID:** `app.tvviewer.webos`  
**Version:** 2.25.0  
**Status:** Submission bundle prepared; LG account, device testing, content-rights
review, and certification approval remain open.

## Readiness summary

| Workstream | Status | Evidence |
|---|---|---|
| webOS application | Ready for device validation | FHD and HD IPKs build from the same validated source |
| Store metadata | Prepared | Listing copy and exact field values below |
| Store artwork | Prepared | 400x400 icon, 1920x1080 splash, four FHD screenshots |
| UX scenario | Prepared | `TV-Viewer-LG-webOS-UX-Scenario-v2.25.0.pptx` |
| Self-evaluation checklist | Draft prepared | Primary sheet: 8 Pass, 20 N/A, 25 pending device cases. Additional checks: 13 Pass, 7 N/A, 31 pending content-review cases |
| Privacy and permissions | Prepared | No account, analytics, ads, payment, device identifiers, or Luna Bus permissions |
| Physical/Cloud Test Lab evidence | Blocked externally | Requires an LG TV, LG App CTS, or Seller Lounge Cloud Test Lab |
| Content-rights acceptance | Blocked externally | Requires LG 1:1 Q&A and territory/content decision |
| Store publication | Not submitted | Requires Seller Lounge access and LG certification approval |

## Seller Lounge field values

| Field | Value |
|---|---|
| App name | TV Viewer |
| App ID | `app.tvviewer.webos` |
| Version | 2.25.0 |
| Category | Entertainment |
| Language | English |
| Minimum planned platform | webOS TV 5.0 |
| Supported resolutions | 1920x1080 and 1280x720 |
| Privacy policy | `https://github.com/tv-viewer-app/tv_viewer/blob/master/PRIVACY_POLICY.md` |
| Support URL | `https://github.com/tv-viewer-app/tv_viewer/issues` |
| Login required | No |
| In-app purchase | No |
| Advertising | No |
| Analytics in webOS build | No |
| Privileged webOS APIs | None; `requiredACG` is an empty array |

**Short description**

> Browse and play community-maintained live TV and radio streams with a
> remote-first interface, search, filters, multi-source failover, and local
> favorites.

Use the full description from `README.md` in this directory.

## Upload set

1. `app.tvviewer.webos_2.25.0_1080p_all.ipk`
2. `app.tvviewer.webos_2.25.0_720p_all.ipk`
3. `icon-400.png`
4. The four files in `screenshots`
5. `lg-self-evaluation-checklist-5.0-tv-viewer-draft.xlsx`
6. `TV-Viewer-LG-webOS-UX-Scenario-v2.25.0.pptx`
7. Privacy and support URLs listed above

## Required actions before submission

1. Ask LG Seller Lounge 1:1 Q&A whether a curated community catalog is
   acceptable without direct broadcaster agreements.
2. Select initial territories only after the content-rights and geo-availability
   review.
3. Install the FHD package on a physical LG TV or run it through the official
   Cloud Test Lab and LG App CTS.
4. Test launch, D-pad, OK, Back, Magic Remote, media keys, playback,
   source fallback, suspend/resume, HD/FHD scaling, and exit behavior.
5. Replace every yellow blank in the checklist with `Pass` or `N/A` only when
   evidence exists.
6. Complete the Seller Lounge age-rating questionnaire.
7. Upload the final artifacts and submit for LG review.

## Go/no-go rule

Do not represent the app as published or certification-ready until every
official checklist case is `Pass` or `N/A`, device evidence is attached, LG
accepts the catalog/territory model, and Seller Lounge certification is
approved.
