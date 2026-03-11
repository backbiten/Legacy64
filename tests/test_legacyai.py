"""Tests for legacyai – patch, patchset, bind, verify, and CLI."""

import hashlib
import textwrap
from pathlib import Path

import pytest
import yaml

from legacyai.store import compute_sha256, compute_sha256_bytes
from legacyai.patch import add_patch, list_patches, load_patch
from legacyai.patchset import (
    create_patchset,
    add_patch_to_patchset,
    list_patchsets,
    load_patchset,
)
from legacyai.bind import bind_source_patch, list_bindings
from legacyai.verify import verify
from legacyai.cli import main


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def repo(tmp_path):
    """Minimal archive root with required sub-directories."""
    (tmp_path / "patches").mkdir()
    (tmp_path / "patchsets" / "y2038").mkdir(parents=True)
    (tmp_path / "bindings" / "source-patch").mkdir(parents=True)
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "objects").mkdir()
    return tmp_path


@pytest.fixture()
def patch_file(tmp_path):
    """A small synthetic unified diff file."""
    content = textwrap.dedent("""\
        --- a/src/time.c
        +++ b/src/time.c
        @@ -10,7 +10,7 @@
        -typedef int time_t;
        +typedef long long time_t;
    """).encode()
    p = tmp_path / "fix-time_t.patch"
    p.write_bytes(content)
    return p


# ---------------------------------------------------------------------------
# store helpers
# ---------------------------------------------------------------------------

