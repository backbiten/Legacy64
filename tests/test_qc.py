"""Tests for QC rules (legacyai/scanner/qc.py)."""

import hashlib
from pathlib import Path

import pytest

from legacyai.scanner.qc import (
    check_file_readable,
    check_hash_matches,
    check_file_size,
    check_file_type,
    detect_file_type,
    run_qc_checks,
    qc_status,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# QC-001: File readable
# ---------------------------------------------------------------------------


def test_qc001_readable(tmp_path):
    f = tmp_path / "test.txt"
    f.write_bytes(b"hello")
    result = check_file_readable(f)
    assert result.status == "PASS"
    assert result.check_id == "QC-001"


def test_qc001_missing(tmp_path):
    result = check_file_readable(tmp_path / "nonexistent.txt")
    assert result.status == "FAIL"


# ---------------------------------------------------------------------------
# QC-002: Hash integrity
# ---------------------------------------------------------------------------


def test_qc002_correct_hash(tmp_path):
    f = tmp_path / "data.bin"
    data = b"hello world"
    f.write_bytes(data)
    expected = "sha256:" + hashlib.sha256(data).hexdigest()
    result = check_hash_matches(f, expected)
    assert result.status == "PASS"
    assert result.check_id == "QC-002"


def test_qc002_wrong_hash(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"hello")
    result = check_hash_matches(f, "sha256:" + "a" * 64)
    assert result.status == "FAIL"


def test_qc002_no_hash(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    result = check_hash_matches(f, None)
    assert result.status == "PASS"  # skipped — no expected hash


def test_qc002_bad_scheme(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    result = check_hash_matches(f, "md5:abc123")
    assert result.status == "FAIL"


# ---------------------------------------------------------------------------
# QC-003: File size
# ---------------------------------------------------------------------------


def test_qc003_normal_file(tmp_path):
    f = tmp_path / "file.txt"
    f.write_bytes(b"content")
    result = check_file_size(f)
    assert result.status == "PASS"


def test_qc003_empty_file(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    result = check_file_size(f)
    assert result.status == "FAIL"
    assert "0 bytes" in result.details


# ---------------------------------------------------------------------------
# QC-004: File type detection
# ---------------------------------------------------------------------------


def test_qc004_elf(tmp_path):
    f = tmp_path / "prog.elf"
    f.write_bytes(b"\x7fELF" + b"\x00" * 60)
    result = check_file_type(f)
    assert result.status == "PASS"
    assert "ELF" in result.details


def test_qc004_zip():
    result = check_file_type(FIXTURES / "suspicious.zip")
    assert result.status == "PASS"
    assert "ZIP" in result.details


def test_qc004_text():
    result = check_file_type(FIXTURES / "safe_text.txt")
    assert result.status == "PASS"
    assert "text" in result.details.lower()


def test_detect_file_type_elf_fixture():
    t = detect_file_type(FIXTURES / "elf_stub.bin")
    assert t == "ELF executable"


def test_detect_file_type_zip_fixture():
    t = detect_file_type(FIXTURES / "suspicious.zip")
    assert t == "ZIP archive"


# ---------------------------------------------------------------------------
# run_qc_checks aggregation
# ---------------------------------------------------------------------------


def test_run_qc_checks_all_pass(tmp_path):
    f = tmp_path / "data.txt"
    f.write_bytes(b"hello")
    results = run_qc_checks(f)
    assert len(results) == 4
    assert qc_status(results) == "PASS"


def test_run_qc_checks_fail_on_empty(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    results = run_qc_checks(f)
    assert qc_status(results) == "FAIL"


def test_run_qc_checks_fail_on_missing(tmp_path):
    results = run_qc_checks(tmp_path / "ghost.bin")
    assert qc_status(results) == "FAIL"
