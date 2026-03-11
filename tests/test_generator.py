"""
Tests for legacyai.app_pack.generator — deterministic script generation.
"""

from pathlib import Path

import pytest
import yaml

from legacyai.app_pack.generator import generate_script, write_script
from legacyai.app_pack.loader import load_manifest, find_manifest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manifest(platform, apps=None):
    """Build a minimal manifest dict for testing."""
    base = {
        "id": "test_pack",
        "description": "Test pack for unit tests.",
        "platform": platform,
        "licensing_notes": "Test licensing note.",
        "apps": apps or [],
    }
    return base


def _linux_app(app_id="firefox", distros=None):
    return {
        "id": app_id,
        "name": app_id.title(),
        "description": f"{app_id.title()} browser.",
        "distros": distros or {
            "debian_ubuntu": {
                "package_manager": "apt",
                "pre_install": ["apt-get update -y"],
                "commands": ["apt-get install -y firefox"],
            },
            "fedora_rhel": {
                "package_manager": "dnf",
                "commands": ["dnf install -y firefox"],
            },
            "arch_manjaro": {
                "package_manager": "pacman",
                "commands": ["pacman -S --noconfirm firefox"],
            },
        },
    }


def _windows_app(app_id="firefox"):
    return {
        "id": app_id,
        "name": app_id.title(),
        "description": f"{app_id.title()} app.",
        "install": {
            "package_manager": "winget",
            "commands": [
                f"winget install --id Mozilla.Firefox -e --accept-source-agreements"
            ],
        },
    }


def _macos_app(app_id="firefox"):
    return {
        "id": app_id,
        "name": app_id.title(),
        "description": f"{app_id.title()} app.",
        "install": {
            "package_manager": "brew",
            "commands": ["brew install --cask firefox"],
        },
    }


# ---------------------------------------------------------------------------
# generate_script — Linux
# ---------------------------------------------------------------------------

