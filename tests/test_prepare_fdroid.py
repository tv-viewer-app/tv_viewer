from pathlib import Path

from flutter_app.tool.prepare_fdroid import prepare_manifest


def test_prepare_manifest_removes_self_update_components(tmp_path: Path) -> None:
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(
        """<manifest>
    <!-- Self-update from GitHub Releases (sideload/F-Droid users) -->
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>
    <application>
        <!-- FileProvider for in-app APK self-update install (#207) -->
        <provider android:name="androidx.core.content.FileProvider">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS"/>
        </provider>
    </application>
</manifest>
""",
        encoding="utf-8",
    )

    prepare_manifest(manifest)
    prepare_manifest(manifest)

    result = manifest.read_text(encoding="utf-8")
    assert "REQUEST_INSTALL_PACKAGES" not in result
    assert "FileProvider" not in result
    assert "<application>" in result
