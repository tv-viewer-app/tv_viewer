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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    missing = [str(source) for source in FILES if not source.is_file()]
    if missing:
        raise SystemExit("Missing submission artifacts:\n- " + "\n- ".join(missing))

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

    print(BUNDLE_DIR)
    print(ZIP_PATH)


if __name__ == "__main__":
    main()
