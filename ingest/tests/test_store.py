"""restore against an in-memory R2 stand-in."""
import hashlib
import io

import pytest

from ingest import config, store


class FakeR2:
    def __init__(self, objects: dict[str, bytes]):
        self.objects = objects

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}


def row(ref: str, data: bytes) -> store.ManifestRow:
    return store.ManifestRow(sha256=hashlib.sha256(data).hexdigest(), kind="code_chapter", ref=ref,
                             parent_ref="", source_url=f"https://example.test/{ref}.pdf", obtained_by="script",
                             obtained_at="2026-10-28T09:00:00Z", last_modified="", etag="", bytes=len(data),
                             content_type="application/pdf", encoding="")


@pytest.fixture
def snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "CORPUS", tmp_path / "corpus")
    monkeypatch.setattr(config, "MANIFEST", tmp_path / "snapshot" / "manifest.csv")
    rows = [row("ch-1", b"%PDF one"), row("ch-2", b"%PDF two")]
    store.write_manifest(rows)
    return rows


def test_restore_reproduces_corpus_on_a_clean_directory(snapshot):
    r2 = FakeR2({r.key: data for r, data in zip(snapshot, [b"%PDF one", b"%PDF two"])})
    store.restore(r2, "bucket")
    assert (config.CORPUS / "code_chapter" / "ch-1.pdf").read_bytes() == b"%PDF one"
    assert (config.CORPUS / "code_chapter" / "ch-2.pdf").read_bytes() == b"%PDF two"


def test_restore_fails_loudly_on_a_sha256_mismatch_and_never_writes_the_bad_file(snapshot):
    r2 = FakeR2({snapshot[0].key: b"%PDF one", snapshot[1].key: b"%PDF tampered"})
    with pytest.raises(SystemExit, match=r"(?s)sha256 mismatch for 1 of 2 files.*ch-2"):
        store.restore(r2, "bucket")
    assert not (config.CORPUS / "code_chapter" / "ch-2.pdf").exists()
