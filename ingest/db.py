"""load: build/ → the staging schema. swap: staging → live, in one transaction."""
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


def swap() -> None:
    with connect() as conn:
        apply_schema(conn)
        (snapshots,) = conn.execute("select count(*) from staging.snapshot").fetchone()
        (n_chunks,) = conn.execute("select count(*) from staging.chunks").fetchone()
        if snapshots != 1 or n_chunks == 0:
            raise SystemExit(f"staging is not a complete snapshot ({snapshots} snapshot rows, "
                             f"{n_chunks} chunks); run `load` first")
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
