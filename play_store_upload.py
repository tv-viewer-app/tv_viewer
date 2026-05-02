"""
Google Play Console Automation Script for TV Viewer
====================================================
Automates: store listing update, AAB upload, internal testing release.

Prerequisites:
1. Create the app in Play Console manually (one-time, can't be automated)
2. Set up API access: Play Console → Setup → API access
3. Create/link a Google Cloud service account with "Release manager" role
4. Download the service account JSON key file
5. Install: pip install google-auth google-api-python-client

Usage:
  python play_store_upload.py --key path/to/service-account.json
  python play_store_upload.py --key path/to/service-account.json --track production
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: pip install google-auth google-api-python-client")
    sys.exit(1)

PACKAGE_NAME = "app.tvviewer.player"
SCRIPT_DIR = Path(__file__).parent


def _read_app_version():
    """Read version name + code from flutter_app/pubspec.yaml so we can't drift."""
    pubspec = SCRIPT_DIR / "flutter_app" / "pubspec.yaml"
    for line in pubspec.read_text(encoding="utf-8").splitlines():
        if line.startswith("version:"):
            raw = line.split(":", 1)[1].strip()  # e.g. "2.7.3+39"
            name, _, code = raw.partition("+")
            return name.strip(), int(code) if code else 0
    raise RuntimeError("Could not find `version:` in pubspec.yaml")


APP_VERSION_NAME, APP_VERSION_CODE = _read_app_version()
AAB_PATH = SCRIPT_DIR / "dist" / f"tv-viewer-v{APP_VERSION_NAME}.aab"

# Store listing content
LISTING = {
    "language": "en-US",
    "title": "TV Viewer - IPTV Player",
    "shortDescription": (
        "Free open-source IPTV player. 6,000+ live channels "
        "from 60+ countries worldwide."
    ),
    "fullDescription": """TV Viewer is a free, open-source IPTV streaming app that brings live television and radio from around the world to your device.

🌍 6,000+ Channels from 60+ Countries
Browse channels by country, language, or category. From news and sports to entertainment and music — all organized and searchable.

📻 Dedicated Radio Player
Listen to radio stations with a beautiful player UI featuring genre browsing, search, and now-playing controls.

🔍 Advanced Search & Filters
Smart search with prefix syntax (country:, category:, language:). Sort by name, country, or category. Collapsible filter sidebar for full-screen viewing.

📱 Picture-in-Picture
Keep watching while using other apps with native PiP support on Android 8.0+.

👨‍👩‍👧‍👦 Parental Controls
Built-in age verification and content filtering. First-run consent dialog ensures family safety.

🔒 Privacy First & Secure
No account required. No tracking. No ads. Google Play Integrity API verified. All data stays on your device.

📊 Built-in Diagnostics
Network diagnostics, stream URL tester, system info — troubleshoot issues right from the app.

✨ Full Feature List:
• Live TV streaming from community-maintained IPTV playlists
• Dedicated radio player with genre browsing
• Advanced search with prefix syntax
• Sort channels by name, country, category, type
• Channel thumbnails with cached images
• Swipe to report broken channels
• Misclassification reporting
• Collapsible filters for full-screen viewing
• Picture-in-Picture mode
• Chromecast & external player support (VLC, MX Player)
• Parental controls with age gate
• Settings screen with stream timeout controls
• M3U repository management (add/remove sources)
• Auto-update notifications from GitHub releases
• Onboarding tooltips for new users
• Dark theme
• Hebrew and RTL language support

TV Viewer does not host any content. All streams come from publicly available community-maintained playlists (IPTV).""",
}

RELEASE_NOTES = {
    "en-US": f"""What's new in v{APP_VERSION_NAME}:
• Settings screen with stream timeout controls & theme toggle
• Advanced search: country:, category:, language:, type: prefixes
• Sort channels by name, country, category, or type
• Channel thumbnails with cached network images
• M3U repository management — add/remove playlist sources
• Dedicated radio player with genre browsing
• Auto-update checker via GitHub Releases
• Chromecast & external player improvements
• Google Play Integrity API for app security
• First-run consent dialog with age verification
• Network diagnostics & stream tester
• Onboarding tooltips for new users
• Rich channel info popup with EPG data"""
}