def test_compute_sha256(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_bytes(b"hello world")
    assert compute_sha256(f) == hashlib.sha256(b"hello world").hexdigest()


def test_compute_sha256_bytes():
    assert compute_sha256_bytes(b"abc") == hashlib.sha256(b"abc").hexdigest()


# ---------------------------------------------------------------------------
# patch
# ---------------------------------------------------------------------------

def test_add_patch_creates_files(repo, patch_file):
    record = add_patch(repo, patch_file, tags=["y2038"], name="Fix time_t")
    sha = record["id"]

    assert (repo / "patches" / f"{sha}.patch").exists()
    assert (repo / "patches" / f"{sha}.yml").exists()


def test_add_patch_record_fields(repo, patch_file):
    record = add_patch(repo, patch_file, tags=["y2038"])
    assert record["tags"] == ["y2038"]
    assert record["hash"] == record["id"]
    assert record["file"].startswith("patches/")
    assert "added_at" in record


def test_add_patch_idempotent(repo, patch_file):
    r1 = add_patch(repo, patch_file)
    r2 = add_patch(repo, patch_file)
    assert r1["id"] == r2["id"]
    # Only one patch file should exist
    assert len(list((repo / "patches").glob("*.patch"))) == 1


def test_list_patches(repo, patch_file):
    add_patch(repo, patch_file)
    records = list_patches(repo)
    assert len(records) == 1


def test_list_patches_empty(repo):
    assert list_patches(repo) == []


def test_load_patch_by_prefix(repo, patch_file):
    record = add_patch(repo, patch_file)
    loaded = load_patch(repo, record["id"][:8])
    assert loaded["id"] == record["id"]


def test_load_patch_not_found(repo):
    with pytest.raises(FileNotFoundError):
        load_patch(repo, "deadbeef")


# ---------------------------------------------------------------------------
# patchset
# ---------------------------------------------------------------------------

def test_create_patchset(repo):
    record = create_patchset(repo, "y2038:fix-libc", description="Test patchset")
    assert record["id"] == "y2038:fix-libc"
    assert record["namespace"] == "y2038"
    assert record["name"] == "fix-libc"
    assert "y2038" in record["tags"]
    meta_file = repo / "patchsets" / "y2038" / "fix-libc.yml"
    assert meta_file.exists()


def test_create_patchset_duplicate_raises(repo):
    create_patchset(repo, "y2038:fix-libc")
    with pytest.raises(FileExistsError):
        create_patchset(repo, "y2038:fix-libc")


def test_add_patch_to_patchset(repo, patch_file):
    patch_record = add_patch(repo, patch_file, tags=["y2038"])
    create_patchset(repo, "y2038:my-series")
    updated = add_patch_to_patchset(
        repo, "y2038:my-series", patch_record["id"], order=1, note="first patch"
    )
    assert len(updated["patches"]) == 1
    assert updated["patches"][0]["patch_id"] == patch_record["id"]
    assert updated["patches"][0]["order"] == 1
    assert updated["patches"][0]["note"] == "first patch"


def test_add_patches_ordered(repo, patch_file, tmp_path):
    p2_content = b"--- a/foo\n+++ b/foo\n@@ -1 +1 @@\n-old\n+new\n"
    p2 = tmp_path / "second.patch"
    p2.write_bytes(p2_content)

    r1 = add_patch(repo, patch_file)
    r2 = add_patch(repo, p2)
    create_patchset(repo, "y2038:ordered")
    add_patch_to_patchset(repo, "y2038:ordered", r2["id"], order=2)
    add_patch_to_patchset(repo, "y2038:ordered", r1["id"], order=1)

    pset = load_patchset(repo, "y2038:ordered")
    assert pset["patches"][0]["patch_id"] == r1["id"]
    assert pset["patches"][1]["patch_id"] == r2["id"]


def test_add_patch_to_patchset_not_found(repo):
    with pytest.raises(FileNotFoundError):
        add_patch_to_patchset(repo, "y2038:nonexistent", "abc", order=1)


def test_list_patchsets(repo):
    create_patchset(repo, "y2038:alpha")
    create_patchset(repo, "y2038:beta")
    records = list_patchsets(repo)
    ids = [r["id"] for r in records]
    assert "y2038:alpha" in ids
    assert "y2038:beta" in ids


def test_patchset_with_baseline(repo):
    record = create_patchset(
        repo,
        "y2038:with-baseline",
        baseline_artifact_id="libc-src-1.0",
        expected_source_hash="a" * 64,
    )
    assert record["baseline_artifact_id"] == "libc-src-1.0"
    assert record["expected_source_hash"] == "a" * 64


# ---------------------------------------------------------------------------
# bind
# ---------------------------------------------------------------------------

def test_bind_source_patch(repo, patch_file):
    patch_record = add_patch(repo, patch_file, tags=["y2038"])
    binding = bind_source_patch(
        repo,
        source_artifact_id="libc-src-1.0",
        tags=["y2038"],
        patchset_id="y2038:fix-libc",
        patch_ids=[patch_record["id"]],
    )
    assert binding["type"] == "source-patch"
    assert binding["source_artifact_id"] == "libc-src-1.0"
    assert "y2038" in binding["tags"]
    assert binding["patchset_id"] == "y2038:fix-libc"
    binding_file = repo / "bindings" / "source-patch" / f"{binding['id']}.yml"
    assert binding_file.exists()


def test_list_bindings(repo):
    bind_source_patch(repo, source_artifact_id="art-1", tags=["y2038"])
    bind_source_patch(repo, source_artifact_id="art-2")
    records = list_bindings(repo)
    assert len(records) == 2


# ---------------------------------------------------------------------------
# verify – clean archive
# ---------------------------------------------------------------------------

def test_verify_empty_archive(repo):
    errors, checked, ok = verify(repo)
    assert errors == []
    assert checked == 0


def test_verify_clean(repo, patch_file):
    record = add_patch(repo, patch_file, tags=["y2038"])
    create_patchset(repo, "y2038:clean-series")
    add_patch_to_patchset(repo, "y2038:clean-series", record["id"], order=1)

    errors, checked, ok = verify(repo)
    assert not errors, f"Unexpected errors: {[str(e) for e in errors]}"


def test_verify_missing_patch_file(repo, patch_file):
    record = add_patch(repo, patch_file)
    # Delete the actual patch file to simulate corruption
    (repo / record["file"]).unlink()

    errors, checked, ok = verify(repo)
    assert any("missing" in str(e).lower() for e in errors)


def test_verify_hash_mismatch(repo, patch_file):
    record = add_patch(repo, patch_file)
    # Corrupt the patch file
    patch_path = repo / record["file"]
    patch_path.write_bytes(b"tampered content")

    errors, checked, ok = verify(repo)
    assert any("mismatch" in str(e).lower() for e in errors)


def test_verify_missing_patch_in_patchset(repo, patch_file):
    record = add_patch(repo, patch_file)
    create_patchset(repo, "y2038:broken")

    # Manually inject a reference to a non-existent patch
    ps_file = repo / "patchsets" / "y2038" / "broken.yml"
    with open(ps_file, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    data["patches"] = [{"order": 1, "patch_id": "nonexistent" * 4}]
    with open(ps_file, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False)

    errors, checked, ok = verify(repo)
    assert any("not found" in str(e).lower() for e in errors)


def test_verify_missing_baseline_artifact(repo):
    create_patchset(
        repo, "y2038:needs-artifact", baseline_artifact_id="missing-artifact"
    )
    errors, _, _ = verify(repo)
    assert any("missing-artifact" in str(e) for e in errors)


def test_verify_binding_references_missing_patchset(repo):
    bind_source_patch(
        repo,
        source_artifact_id="art",
        patchset_id="y2038:does-not-exist",
    )
    errors, _, _ = verify(repo)
    assert any("does-not-exist" in str(e) for e in errors)


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

def test_cli_patch_add(repo, patch_file):
    rc = main(["--root", str(repo), "patch", "add", str(patch_file), "--tag", "y2038"])
    assert rc == 0
    patches = list((repo / "patches").glob("*.patch"))
    assert len(patches) == 1


def test_cli_patch_add_missing_file(repo):
    rc = main(["--root", str(repo), "patch", "add", "/nonexistent/file.patch"])
    assert rc == 1


def test_cli_patch_list(repo, patch_file, capsys):
    add_patch(repo, patch_file, tags=["y2038"], name="my-patch")
    rc = main(["--root", str(repo), "patch", "list"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "my-patch" in captured.out


def test_cli_patchset_create(repo):
    rc = main(
        [
            "--root", str(repo),
            "patchset", "create", "y2038:cli-test",
            "--description", "Created via CLI",
        ]
    )
    assert rc == 0
    assert (repo / "patchsets" / "y2038" / "cli-test.yml").exists()


def test_cli_patchset_create_duplicate(repo):
    main(["--root", str(repo), "patchset", "create", "y2038:dup"])
    rc = main(["--root", str(repo), "patchset", "create", "y2038:dup"])
    assert rc == 1


def test_cli_patchset_add_and_show(repo, patch_file, capsys):
    patch_record = add_patch(repo, patch_file)
    main(["--root", str(repo), "patchset", "create", "y2038:show-test"])
    rc = main(
        [
            "--root", str(repo),
            "patchset", "add", "y2038:show-test",
            "--patch", patch_record["id"],
            "--order", "1",
        ]
    )
    assert rc == 0

    rc2 = main(["--root", str(repo), "patchset", "show", "y2038:show-test"])
    assert rc2 == 0
    captured = capsys.readouterr()
    assert "show-test" in captured.out


def test_cli_patchset_list(repo, capsys):
    create_patchset(repo, "y2038:list-a")
    create_patchset(repo, "y2038:list-b")
    rc = main(["--root", str(repo), "patchset", "list"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "y2038:list-a" in captured.out
    assert "y2038:list-b" in captured.out


def test_cli_bind_source_patch(repo):
    rc = main(
        [
            "--root", str(repo),
            "bind", "source-patch",
            "--source", "libc-src-1.0",
            "--tag", "y2038",
        ]
    )
    assert rc == 0
    bindings = list((repo / "bindings" / "source-patch").glob("*.yml"))
    assert len(bindings) == 1


def test_cli_verify_clean(repo, patch_file, capsys):
    add_patch(repo, patch_file, tags=["y2038"])
    rc = main(["--root", str(repo), "verify"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "0 error" in captured.out


def test_cli_verify_error(repo, patch_file, capsys):
    record = add_patch(repo, patch_file)
    (repo / record["file"]).write_bytes(b"tampered")
    rc = main(["--root", str(repo), "verify"])
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.out.lower()
