"""load: build/ → the staging schema. smoke: check staging. swap: staging → live, in one transaction."""
from __future__ import annotations

import hashlib
import json
from datetime import date

import psycopg

from . import config, store

SCHEMA_SQL = config.ROOT / "db" / "schema.sql"
TABLES = ["snapshot", "documents", "chunks", "amendments"]   # parent → child
CHUNK_COLUMNS = ["id", "document_id", "family", "kind", "section", "subsection_range", "stage",
                 "heading", "breadcrumb", "body", "label", "sublabel", "href", "amended_since",
                 "page_start", "page_end", "tokens", "embedding"]
DOCUMENT_COLUMNS = ["id", "kind", "family", "title", "source_url", "sha256", "fetched_at",
                    "consolidated_as_of", "enacted", "in_force", "item_id", "status_stamp",
                    "decision_date", "bylaws"]


def connect() -> psycopg.Connection:
    return psycopg.connect(config.env("DATABASE_URL"))


def apply_schema(conn: psycopg.Connection) -> None:
    template = SCHEMA_SQL.read_text(encoding="utf-8")
    for schema in ("public", "staging"):
        conn.execute(template.replace("{schema}", schema))


def _jsonl(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def load() -> None:
    documents, chunks = _jsonl(config.DOCUMENTS), _jsonl(config.CHUNKS)
    embeddings = {e["chunk_id"]: e for e in _jsonl(config.EMBEDDINGS)}

    models = {(e["model"], e["dim"]) for e in embeddings.values()}
    if models != {(config.EMBED_MODEL, config.EMBED_DIM)}:
        raise SystemExit(f"refusing to load mixed or unexpected embeddings: {sorted(models)}; "
                         f"expected {config.EMBED_MODEL}/{config.EMBED_DIM}")
    if missing := [c["id"] for c in chunks if c["id"] not in embeddings]:
        raise SystemExit(f"{len(missing)} chunks have no embedding (run `embed`): {missing[:5]}")

    fetched = [r.obtained_at[:10] for r in store.read_manifest() if r.obtained_by == "script"]
    snapshot_date = date.fromisoformat(min(fetched))
    digest = hashlib.sha256(config.CHUNKS.read_bytes() + config.EMBED_MODEL.encode()).hexdigest()[:8]
    snapshot = {
        "id": f"{snapshot_date.isoformat()}-{digest}",
        "snapshot_date": snapshot_date,
        "embed_model": config.EMBED_MODEL,
        "embed_dim": config.EMBED_DIM,
        "scope_sentence": config.SCOPE_SENTENCE.format(
            date=f"{snapshot_date:%B} {snapshot_date.day}, {snapshot_date.year}"),
        "chunker_version": config.CHUNKER_VERSION,
    }

    with connect() as conn:
        apply_schema(conn)
        conn.execute("truncate " + ", ".join(f"staging.{t}" for t in TABLES))
        conn.execute("insert into staging.snapshot (id, snapshot_date, embed_model, embed_dim, "
                     "scope_sentence, chunker_version) values (%(id)s, %(snapshot_date)s, "
                     "%(embed_model)s, %(embed_dim)s, %(scope_sentence)s, %(chunker_version)s)",
                     snapshot)
        with conn.cursor() as cur:
            cur.executemany(
                f"insert into staging.documents ({', '.join(DOCUMENT_COLUMNS)}) "
                f"values ({', '.join('%s' for _ in DOCUMENT_COLUMNS)})",
                [[d[k] for k in DOCUMENT_COLUMNS] for d in documents])
            cur.executemany(
                f"insert into staging.chunks ({', '.join(CHUNK_COLUMNS)}) "
                f"values ({', '.join('%s' for _ in CHUNK_COLUMNS[:-1])}, %s::extensions.halfvec)",
                [[c[k] for k in CHUNK_COLUMNS[:-1]] + [json.dumps(embeddings[c["id"]]["embedding"])]
                 for c in chunks])
    print(f"staging: snapshot {snapshot['id']}, {len(documents)} documents, {len(chunks)} chunks")


REPLACEMENT_CHAR = chr(0xFFFD)   # a windows-1252 decode gone wrong

# Fixed § lookups: every chunk id of the § must be in staging, and no others.
PINS = {
    "591-2.6": ["tmc:591-2.6"],
    "591-1.1": ["tmc:591-1.1:ambient-sound-level", "tmc:591-1.1:living-area", "tmc:591-1.1:unreasonable-noise"],
    "681-4": ["tmc:681-4:A-I", "tmc:681-4:J", "tmc:681-4:Jp2", "tmc:681-4:K"],
    "681-5": ["tmc:681-5:A-G", "tmc:681-5:H-L"],
    "349-1": ["tmc:349-1:animal", "tmc:349-1:guard-dog"],
}


def smoke_failures(stats: dict, chunks: list[dict], manifest: list[store.ManifestRow],
                   skipped: list[str]) -> list[str]:
    """Pure: what staging (`stats`) gets wrong against the build files. Empty means pass."""
    fail = []
    if stats["snapshots"] != 1:
        fail.append(f"{stats['snapshots']} snapshot rows, expected 1")
    elif stats["chunker_version"] != config.CHUNKER_VERSION:
        fail.append(f"chunker_version {stats['chunker_version']!r}, expected {config.CHUNKER_VERSION!r}")
    if abs(stats["chunks"] - len(chunks)) > 0.1 * len(chunks):
        fail.append(f"{stats['chunks']} chunks in staging, build/chunks.jsonl has {len(chunks)} (±10%)")
    if stats["without_embedding"]:
        fail.append(f"{stats['without_embedding']} chunks without an embedding")
    if stats["replacement_char"]:
        fail.append(f"U+FFFD in {stats['replacement_char']} chunks or documents: {stats['replacement_ids'][:5]}")
    if bare := [r.ref for r in manifest if r.ref not in skipped and r.sha256 not in stats["shas_with_chunks"]]:
        fail.append(f"{len(bare)} manifest files produced no chunk: {bare[:10]}")
    for section, ids in PINS.items():
        if (got := stats["pins"].get(section, [])) != sorted(ids):
            fail.append(f"pin § {section}: {got}, expected {ids}")
    return fail


def staging_stats(conn: psycopg.Connection) -> dict:
    one = lambda sql, *a: conn.execute(sql, a).fetchone()[0]
    fffd = conn.execute(
        "select id from staging.chunks where strpos(breadcrumb || body || label || sublabel || "
        "coalesce(heading, ''), %(c)s) > 0 union all select id from staging.documents "
        "where strpos(title, %(c)s) > 0 order by 1", {"c": REPLACEMENT_CHAR}).fetchall()
    pins: dict[str, list[str]] = {}
    for section, cid in conn.execute("select section, id from staging.chunks where section = any(%s)",
                                     (list(PINS),)):
        pins.setdefault(section, []).append(cid)
    pins = {s: sorted(ids) for s, ids in pins.items()}    # Python order, not the DB collation's
    return {
        "snapshots": one("select count(*) from staging.snapshot"),
        "chunker_version": one("select min(chunker_version) from staging.snapshot"),
        "chunks": one("select count(*) from staging.chunks"),
        "without_embedding": one("select count(*) from staging.chunks where embedding is null"),
        "replacement_char": len(fffd), "replacement_ids": [r[0] for r in fffd],
        "shas_with_chunks": {r[0] for r in conn.execute(
            "select distinct d.sha256 from staging.documents d join staging.chunks c on c.document_id = d.id")},
        "pins": pins,
    }


def check_staging(conn: psycopg.Connection) -> list[str]:
    skipped = [json.loads(line)["ref"] for line in config.SKIPPED.read_text(encoding="utf-8").splitlines()]
    return smoke_failures(staging_stats(conn), _jsonl(config.CHUNKS), store.read_manifest(), skipped)


def smoke() -> None:
    with connect() as conn:
        apply_schema(conn)
        fail = check_staging(conn)
    if fail:
        raise SystemExit("smoke FAILED:" + "".join(f"\n  {f}" for f in fail))
    print("smoke passed")


def swap() -> None:
    with connect() as conn:
        apply_schema(conn)
        if fail := check_staging(conn):
            raise SystemExit("refusing to swap; smoke fails on staging:" + "".join(f"\n  {f}" for f in fail))
        (n_chunks,) = conn.execute("select count(*) from staging.chunks").fetchone()
        with conn.transaction():
            for t in reversed(TABLES):
                conn.execute(f"delete from public.{t}")
            for t in TABLES:
                cols = CHUNK_COLUMNS if t == "chunks" else ["*"]
                cols_sql = ", ".join(cols)
                target = f"public.{t}" + (f" ({cols_sql})" if t == "chunks" else "")
                conn.execute(f"insert into {target} select {cols_sql} from staging.{t}")
        (sid,) = conn.execute("select id from public.snapshot").fetchone()
    print(f"live: snapshot {sid}, {n_chunks} chunks")
