"""Integration tests for the legacyai CLI (legacyai/cli.py)."""

import json
import sys
from pathlib import Path

import pytest

from legacyai.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def repo(tmp_path):
    """Initialise a fresh Legacy64 repo in a temp directory."""
    assert main(["--repo", str(tmp_path), "init"]) == 0
    return tmp_path


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


def test_init_creates_layout(tmp_path):
    rc = main(["--repo", str(tmp_path), "init"])
    assert rc == 0
    assert (tmp_path / ".legacy64").exists()
    assert (tmp_path / "objects").is_dir()
    assert (tmp_path / "quarantine").is_dir()


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


def test_add_safe_file(repo):
    rc = main(["--repo", str(repo), "add", str(FIXTURES / "safe_text.txt"), "--id", "safe-1"])
    assert rc == 0
    assert (repo / "artifacts" / "safe-1.json").exists()


def test_add_no_scan(repo):
    rc = main(
        ["--repo", str(repo), "add", str(FIXTURES / "safe_text.txt"), "--id", "noscan-1", "--no-scan"]
    )
    assert rc == 0
    art = json.loads((repo / "artifacts" / "noscan-1.json").read_text())
    assert art["scan_status"] == "UNCHECKED"


def test_add_suspicious_quarantines(repo):
    """Adding the suspicious zip with --scan should quarantine it."""
    rc = main(["--repo", str(repo), "add", str(FIXTURES / "suspicious.zip"), "--id", "bad-zip"])
    # Should return non-zero (quarantined)
    assert rc != 0
    # Quarantine record should exist
    assert (repo / "quarantine" / "records" / "bad-zip.json").exists()
    # Should NOT be in normal artifacts
    assert not (repo / "artifacts" / "bad-zip.json").exists()


def test_add_missing_file(repo):
    rc = main(["--repo", str(repo), "add", "/nonexistent/file.bin", "--id", "ghost"])
    assert rc != 0


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------


def test_scan_existing_artifact(repo):
    main(["--repo", str(repo), "add", str(FIXTURES / "safe_text.txt"), "--id", "scan-me"])
    rc = main(["--repo", str(repo), "scan", "scan-me"])
    assert rc == 0
    report_path = repo / "reports" / "scan-me.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["decision"] in ("PASS", "WARN")


def test_scan_missing_artifact(repo):
    rc = main(["--repo", str(repo), "scan", "nonexistent"])
    assert rc != 0


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_empty(repo):
    rc = main(["--repo", str(repo), "list"])
    assert rc == 0


def test_list_shows_artifact(repo, capsys):
    main(["--repo", str(repo), "add", str(FIXTURES / "safe_text.txt"), "--id", "listed-1"])
    rc = main(["--repo", str(repo), "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "listed-1" in out


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


def test_export_safe_artifact(repo, tmp_path):
    main(["--repo", str(repo), "add", str(FIXTURES / "safe_text.txt"), "--id", "export-me"])
    dest = tmp_path / "exported.txt"
    rc = main(["--repo", str(repo), "export", "export-me", str(dest)])
    assert rc == 0
    assert dest.exists()
    assert dest.read_bytes() == (FIXTURES / "safe_text.txt").read_bytes()


def test_export_no_rescan(repo, tmp_path):
    main(["--repo", str(repo), "add", str(FIXTURES / "safe_text.txt"), "--id", "exp2"])
    dest = tmp_path / "exported2.txt"
    rc = main(["--repo", str(repo), "export", "exp2", str(dest), "--no-rescan"])
    assert rc == 0


def test_export_missing_artifact(repo, tmp_path):
    rc = main(["--repo", str(repo), "export", "nonexistent", str(tmp_path / "out.bin")])
    assert rc != 0


# ---------------------------------------------------------------------------
# quarantine subcommands
# ---------------------------------------------------------------------------


def test_quarantine_list_empty(repo, capsys):
    rc = main(["--repo", str(repo), "quarantine", "list"])
    assert rc == 0


def test_quarantine_full_flow(repo):
    # Add suspicious file (gets quarantined)
    main(["--repo", str(repo), "add", str(FIXTURES / "suspicious.zip"), "--id", "q-test"])

    # List quarantine
    rc = main(["--repo", str(repo), "quarantine", "list"])
    assert rc == 0

    # Promote
    rc = main(["--repo", str(repo), "quarantine", "promote", "q-test"])
    assert rc == 0
    assert (repo / "artifacts" / "q-test.json").exists()

    # Should no longer be quarantined
    rc = main(["--repo", str(repo), "quarantine", "promote", "q-test"])
    assert rc != 0  # Already promoted


def test_quarantine_reject(repo):
    main(["--repo", str(repo), "add", str(FIXTURES / "suspicious.zip"), "--id", "q-reject"])
    rc = main(["--repo", str(repo), "quarantine", "reject", "q-reject"])
    assert rc == 0
    # Should no longer be in quarantine
    assert not (repo / "quarantine" / "records" / "q-reject.json").exists()
