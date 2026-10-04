"""Assemble the LG Seller Lounge submission bundle with SHA-256 checksums."""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LISTING_DIR = REPO_ROOT / "store-listings" / "lg-webos"
WEBOS_DIR = REPO_ROOT / "webos_app"
VERSION = "2.25.0"
OUTPUT_ROOT = REPO_ROOT / "dist"
BUNDLE_NAME = f"lg-webos-submission-v{VERSION}"
BUNDLE_DIR = OUTPUT_ROOT / BUNDLE_NAME
ZIP_PATH = OUTPUT_ROOT / f"{BUNDLE_NAME}.zip"
UPLOAD_DIR = LISTING_DIR / "upload-ready"
TEST_IPK_ZIP_NAME = f"TV_Viewer_v{VERSION}_LG_webOS_1080p_Test_IPK.zip"

FILES = {
    WEBOS_DIR / "dist" / f"app.tvviewer.webos_{VERSION}_1080p_all.ipk": Path(
        "packages/app.tvviewer.webos_2.25.0_1080p_all.ipk"
    ),
    WEBOS_DIR / "dist" / f"app.tvviewer.webos_{VERSION}_720p_all.ipk": Path(
        "packages/app.tvviewer.webos_2.25.0_720p_all.ipk"
    ),
    LISTING_DIR / "icon-400.png": Path("artwork/icon-400.png"),
    LISTING_DIR / "lg-self-evaluation-checklist-5.0-tv-viewer-draft.xlsx": Path(
        "qa/lg-self-evaluation-checklist-5.0-tv-viewer-draft.xlsx"
    ),
    LISTING_DIR / f"TV-Viewer-LG-webOS-UX-Scenario-v{VERSION}.pptx": Path(
        f"qa/TV-Viewer-LG-webOS-UX-Scenario-v{VERSION}.pptx"
    ),
    LISTING_DIR / "README.md": Path("documentation/STORE_LISTING.md"),
    LISTING_DIR / "SUBMISSION_STATUS.md": Path("documentation/SUBMISSION_STATUS.md"),
    LISTING_DIR / "CONTENT_RIGHTS_AND_MODERATION.md": Path(
        "documentation/CONTENT_RIGHTS_AND_MODERATION.md"
    ),
    REPO_ROOT / "PRIVACY_POLICY.md": Path("documentation/PRIVACY_POLICY.md"),
}

for screenshot in sorted((LISTING_DIR / "screenshots").glob("*.png")):
    FILES[screenshot] = Path("artwork/screenshots") / screenshot.name

UPLOAD_FILES = {
    WEBOS_DIR / "dist" / f"app.tvviewer.webos_{VERSION}_1080p_all.ipk": (
        f"TV_Viewer_v{VERSION}_LG_webOS_1080p.ipk"
    ),
    WEBOS_DIR / "dist" / f"app.tvviewer.webos_{VERSION}_720p_all.ipk": (
        f"TV_Viewer_v{VERSION}_LG_webOS_720p.ipk"
    ),
    LISTING_DIR / "icon-400.png": "TV_Viewer_App_Icon_400x400.png",
    WEBOS_DIR / "splash.png": "TV_Viewer_Launcher_Background_1920x1080.png",
    LISTING_DIR / "screenshots" / "00-first-run-notice.png": (
        "TV_Viewer_Screenshot_01_First_Run.png"
    ),
    LISTING_DIR / "screenshots" / "01-catalog.png": (
        "TV_Viewer_Screenshot_02_Catalog.png"
    ),
    LISTING_DIR / "screenshots" / "02-remote-help.png": (
        "TV_Viewer_Screenshot_03_Remote_Help.png"
    ),
    LISTING_DIR / "screenshots" / "03-player-controls.png": (
        "TV_Viewer_Screenshot_04_Player.png"
    ),
    LISTING_DIR / "lg-self-evaluation-checklist-5.0-tv-viewer-draft.xlsx": (
        f"TV_Viewer_LG_Self_Checklist_v{VERSION}.xlsx"
    ),
    LISTING_DIR / f"TV-Viewer-LG-webOS-UX-Scenario-v{VERSION}.pptx": (
        f"TV_Viewer_LG_UX_Scenario_v{VERSION}.pptx"
    ),
    LISTING_DIR / "README.md": "TV_Viewer_Store_Listing.md",
    LISTING_DIR / "SUBMISSION_STATUS.md": "TV_Viewer_Submission_Status.md",
    LISTING_DIR / "CONTENT_RIGHTS_AND_MODERATION.md": (
        "TV_Viewer_Content_Rights_and_Moderation.md"
    ),
    REPO_ROOT / "PRIVACY_POLICY.md": "TV_Viewer_Privacy_Policy.md",
}

