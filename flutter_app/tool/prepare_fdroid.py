"""Remove Android self-update components from an F-Droid source build."""

from pathlib import Path
import re


MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "android"
    / "app"
    / "src"
    / "main"
    / "AndroidManifest.xml"
)


def prepare_manifest(path: Path = MANIFEST) -> None:
    content = path.read_text(encoding="utf-8")
    content = re.sub(
        r"\s*<!-- Self-update from GitHub Releases \(sideload/F-Droid users\) -->"
        r"\s*<uses-permission android:name=\"android\.permission\.REQUEST_INSTALL_PACKAGES\"/>",
        "",
        content,
    )
    content = re.sub(
        r"\n\s*<!-- FileProvider for in-app APK self-update install \(#207\) -->"
        r"\s*<provider\b.*?</provider>",
        "",
        content,
        flags=re.DOTALL,
    )
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    prepare_manifest()
