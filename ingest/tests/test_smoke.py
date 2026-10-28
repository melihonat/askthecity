"""smoke_failures: what blocks `swap`, judged from staging stats against the build files."""
import pytest

from ingest import config, db
from ingest.store import ManifestRow


def row(ref: str, sha: str) -> ManifestRow:
    return ManifestRow(sha256=sha, kind="code_chapter", ref=ref, parent_ref="", source_url="",
                       obtained_by="script", obtained_at="2026-10-28T09:00:00Z", last_modified="",
                       etag="", bytes=1, content_type="application/pdf", encoding="")


MANIFEST = [row("ch-1", "a1"), row("ch-2", "b2"), row("ch-9", "c9")]
SKIPPED = ["ch-9"]                                    # a "Reserved" stub
CHUNKS = [{"id": f"tmc:1-{i}"} for i in range(100)]


@pytest.fixture
def stats(monkeypatch):
    monkeypatch.setattr(db, "PINS", {"1-2": ["tmc:1-2"]})
    return {"snapshots": 1, "chunker_version": config.CHUNKER_VERSION, "chunks": 100,
            "without_embedding": 0, "replacement_char": 0, "replacement_ids": [],
            "shas_with_chunks": {"a1", "b2"}, "pins": {"1-2": ["tmc:1-2"]}}


def failures(stats):
    return db.smoke_failures(stats, CHUNKS, MANIFEST, SKIPPED)


def test_a_complete_staging_passes(stats):
    assert failures(stats) == []


def test_wrong_chunk_count_fails(stats):
    assert failures({**stats, "chunks": 111}) == ["111 chunks in staging, build/chunks.jsonl has 100 (±10%)"]
    assert failures({**stats, "chunks": 95}) == []


def test_missing_embeddings_fail(stats):
    assert failures({**stats, "without_embedding": 3}) == ["3 chunks without an embedding"]


def test_any_replacement_character_fails(stats):
    [msg] = failures({**stats, "replacement_char": 1, "replacement_ids": ["tmc:1-7"]})
    assert "U+FFFD" in msg and "tmc:1-7" in msg


def test_a_manifest_file_without_chunks_fails_unless_skipped(stats):
    assert failures({**stats, "shas_with_chunks": {"a1"}}) == ["1 manifest files produced no chunk: ['ch-2']"]


def test_snapshot_row_and_chunker_version_are_checked(stats):
    assert failures({**stats, "snapshots": 0}) == ["0 snapshot rows, expected 1"]
    assert failures({**stats, "chunker_version": "code-basic-1"}) == [
        f"chunker_version 'code-basic-1', expected {config.CHUNKER_VERSION!r}"]


def test_a_pin_returning_other_chunk_ids_fails(stats):
    assert failures({**stats, "pins": {"1-2": ["tmc:1-2:A", "tmc:1-2:B"]}}) == [
        "pin § 1-2: ['tmc:1-2:A', 'tmc:1-2:B'], expected ['tmc:1-2']"]
