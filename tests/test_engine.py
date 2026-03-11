"""Tests for the scan engine (legacyai/scanner/engine.py)."""

import json
from pathlib import Path

import pytest

from legacyai.scanner.engine import ScanEngine

FIXTURES = Path(__file__).parent / "fixtures"


def test_engine_safe_text():
    engine = ScanEngine()
    report = engine.scan(FIXTURES / "safe_text.txt", artifact_id="test-safe")
    assert report.artifact_id == "test-safe"
    assert report.decision in ("PASS", "WARN")
    assert report.qc_status == "PASS"
    assert report.schema_version == "1.0"


def test_engine_elf_stub():
    engine = ScanEngine()
    report = engine.scan(FIXTURES / "elf_stub.bin", artifact_id="test-elf")
    # ELF triggers QA-001 WARN → decision WARN or FAIL (not PASS)
    assert report.decision in ("WARN", "FAIL")
    assert report.qc_status == "PASS"
    assert any(c["rule_id"] == "QA-001" for c in report.qa_findings)


def test_engine_suspicious_zip():
    engine = ScanEngine()
    report = engine.scan(FIXTURES / "suspicious.zip", artifact_id="test-zip")
    assert report.decision == "FAIL"
    assert report.qa_status == "FAIL"


def test_engine_to_dict():
    engine = ScanEngine()
    report = engine.scan(FIXTURES / "safe_text.txt")
    d = report.to_dict()
    assert "qc" in d
    assert "qa" in d
    assert "decision" in d
    assert d["schema_version"] == "1.0"


def test_engine_to_json():
    engine = ScanEngine()
    report = engine.scan(FIXTURES / "safe_text.txt")
    raw = report.to_json()
    parsed = json.loads(raw)
    assert parsed["decision"] in ("PASS", "WARN", "FAIL")


def test_engine_hash_verification(tmp_path):
    import hashlib
    f = tmp_path / "data.txt"
    data = b"integrity test"
    f.write_bytes(data)
    correct_hash = "sha256:" + hashlib.sha256(data).hexdigest()
    wrong_hash = "sha256:" + "0" * 64

    engine = ScanEngine()
    report_ok = engine.scan(f, expected_hash=correct_hash)
    assert report_ok.qc_status == "PASS"

    report_bad = engine.scan(f, expected_hash=wrong_hash)
    assert report_bad.qc_status == "FAIL"
    assert report_bad.decision == "FAIL"


def test_engine_missing_file(tmp_path):
    engine = ScanEngine()
    report = engine.scan(tmp_path / "ghost.bin")
    assert report.qc_status == "FAIL"
    assert report.decision == "FAIL"
