"""
Tests for legacyai.app_pack.loader — manifest discovery and parsing.
"""

import json
from pathlib import Path

import pytest
import yaml

from legacyai.app_pack.loader import (
    find_manifest,
    list_packs,
    load_manifest,
    validate_manifest,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def linux_manifest_path():
    """Return the path to the real linux/desktop.yml manifest."""
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "app-packs" / "linux" / "desktop.yml"


@pytest.fixture()
def windows_manifest_path():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "app-packs" / "windows" / "desktop.yml"


@pytest.fixture()
def macos_manifest_path():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "app-packs" / "macos" / "desktop.yml"


@pytest.fixture()
def tmp_manifest(tmp_path):
    """Create a minimal valid manifest in a temp directory."""
    data = {
        "id": "test_pack",
        "description": "Test pack",
        "platform": "linux",
        "apps": [
            {
                "id": "testapp",
                "name": "Test App",
                "description": "A test application.",
                "distros": {
                    "debian_ubuntu": {
                        "package_manager": "apt",
                        "commands": ["apt-get install -y testapp"],
                    }
                },
            }
        ],
    }
    manifest_file = tmp_path / "test_pack.yml"
    manifest_file.write_text(yaml.dump(data), encoding="utf-8")
    return manifest_file


# ---------------------------------------------------------------------------
# load_manifest
# ---------------------------------------------------------------------------

class TestLoadManifest:
    def test_loads_linux_manifest(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        assert isinstance(data, dict)
        assert data["id"] == "desktop"
        assert data["platform"] == "linux"
        assert isinstance(data["apps"], list)
        assert len(data["apps"]) >= 1

    def test_loads_windows_manifest(self, windows_manifest_path):
        data = load_manifest(windows_manifest_path)
        assert data["id"] == "desktop"
        assert data["platform"] == "windows"

    def test_loads_macos_manifest(self, macos_manifest_path):
        data = load_manifest(macos_manifest_path)
        assert data["id"] == "desktop"
        assert data["platform"] == "macos"

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Manifest not found"):
            load_manifest(tmp_path / "nonexistent.yml")

    def test_raises_on_malformed_yaml(self, tmp_path):
        bad = tmp_path / "bad.yml"
        bad.write_text(": :\n  broken yaml: [unclosed", encoding="utf-8")
        with pytest.raises(Exception):
            load_manifest(bad)

    def test_raises_on_non_mapping_yaml(self, tmp_path):
        bad = tmp_path / "list.yml"
        bad.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Expected a YAML mapping"):
            load_manifest(bad)

    def test_loads_tmp_manifest(self, tmp_manifest):
        data = load_manifest(tmp_manifest)
        assert data["id"] == "test_pack"


# ---------------------------------------------------------------------------
# Required fields in real manifests
# ---------------------------------------------------------------------------

class TestManifestRequiredFields:
    @pytest.mark.parametrize("fixture_name", ["linux_manifest_path", "windows_manifest_path", "macos_manifest_path"])
    def test_has_required_top_level_fields(self, fixture_name, request):
        path = request.getfixturevalue(fixture_name)
        data = load_manifest(path)
        for field in ("id", "description", "platform", "apps"):
            assert field in data, f"Missing required field '{field}' in {path}"

    def test_linux_apps_have_distros(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        apps_with_installs = [
            a for a in data["apps"]
            if "distros" in a or "install" in a
        ]
        assert len(apps_with_installs) >= 1

    def test_windows_apps_have_install(self, windows_manifest_path):
        data = load_manifest(windows_manifest_path)
        for app in data["apps"]:
            assert "install" in app, f"Windows app '{app.get('id')}' missing 'install' key"

    def test_macos_apps_have_install(self, macos_manifest_path):
        data = load_manifest(macos_manifest_path)
        for app in data["apps"]:
            assert "install" in app, f"macOS app '{app.get('id')}' missing 'install' key"


# ---------------------------------------------------------------------------
# App content — specific expected apps
# ---------------------------------------------------------------------------

class TestLinuxManifestContent:
    def test_contains_firefox(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        ids = {a["id"] for a in data["apps"]}
        assert "firefox" in ids

    def test_contains_signal(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        ids = {a["id"] for a in data["apps"]}
        assert "signal" in ids

    def test_contains_tor_browser(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        ids = {a["id"] for a in data["apps"]}
        assert "tor_browser" in ids

    def test_contains_spotify(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        ids = {a["id"] for a in data["apps"]}
        assert "spotify" in ids

    def test_contains_netflix_entry(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        ids = {a["id"] for a in data["apps"]}
        assert "netflix_ready" in ids

    def test_netflix_has_post_install_notes(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        netflix = next(a for a in data["apps"] if a["id"] == "netflix_ready")
        notes = netflix.get("post_install_notes", "").lower()
        # Notes must mention netflix (the service) so users know what this entry is for
        assert "netflix" in notes

    def test_netflix_does_not_claim_direct_install(self, linux_manifest_path):
        """Netflix should NOT be described as a direct install."""
        data = load_manifest(linux_manifest_path)
        netflix = next(a for a in data["apps"] if a["id"] == "netflix_ready")
        desc = netflix.get("description", "").lower()
        # Should be described as browser-based or access, not a native install
        assert "browser" in desc or "access" in desc

    def test_signal_debian_has_pre_install_repo_step(self, linux_manifest_path):
        data = load_manifest(linux_manifest_path)
        signal = next(a for a in data["apps"] if a["id"] == "signal")
        deb_entry = signal["distros"]["debian_ubuntu"]
        pre = deb_entry.get("pre_install", [])
        assert any("signal" in cmd.lower() for cmd in pre)


# ---------------------------------------------------------------------------
# list_packs
# ---------------------------------------------------------------------------

class TestListPacks:
    def test_lists_real_packs(self):
        packs = list_packs()
        assert len(packs) >= 3  # linux, windows, macos

    def test_pack_summary_has_required_keys(self):
        packs = list_packs()
        for pack in packs:
            for key in ("id", "platform", "description", "path"):
                assert key in pack, f"Missing key '{key}' in pack summary"

    def test_platforms_covered(self):
        packs = list_packs()
        platforms = {p["platform"] for p in packs}
        assert "linux" in platforms
        assert "windows" in platforms
        assert "macos" in platforms


# ---------------------------------------------------------------------------
# find_manifest
# ---------------------------------------------------------------------------

class TestFindManifest:
    def test_finds_linux_desktop(self):
        path = find_manifest("desktop", "linux")
        assert path.exists()
        assert path.suffix == ".yml"

    def test_finds_windows_desktop(self):
        path = find_manifest("desktop", "windows")
        assert path.exists()

    def test_finds_macos_desktop(self):
        path = find_manifest("desktop", "macos")
        assert path.exists()

    def test_raises_on_unknown_pack(self):
        with pytest.raises(FileNotFoundError, match="No manifest found"):
            find_manifest("does_not_exist", "linux")

    def test_raises_on_unknown_os(self):
        with pytest.raises(FileNotFoundError, match="No manifest found"):
            find_manifest("desktop", "amiga")


# ---------------------------------------------------------------------------
# validate_manifest — schema validation
# ---------------------------------------------------------------------------

class TestValidateManifest:
    def test_valid_manifest_passes(self):
        data = {
            "id": "my_pack",
            "description": "A pack",
            "platform": "linux",
            "apps": [
                {"id": "app1", "name": "App 1", "description": "Desc."}
            ],
        }
        # Should not raise
        validate_manifest(data)

    def test_missing_required_field_raises_or_passes_gracefully(self):
        """
        When jsonschema is installed, a missing required field should raise.
        When it is not installed, validation is silently skipped.
        """
        data = {
            "description": "Missing id and platform",
            "apps": [],
        }
        try:
            import jsonschema  # noqa: F401
            with pytest.raises(Exception):
                validate_manifest(data)
        except ImportError:
            pass  # jsonschema not available — skip