def get_service(key_path: str):
    """Build the Google Play Developer API service."""
    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/androidpublisher"],
    )
    return build("androidpublisher", "v3", credentials=credentials)


def update_listing(service, edit_id: str):
    """Update the store listing (title, descriptions)."""
    print(f"  Updating store listing ({LISTING['language']})...")
    service.edits().listings().update(
        packageName=PACKAGE_NAME,
        editId=edit_id,
        language=LISTING["language"],
        body={
            "title": LISTING["title"],
            "shortDescription": LISTING["shortDescription"],
            "fullDescription": LISTING["fullDescription"],
            "language": LISTING["language"],
        },
    ).execute()
    print("  ✓ Store listing updated")


def upload_aab(service, edit_id: str, aab_path: str):
    """Upload the AAB to the edit."""
    print(f"  Uploading AAB ({Path(aab_path).name}, {Path(aab_path).stat().st_size / 1e6:.1f} MB)...")
    media = MediaFileUpload(aab_path, mimetype="application/octet-stream")
    response = service.edits().bundles().upload(
        packageName=PACKAGE_NAME,
        editId=edit_id,
        media_body=media,
    ).execute()
    version_code = response["versionCode"]
    print(f"  ✓ AAB uploaded (versionCode: {version_code})")
    return version_code


def assign_to_track(service, edit_id: str, track: str, version_code: int):
    """Assign the uploaded version to a release track."""
    print(f"  Assigning versionCode {version_code} to '{track}' track...")
    release_notes = [
        {"language": lang, "text": text}
        for lang, text in RELEASE_NOTES.items()
    ]
    service.edits().tracks().update(
        packageName=PACKAGE_NAME,
        editId=edit_id,
        track=track,
        body={
            "track": track,
            "releases": [
                {
                    "versionCodes": [str(version_code)],
                    "releaseNotes": release_notes,
                    "status": "completed",
                    "name": APP_VERSION_NAME,
                }
            ],
        },
    ).execute()
    print(f"  ✓ Release assigned to '{track}' track")


def main():
    parser = argparse.ArgumentParser(
        description="Upload TV Viewer to Google Play Console"
    )
    parser.add_argument(
        "--key", required=True, help="Path to service account JSON key file"
    )
    parser.add_argument(
        "--aab", default=str(AAB_PATH), help=f"Path to AAB file (default: {AAB_PATH})"
    )
    parser.add_argument(
        "--track",
        default="internal",
        choices=["internal", "alpha", "beta", "production"],
        help="Release track (default: internal)",
    )
    parser.add_argument(
        "--listing-only",
        action="store_true",
        help="Only update store listing, don't upload AAB",
    )
    args = parser.parse_args()

    if not os.path.exists(args.key):
        print(f"ERROR: Key file not found: {args.key}")
        sys.exit(1)

    if not args.listing_only and not os.path.exists(args.aab):
        print(f"ERROR: AAB file not found: {args.aab}")
        print("Build it with: cd flutter_app && flutter build appbundle --release")
        sys.exit(1)

    print(f"Package: {PACKAGE_NAME}")
    print(f"Track:   {args.track}")
    print()

    service = get_service(args.key)

    # Create a new edit (transaction)
    print("Creating edit...")
    edit = service.edits().insert(
        packageName=PACKAGE_NAME, body={}
    ).execute()
    edit_id = edit["id"]
    print(f"  ✓ Edit created (id: {edit_id})")

    try:
        # Update store listing
        update_listing(service, edit_id)

        if not args.listing_only:
            # Upload AAB
            version_code = upload_aab(service, edit_id, args.aab)

            # Assign to track
            assign_to_track(service, edit_id, args.track, version_code)

        # Commit the edit
        print("Committing edit...")
        service.edits().commit(
            packageName=PACKAGE_NAME, editId=edit_id
        ).execute()
        print("  ✓ Edit committed successfully!")
        print()
        print("=" * 50)
        if args.listing_only:
            print("Store listing updated successfully!")
        else:
            print(f"Release uploaded to '{args.track}' track!")
            print(f"Go to Play Console to review: https://play.google.com/console")
        print("=" * 50)

    except Exception as e:
        print(f"\nERROR: {e}")
        print("Rolling back edit...")
        try:
            service.edits().delete(
                packageName=PACKAGE_NAME, editId=edit_id
            ).execute()
            print("  ✓ Edit rolled back")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
