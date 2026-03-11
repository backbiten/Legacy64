"""Tests for QA rules (legacyai/scanner/qa.py)."""

import io
import zipfile
from pathlib import Path

import pytest

from legacyai.scanner.qa import (
    run_qa_checks,
    qa_status,
    _rule_elf,
    _rule_pe,
    _rule_shebang,
    _rule_zip,
    _rule_tar,
    _rule_entropy,
    _rule_secrets,
    _rule_embedded_exec,
    _shannon_entropy,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Shannon entropy helper
# ---------------------------------------------------------------------------


def test_entropy_uniform():
    """All same bytes = 0 entropy."""
    assert _shannon_entropy(b"\x00" * 100) == 0.0


def test_entropy_random():
    """Random-ish data should have high entropy."""
    import os
    data = os.urandom(4096)
    assert _shannon_entropy(data) > 6.0


# ---------------------------------------------------------------------------
# QA-001 ELF
# ---------------------------------------------------------------------------


def test_qa001_elf_fixture():
    findings = _rule_elf(FIXTURES / "elf_stub.bin")
    assert len(findings) == 1
    assert findings[0].rule_id == "QA-001"
    assert findings[0].severity == "WARN"


def test_qa001_no_elf(tmp_path):
    f = tmp_path / "safe.txt"
    f.write_bytes(b"hello world")
    findings = _rule_elf(f)
    assert findings == []


# ---------------------------------------------------------------------------
# QA-002 PE
# ---------------------------------------------------------------------------


def test_qa002_pe(tmp_path):
    f = tmp_path / "prog.exe"
    f.write_bytes(b"MZ" + b"\x00" * 100)
    findings = _rule_pe(f)
    assert len(findings) == 1
    assert findings[0].rule_id == "QA-002"


def test_qa002_no_pe(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"PK\x03\x04")
    assert _rule_pe(f) == []


# ---------------------------------------------------------------------------
# QA-004 Shebang
# ---------------------------------------------------------------------------


def test_qa004_shebang(tmp_path):
    f = tmp_path / "script.sh"
    f.write_bytes(b"#!/bin/bash\necho hello\n")
    findings = _rule_shebang(f)
    assert len(findings) == 1
    assert findings[0].rule_id == "QA-004"
    assert "bash" in findings[0].details


def test_qa004_no_shebang(tmp_path):
    f = tmp_path / "plain.txt"
    f.write_bytes(b"# comment\necho hello\n")
    assert _rule_shebang(f) == []


# ---------------------------------------------------------------------------
# QA-005 ZIP inspection
# ---------------------------------------------------------------------------


def test_qa005_autorun(tmp_path):
    f = tmp_path / "bad.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("autorun.inf", "[AutoRun]")
    f.write_bytes(buf.getvalue())
    findings = _rule_zip(f)
    rule_ids = [ff.rule_id for ff in findings]
    assert "QA-005" in rule_ids
    fail_findings = [ff for ff in findings if ff.severity == "FAIL"]
    assert any("autorun.inf" in ff.details for ff in fail_findings)


def test_qa005_double_extension(tmp_path):
    f = tmp_path / "tricky.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("document.pdf.exe", "MZ fake")
    f.write_bytes(buf.getvalue())
    findings = _rule_zip(f)
    assert any("pdf.exe" in ff.details for ff in findings)


def test_qa005_lnk_extension(tmp_path):
    f = tmp_path / "lnk.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("shortcut.lnk", "fake lnk data")
    f.write_bytes(buf.getvalue())
    findings = _rule_zip(f)
    assert any(".lnk" in ff.details for ff in findings)


def test_qa005_clean_zip(tmp_path):
    f = tmp_path / "clean.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "All good.")
    f.write_bytes(buf.getvalue())
    findings = _rule_zip(f)
    # Clean zip should have no FAIL or WARN findings
    bad = [ff for ff in findings if ff.severity in ("FAIL", "WARN")]
    assert bad == []


def test_qa005_fixture():
    """The suspicious.zip fixture should trigger multiple QA-005 findings."""
    findings = _rule_zip(FIXTURES / "suspicious.zip")
    assert len(findings) >= 2  # autorun.inf + double extension


def test_qa005_non_zip(tmp_path):
    f = tmp_path / "plain.txt"
    f.write_bytes(b"not a zip file")
    assert _rule_zip(f) == []


# ---------------------------------------------------------------------------
# QA-007 High entropy
# ---------------------------------------------------------------------------


def test_qa007_high_entropy(tmp_path):
    import os
    f = tmp_path / "random.bin"
    f.write_bytes(os.urandom(8192))
    findings = _rule_entropy(f)
    assert any(ff.rule_id == "QA-007" and "entropy" in ff.name.lower() for ff in findings)


def test_qa007_low_entropy(tmp_path):
    f = tmp_path / "zeros.bin"
    f.write_bytes(b"\x00" * 8192)
    findings = _rule_entropy(f)
    assert not any("entropy" in ff.name.lower() for ff in findings)


def test_qa007_base64_blob(tmp_path):
    import base64
    payload = base64.b64encode(b"A" * 300)
    f = tmp_path / "script.sh"
    f.write_bytes(b"#!/bin/sh\nDATA=" + payload + b"\n")
    findings = _rule_entropy(f)
    assert any("base64" in ff.name.lower() for ff in findings)


# ---------------------------------------------------------------------------
# QA-009 Secrets
# ---------------------------------------------------------------------------


def test_qa009_aws_key(tmp_path):
    f = tmp_path / "config.sh"
    f.write_bytes(b"export AWS_KEY=AKIAIOSFODNN7EXAMPLE\n")
    findings = _rule_secrets(f)
    assert any(ff.rule_id == "QA-009" for ff in findings)
    assert any("AWS" in ff.name for ff in findings)


def test_qa009_pem_key(tmp_path):
    f = tmp_path / "key.pem"
    f.write_bytes(b"-----BEGIN RSA PRIVATE KEY-----\nABC123\n-----END RSA PRIVATE KEY-----\n")
    findings = _rule_secrets(f)
    assert any("PEM" in ff.name or "private" in ff.name.lower() for ff in findings)


def test_qa009_clean_file(tmp_path):
    f = tmp_path / "clean.txt"
    f.write_bytes(b"Just a normal file with nothing suspicious.\n")
    findings = _rule_secrets(f)
    assert findings == []


def test_qa009_secrets_fixture():
    findings = _rule_secrets(FIXTURES / "secrets_script.sh")
    assert any(ff.rule_id == "QA-009" for ff in findings)


# ---------------------------------------------------------------------------
# QA-008 Embedded executable
# ---------------------------------------------------------------------------


def test_qa008_embedded_elf_in_text(tmp_path):
    f = tmp_path / "tricky.txt"
    # Embed ELF magic after some text bytes
    f.write_bytes(b"normal text\n" + b"\x7fELF" + b"\x00" * 60)
    findings = _rule_embedded_exec(f)
    assert any(ff.rule_id == "QA-008" for ff in findings)


def test_qa008_clean_elf_file(tmp_path):
    """ELF file itself should NOT trigger QA-008 (QA-001 covers that)."""
    f = tmp_path / "prog"
    f.write_bytes(b"\x7fELF" + b"\x00" * 60)
    findings = _rule_embedded_exec(f)
    assert findings == []


# ---------------------------------------------------------------------------
# Full run_qa_checks / qa_status integration
# ---------------------------------------------------------------------------


def test_run_qa_checks_safe_text():
    findings = run_qa_checks(FIXTURES / "safe_text.txt")
    assert qa_status(findings) == "PASS"


def test_run_qa_checks_elf():
    findings = run_qa_checks(FIXTURES / "elf_stub.bin")
    status = qa_status(findings)
    assert status in ("WARN", "FAIL")


def test_run_qa_checks_suspicious_zip():
    findings = run_qa_checks(FIXTURES / "suspicious.zip")
    status = qa_status(findings)
    assert status == "FAIL"  # autorun.inf triggers FAIL


def test_qa_status_empty():
    assert qa_status([]) == "PASS"
