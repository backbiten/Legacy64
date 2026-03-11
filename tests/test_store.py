"""Tests for the store and quarantine (legacyai/store.py, legacyai/quarantine.py)."""

import hashlib
import json
from pathlib import Path

import pytest

from legacyai.store import Store, StoreError
from legacyai.quarantine import Quarantine


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path)
    s.init()
    return s


@pytest.fixture
def sample_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_bytes(b"hello Legacy64")
    return f


# ---------------------------------------------------------------------------
# Store: init
# ---------------------------------------------------------------------------


def test_store_init_creates_dirs(tmp_path):
    s = Store(tmp_path)
    s.init()
    assert (tmp_path / "objects").is_dir()
    assert (tmp_path / "artifacts").is_dir()
    assert (tmp_path / "reports").is_dir()
    assert (tmp_path / "quarantine" / "objects").is_dir()
    assert (tmp_path / "quarantine" / "records").is_dir()
    assert (tmp_path / ".legacy64").exists()


def test_store_init_idempotent(tmp_path):
    s = Store(tmp_path)
    s.init()
    s.init()  # Should not raise


# ---------------------------------------------------------------------------
# Store: find_root
# ---------------------------------------------------------------------------


def test_find_root_from_child(tmp_path):
    s = Store(tmp_path)
    s.init()
    child = tmp_path / "sub" / "dir"
    child.mkdir(parents=True)
    found = Store.find_root(child)
    assert found.root == tmp_path


def test_find_root_not_found(tmp_path):
    with pytest.raises(StoreError, match="Not inside a Legacy64 repository"):
        Store.find_root(tmp_path)


# ---------------------------------------------------------------------------
# Store: object storage
# ---------------------------------------------------------------------------


def test_store_object(store, sample_file):
    h = store.store_object(sample_file)
    assert h.startswith("sha256:")
    expected_hex = hashlib.sha256(b"hello Legacy64").hexdigest()
    assert h == f"sha256:{expected_hex}"


def test_store_object_idempotent(store, sample_file):
    h1 = store.store_object(sample_file)
    h2 = store.store_object(sample_file)
    assert h1 == h2


def test_object_path_exists(store, sample_file):
    h = store.store_object(sample_file)
    path = store.object_path(h)
    assert path.exists()
    assert path.read_bytes() == b"hello Legacy64"


def test_object_path_missing(store):
    with pytest.raises(StoreError, match="Object not found"):
        store.object_path("sha256:" + "a" * 64)


def test_object_path_bad_scheme(store):
    with pytest.raises(StoreError, match="Unsupported hash scheme"):
        store.object_path("md5:abc")


# ---------------------------------------------------------------------------
# Store: artifact records
# ---------------------------------------------------------------------------


def test_write_read_artifact(store):
    record = {
        "id": "test-art",
        "object_hash": "sha256:" + "a" * 64,
        "scan_status": "PASS",
        "added_at": "2026-01-01T00:00:00Z",
        "source_path": "/tmp/file.txt",
        "report_path": "",
    }
    store.write_artifact(record)
    loaded = store.read_artifact("test-art")
    assert loaded["id"] == "test-art"
    assert loaded["scan_status"] == "PASS"


def test_list_artifacts(store):
    for i in range(3):
        store.write_artifact(
            {
                "id": f"art-{i}",
                "object_hash": "sha256:" + str(i) * 64,
                "scan_status": "PASS",
                "added_at": "2026-01-01T00:00:00Z",
                "source_path": "",
                "report_path": "",
            }
        )
    ids = store.list_artifacts()
    assert ids == ["art-0", "art-1", "art-2"]


def test_read_artifact_missing(store):
    with pytest.raises(StoreError, match="Artifact not found"):
        store.read_artifact("nonexistent")


# ---------------------------------------------------------------------------
# Quarantine
# ---------------------------------------------------------------------------


def test_quarantine_add(store, sample_file):
    q = Quarantine(store)
    rec = q.quarantine(sample_file, "test-q", "Test reason")
    assert rec["id"] == "test-q"
    assert "test-q" in q.list_ids()


def test_quarantine_promote(store, sample_file):
    q = Quarantine(store)
    q.quarantine(sample_file, "test-promote", "Reason")
    artifact = q.promote("test-promote")
    assert artifact["id"] == "test-promote"
    # Now in normal store
    assert "test-promote" in store.list_artifacts()
    # Removed from quarantine
    assert "test-promote" not in q.list_ids()


def test_quarantine_reject(store, sample_file):
    q = Quarantine(store)
    q.quarantine(sample_file, "test-reject", "Reason")
    q.reject("test-reject")
    assert "test-reject" not in q.list_ids()


def test_quarantine_promote_missing(store):
    q = Quarantine(store)
    with pytest.raises(StoreError):
        q.promote("nonexistent")
