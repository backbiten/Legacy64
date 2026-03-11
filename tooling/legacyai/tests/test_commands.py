"""Tests for legacyai CLI commands."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture()
def repo(tmp_path):
    """Return a temporary directory set up as a legacyai repo."""
    from legacyai.commands.init import run as init_run
    import argparse

    args = argparse.Namespace()
    init_run(args, tmp_path)
    return tmp_path


@pytest.fixture()
def sample_file(tmp_path):
    """A small sample file to import."""
    f = tmp_path / "hello.bin"
    f.write_bytes(b"Hello, Legacy64!")
    return f


class TestInit:
    def test_creates_directories(self, tmp_path):
        from legacyai.commands.init import run, _REQUIRED_DIRS
        import argparse

        run(argparse.Namespace(), tmp_path)
        for rel in _REQUIRED_DIRS:
            assert (tmp_path / rel).is_dir(), f"Missing directory: {rel}"

    def test_creates_config(self, tmp_path):
        from legacyai.commands.init import run
        import argparse

        run(argparse.Namespace(), tmp_path)
        cfg = tmp_path / ".legacyai.yml"
        assert cfg.exists()
        data = yaml.safe_load(cfg.read_text())
        assert data["version"] == 1

    def test_idempotent(self, tmp_path):
        from legacyai.commands.init import run
        import argparse

        run(argparse.Namespace(), tmp_path)
        run(argparse.Namespace(), tmp_path)  # second call should not fail


class TestAdd:
    def test_stores_object_and_creates_record(self, repo, sample_file):
        import argparse
        from legacyai.commands.add import run

        args = argparse.Namespace(
            path=str(sample_file),
            lane="legacy64",
            type="bin",
            name="test-artifact",
            version="1.0",
        )
        rc = run(args, repo)
        assert rc == 0

        # Object stored
        records = list((repo / "artifacts" / "legacy64").glob("*.yml"))
        assert len(records) == 1

        data = yaml.safe_load(records[0].read_text())
        assert data["lane"] == "legacy64"
        assert data["type"] == "bin"
        assert data["sha256"]
        assert (repo / "objects" / "sha256" / data["sha256"][:2] / data["sha256"]).exists()

    def test_missing_file_returns_error(self, repo):
        import argparse
        from legacyai.commands.add import run

        args = argparse.Namespace(
            path="/nonexistent/file.bin",
            lane="legacy32",
            type="bin",
            name=None,
            version=None,
        )
        rc = run(args, repo)
        assert rc == 1

    def test_idempotent_add(self, repo, sample_file):
        """Adding the same file twice should not fail (object already stored)."""
        import argparse
        from legacyai.commands.add import run

        args = argparse.Namespace(
            path=str(sample_file),
            lane="legacy64",
            type="bin",
            name=None,
            version=None,
        )
        assert run(args, repo) == 0
        # Reset name to ensure it gets a new UUID record
        args2 = argparse.Namespace(
            path=str(sample_file),
            lane="legacy32",
            type="bin",
            name=None,
            version=None,
        )
        assert run(args2, repo) == 0


class TestVerify:
    def test_empty_repo_passes(self, repo):
        import argparse
        from legacyai.commands.verify import run

        rc = run(argparse.Namespace(), repo)
        assert rc == 0

    def test_valid_artifact_passes(self, repo, sample_file):
        import argparse
        from legacyai.commands.add import run as add_run
        from legacyai.commands.verify import run as verify_run

        add_args = argparse.Namespace(
            path=str(sample_file),
            lane="legacy64",
            type="bin",
            name=None,
            version=None,
        )
        add_run(add_args, repo)
        rc = verify_run(argparse.Namespace(), repo)
        assert rc == 0

    def test_corrupted_object_fails(self, repo, sample_file):
        import argparse
        from legacyai.commands.add import run as add_run
        from legacyai.commands.verify import run as verify_run

        add_args = argparse.Namespace(
            path=str(sample_file),
            lane="legacy64",
            type="bin",
            name=None,
            version=None,
        )
        add_run(add_args, repo)

        # Corrupt the stored object
        records = list((repo / "artifacts" / "legacy64").glob("*.yml"))
        data = yaml.safe_load(records[0].read_text())
        obj_path = repo / "objects" / "sha256" / data["sha256"][:2] / data["sha256"]
        obj_path.chmod(0o644)
        obj_path.write_bytes(b"corrupted!")

        rc = verify_run(argparse.Namespace(), repo)
        assert rc == 1

    def test_missing_object_fails(self, repo, sample_file):
        import argparse
        from legacyai.commands.add import run as add_run
        from legacyai.commands.verify import run as verify_run

        add_args = argparse.Namespace(
            path=str(sample_file),
            lane="legacy64",
            type="bin",
            name=None,
            version=None,
        )
        add_run(add_args, repo)

        records = list((repo / "artifacts" / "legacy64").glob("*.yml"))
        data = yaml.safe_load(records[0].read_text())
        obj_path = repo / "objects" / "sha256" / data["sha256"][:2] / data["sha256"]
        obj_path.chmod(0o644)
        obj_path.unlink()

        rc = verify_run(argparse.Namespace(), repo)
        assert rc == 1


class TestBind:
    def _add_artifact(self, repo, sample_file, lane):
        import argparse
        from legacyai.commands.add import run as add_run

        args = argparse.Namespace(
            path=str(sample_file),
            lane=lane,
            type="bin",
            name=None,
            version=None,
        )
        add_run(args, repo)
        records = list((repo / "artifacts" / lane).glob("*.yml"))
        data = yaml.safe_load(records[-1].read_text())
        return data["id"]

    def test_bind_without_patch(self, repo, sample_file):
        import argparse
        from legacyai.commands.bind import run

        id32 = self._add_artifact(repo, sample_file, "legacy32")
        id64 = self._add_artifact(repo, sample_file, "legacy64")

        args = argparse.Namespace(
            source="v1.0.0",
            legacy32=id32,
            legacy64=id64,
            patch=None,
        )
        rc = run(args, repo)
        assert rc == 0

        bindings = list((repo / "bindings" / "source-patch").glob("*.yml"))
        assert len(bindings) == 1
        data = yaml.safe_load(bindings[0].read_text())
        assert data["type"] == "source-patch"
        assert data["legacy32_artifact"] == id32
        assert data["legacy64_artifact"] == id64

    def test_bind_with_patch(self, repo, sample_file, tmp_path):
        import argparse
        from legacyai.commands.bind import run

        patch_file = tmp_path / "fix.patch"
        patch_file.write_text("--- a/foo.c\n+++ b/foo.c\n@@ -1 +1 @@\n-old\n+new\n")

        id32 = self._add_artifact(repo, sample_file, "legacy32")
        id64 = self._add_artifact(repo, sample_file, "legacy64")

        args = argparse.Namespace(
            source="git://example.com/repo.git@abc1234",
            legacy32=id32,
            legacy64=id64,
            patch=str(patch_file),
        )
        rc = run(args, repo)
        assert rc == 0

        bindings = list((repo / "bindings" / "source-patch").glob("*.yml"))
        data = yaml.safe_load(bindings[0].read_text())
        assert "patch_file" in data
        assert "patch_sha256" in data
        assert (repo / data["patch_file"]).exists()

    def test_bind_with_missing_patch_fails(self, repo, sample_file):
        import argparse
        from legacyai.commands.bind import run

        id32 = self._add_artifact(repo, sample_file, "legacy32")
        id64 = self._add_artifact(repo, sample_file, "legacy64")

        args = argparse.Namespace(
            source="v1.0.0",
            legacy32=id32,
            legacy64=id64,
            patch="/nonexistent/file.patch",
        )
        rc = run(args, repo)
        assert rc == 1