class TestGenerateLinux:
    def test_returns_string(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert isinstance(script, str)

    def test_has_shebang(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert script.startswith("#!/usr/bin/env bash")

    def test_has_set_e(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert "set -euo pipefail" in script

    def test_contains_install_command_debian(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert "apt-get install -y firefox" in script

    def test_contains_install_command_fedora(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "fedora_rhel")
        assert "dnf install -y firefox" in script

    def test_contains_install_command_arch(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "arch_manjaro")
        assert "pacman -S --noconfirm firefox" in script

    def test_contains_pack_id_in_header(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert "test_pack" in script

    def test_contains_description_in_header(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert "Test pack for unit tests" in script

    def test_contains_licensing_in_header(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert "Test licensing note" in script

    def test_pre_install_commands_included(self):
        manifest = _make_manifest("linux", [_linux_app()])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert "apt-get update -y" in script

    def test_post_install_notes_included(self):
        app = _linux_app()
        app["post_install_notes"] = "Restart your system after install."
        manifest = _make_manifest("linux", [app])
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert "Restart your system after install" in script

    def test_missing_distro_entry_skips_gracefully(self):
        """An app with no entry for arch_manjaro should be skipped with a comment."""
        app = {
            "id": "debonly",
            "name": "DebOnly",
            "description": "Only for Debian.",
            "distros": {
                "debian_ubuntu": {
                    "package_manager": "apt",
                    "commands": ["apt-get install -y debonly"],
                }
            },
        }
        manifest = _make_manifest("linux", [app])
        script = generate_script(manifest, "linux", "arch_manjaro")
        assert "Skipping" in script
        assert "debonly" in script.lower() or "DebOnly" in script

    def test_raises_on_missing_distro_arg(self):
        manifest = _make_manifest("linux", [_linux_app()])
        with pytest.raises(ValueError, match="--distro is required"):
            generate_script(manifest, "linux", None)

    def test_raises_on_invalid_distro(self):
        manifest = _make_manifest("linux", [_linux_app()])
        with pytest.raises(ValueError, match="Unknown distro"):
            generate_script(manifest, "linux", "slackware")

    def test_deterministic_output(self):
        """Same inputs should always produce identical output."""
        manifest = _make_manifest("linux", [_linux_app()])
        s1 = generate_script(manifest, "linux", "debian_ubuntu")
        s2 = generate_script(manifest, "linux", "debian_ubuntu")
        # Strip timestamps for determinism test
        import re

        def strip_ts(s):
            return re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", "TIMESTAMP", s)

        assert strip_ts(s1) == strip_ts(s2)


# ---------------------------------------------------------------------------
# generate_script — Windows
# ---------------------------------------------------------------------------

class TestGenerateWindows:
    def test_returns_string(self):
        manifest = _make_manifest("windows", [_windows_app()])
        script = generate_script(manifest, "windows")
        assert isinstance(script, str)

    def test_has_error_action_preference(self):
        manifest = _make_manifest("windows", [_windows_app()])
        script = generate_script(manifest, "windows")
        assert "$ErrorActionPreference" in script

    def test_contains_winget_command(self):
        manifest = _make_manifest("windows", [_windows_app()])
        script = generate_script(manifest, "windows")
        assert "winget install" in script

    def test_contains_write_host(self):
        manifest = _make_manifest("windows", [_windows_app()])
        script = generate_script(manifest, "windows")
        assert "Write-Host" in script

    def test_no_shebang(self):
        manifest = _make_manifest("windows", [_windows_app()])
        script = generate_script(manifest, "windows")
        assert not script.startswith("#!/")

    def test_distro_ignored_on_windows(self):
        """Passing a distro for Windows should not cause an error."""
        manifest = _make_manifest("windows", [_windows_app()])
        script = generate_script(manifest, "windows", "debian_ubuntu")
        assert "winget install" in script


# ---------------------------------------------------------------------------
# generate_script — macOS
# ---------------------------------------------------------------------------

class TestGenerateMacOS:
    def test_returns_string(self):
        manifest = _make_manifest("macos", [_macos_app()])
        script = generate_script(manifest, "macos")
        assert isinstance(script, str)

    def test_has_shebang(self):
        manifest = _make_manifest("macos", [_macos_app()])
        script = generate_script(manifest, "macos")
        assert script.startswith("#!/usr/bin/env bash")

    def test_contains_brew_command(self):
        manifest = _make_manifest("macos", [_macos_app()])
        script = generate_script(manifest, "macos")
        assert "brew install" in script

    def test_has_set_e(self):
        manifest = _make_manifest("macos", [_macos_app()])
        script = generate_script(manifest, "macos")
        assert "set -euo pipefail" in script


# ---------------------------------------------------------------------------
# generate_script — invalid OS
# ---------------------------------------------------------------------------

class TestInvalidOS:
    def test_raises_on_unknown_os(self):
        manifest = _make_manifest("linux", [_linux_app()])
        with pytest.raises(ValueError, match="Unsupported os_name"):
            generate_script(manifest, "dos", "debian_ubuntu")


# ---------------------------------------------------------------------------
# Real manifests integration
# ---------------------------------------------------------------------------

class TestRealManifests:
    def test_generate_linux_desktop_debian(self):
        path = find_manifest("desktop", "linux")
        manifest = load_manifest(path)
        script = generate_script(manifest, "linux", "debian_ubuntu")
        assert "#!/usr/bin/env bash" in script
        assert "signal" in script.lower()
        assert "firefox" in script.lower()
        assert "spotify" in script.lower()
        assert "tor" in script.lower()
        assert "netflix" in script.lower()

    def test_generate_linux_desktop_fedora(self):
        path = find_manifest("desktop", "linux")
        manifest = load_manifest(path)
        script = generate_script(manifest, "linux", "fedora_rhel")
        assert "dnf install" in script

    def test_generate_linux_desktop_arch(self):
        path = find_manifest("desktop", "linux")
        manifest = load_manifest(path)
        script = generate_script(manifest, "linux", "arch_manjaro")
        assert "pacman" in script or "yay" in script

    def test_generate_windows_desktop(self):
        path = find_manifest("desktop", "windows")
        manifest = load_manifest(path)
        script = generate_script(manifest, "windows")
        assert "winget install" in script
        assert "signal" in script.lower()

    def test_generate_macos_desktop(self):
        path = find_manifest("desktop", "macos")
        manifest = load_manifest(path)
        script = generate_script(manifest, "macos")
        assert "brew install" in script
        assert "signal" in script.lower()


# ---------------------------------------------------------------------------
# write_script
# ---------------------------------------------------------------------------

class TestWriteScript:
    def test_writes_file(self, tmp_path):
        script = "#!/usr/bin/env bash\necho 'hello'\n"
        out = write_script(script, tmp_path / "install.sh")
        assert out.exists()
        assert out.read_text(encoding="utf-8") == script

    def test_creates_parent_dirs(self, tmp_path):
        script = "Write-Host 'hello'"
        out = write_script(script, tmp_path / "nested" / "dir" / "install.ps1")
        assert out.exists()

    def test_returns_resolved_path(self, tmp_path):
        script = "echo ok"
        out = write_script(script, tmp_path / "test.sh")
        assert out.is_absolute()

    def test_overwrites_existing_file(self, tmp_path):
        out_path = tmp_path / "install.sh"
        out_path.write_text("old content", encoding="utf-8")
        write_script("new content", out_path)
        assert out_path.read_text(encoding="utf-8") == "new content"
