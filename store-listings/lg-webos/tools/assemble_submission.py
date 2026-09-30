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

Store copy, privacy, and review notes:
  TV_Viewer_Store_Listing.md
  TV_Viewer_Privacy_Policy.md
  TV_Viewer_Content_Rights_and_Moderation.md
  TV_Viewer_Submission_Status.md
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
    (UPLOAD_DIR / "SELLER_LOUNGE_FILE_MAP.txt").write_text(
        FILE_MAP, encoding="utf-8"
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