FILE_MAP = f"""TV Viewer v{VERSION} - LG Seller Lounge file map

App package / IPK:
  TV_Viewer_v{VERSION}_LG_webOS_1080p.ipk
  Use the 720p IPK only when LG requests an HD package.

App icon (400x400):
  TV_Viewer_App_Icon_400x400.png

Launcher Background Image (1920x1080):
  TV_Viewer_Launcher_Background_1920x1080.png

Screenshots:
  TV_Viewer_Screenshot_01_First_Run.png
  TV_Viewer_Screenshot_02_Catalog.png
  TV_Viewer_Screenshot_03_Remote_Help.png
  TV_Viewer_Screenshot_04_Player.png

QA documents:
  TV_Viewer_LG_Self_Checklist_v{VERSION}.xlsx
  TV_Viewer_LG_UX_Scenario_v{VERSION}.pptx

QA Test IPK attachment:
  {TEST_IPK_ZIP_NAME}
  Upload this ZIP in "Enter Test IPK File or Test URL".

Store copy, privacy, and review notes:
  TV_Viewer_Store_Listing.md
  TV_Viewer_Privacy_Policy.md
  TV_Viewer_Content_Rights_and_Moderation.md
  TV_Viewer_Submission_Status.md

Tag Keywords:
  live television radio news education documentary weather public television streaming IPTV

Contact Seller:
  Type: URL
  Value: https://github.com/tv-viewer-app/tv_viewer/issues

UK data information:
  Privacy Policy: Yes
  Data collected within the app: No
  Shared Data: No
  Privacy Policy URL: https://github.com/tv-viewer-app/tv_viewer/blob/master/PRIVACY_POLICY.md

QA registration:
  UX Scenario: TV_Viewer_LG_UX_Scenario_v{VERSION}.pptx
  Note category: Other Information
  Test account/password: Not applicable
  Voucher code: Not applicable
  Service URL: Leave blank
  Geo IP Block: No
  Billing / paid content: Not applicable / No
  In-App Ad: Not Applicable
  DRM: Not Applicable
  Streaming Protocol: HLS and HTTP/HTTPS, if both are offered
  Video Codec: H.264/AVC
  Audio Codec: AAC and MP3
  HDR: Not Applicable
"""

QA_FIELD_GUIDE = f"""TV Viewer v{VERSION} - LG App QA field guide

Reference email for QA results
  Enter the submitter's preferred monitored email address in Seller Lounge.
  Do not publish that personal email in store listing files.

UX Scenario File
  TV_Viewer_LG_UX_Scenario_v{VERSION}.pptx

Note for Tester
  Category: Other Information
  Text:
  TV Viewer is a free, open-source, remote-first live TV and radio player.
  No account, password, voucher, purchase, advertisement, analytics, DRM, or
  privileged webOS API is used. On first launch, accept the content notice;
  the catalog then loads from the public TV Viewer service. Use the D-pad and
  OK button to browse and open a channel. Back closes dialogs or playback and
  exits from the catalog. Stream availability and regional accessibility are
  controlled by independent stream providers. If a source fails, select Next
  source. Please test network launch, D-pad/OK/Back, Magic Remote, playback,
  Play/Pause, source switching, favorites, suspend/resume, and app exit.

Optional QA attachment
  TV_Viewer_LG_Self_Checklist_v{VERSION}.xlsx

Test Account/Password
  Select Not applicable.

Voucher Code
  Select Not applicable.

Test IPK File or Test URL
  Upload {TEST_IPK_ZIP_NAME}.
  Leave Service URL blank.

Geo IP Block
  Select No. The app does not implement geo-blocking. Individual third-party
  streams can still be unavailable by region.

Billing / paid content
  Select Not applicable or No paid content. There is no purchase, subscription,
  external paid-account conversion, or third-party billing flow.

In-App Ad
  Select Not Applicable.

Player Specification
  DRM: Not Applicable
  Streaming Protocol: HLS; also select HTTP/HTTPS if offered as a protocol
  Video Codec: H.264/AVC
  Audio Codec: AAC and MP3
  HDR: Not Applicable

Do not select MPEG-DASH, Smooth Streaming, PlayReady, Widevine, HEVC, or HDR
unless a separately tested release explicitly adds and validates them.
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    required_sources = set(FILES) | set(UPLOAD_FILES)
    missing = [str(source) for source in required_sources if not source.is_file()]
    if missing:
        raise SystemExit("Missing submission artifacts:\n- " + "\n- ".join(missing))

    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir(parents=True)
    upload_copied: list[Path] = []
    for source, filename in UPLOAD_FILES.items():
        target = UPLOAD_DIR / filename
        shutil.copy2(source, target)
        upload_copied.append(target)

    primary_ipk = (
        WEBOS_DIR / "dist" / f"app.tvviewer.webos_{VERSION}_1080p_all.ipk"
    )
    test_ipk_zip = UPLOAD_DIR / TEST_IPK_ZIP_NAME
    with zipfile.ZipFile(
        test_ipk_zip, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        archive.write(
            primary_ipk,
            f"TV_Viewer_v{VERSION}_LG_webOS_1080p.ipk",
        )
    upload_copied.append(test_ipk_zip)

    (UPLOAD_DIR / "SELLER_LOUNGE_FILE_MAP.txt").write_text(
        FILE_MAP, encoding="utf-8"
    )
    (UPLOAD_DIR / "QA_FIELD_GUIDE.txt").write_text(
        QA_FIELD_GUIDE, encoding="utf-8"
    )
    (UPLOAD_DIR / "SHA256SUMS.txt").write_text(
        "\n".join(
            f"{sha256(path)}  {path.name}" for path in sorted(upload_copied)
        )
        + "\n",
        encoding="utf-8",
    )

    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True)

    copied: list[Path] = []
    for source, relative_target in FILES.items():
        target = BUNDLE_DIR / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(target)

    manifest = BUNDLE_DIR / "SHA256SUMS.txt"
    manifest.write_text(
        "\n".join(
            f"{sha256(path)}  {path.relative_to(BUNDLE_DIR).as_posix()}"
            for path in sorted(copied)
        )
        + "\n",
        encoding="utf-8",
    )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(BUNDLE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, Path(BUNDLE_NAME) / path.relative_to(BUNDLE_DIR))

    print(UPLOAD_DIR)
    print(BUNDLE_DIR)
    print(ZIP_PATH)


if __name__ == "__main__":
    main()
