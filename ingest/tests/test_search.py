"""search_chunks against a local Postgres: a small seeded snapshot with fixed embeddings.

Needs TEST_DATABASE_URL, a Postgres with pgvector >= 0.7 (halfvec) where the test may create
and drop the `ask_city_test` database; skipped without it. Never point it at Supabase.
"""
import json
import os

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from ingest import db

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL is not set")

DIM = 1024
TEST_DB = "ask_city_test"


def axis(i: int, j: int | None = None, w: float = 1.0) -> list[float]:
    """Axis i, plus w along axis j: the larger w, the further from axis i."""
    v = [0.0] * DIM
    v[i] = 1.0
    if j is not None:
        v[j] = w
    return v


QUERY = axis(0)
FAR = [-x for x in QUERY]     # cosine distance 2: last in the vector list

# id, section, body, embedding
CHUNKS = (
    [("tmc:591-2.1", "591-2.1", "Noise of the kind described in Schedule 2 is prohibited.", axis(9)),
     ("tmc:591-2.10", "591-2.10", "Stationary sources are measured at the point of reception.", axis(9)),
     ("tmc:681-4:A", "681-4", "No person shall discharge into a sanitary sewer.", axis(8)),
     ("tmc:681-4:B", "681-4", "No person shall discharge into a storm sewer.", axis(8)),
     ("tmc:950-1316B", "950-1316B", "Parking in a park is prohibited.", FAR),
     ("tmc:740-1", "740-1", "A leaf blower may be used between 7 a.m. and 7 p.m.", FAR),
     ("ie:2026.IE29.6:council", None, "City Council adopted the item.", axis(7))]
    + [(f"tmc:1-{i:02d}", f"1-{i:02d}", "Filler text about permits.", axis(0, i + 10)) for i in range(30)]
    + [(f"tmc:2-{i:02d}", f"2-{i:02d}", "Filler text about permits.", axis(0, 50, 0.5)) for i in range(5)]
)


@pytest.fixture(scope="module")
def conn():
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute(f"drop database if exists {TEST_DB}")
        admin.execute(f"create database {TEST_DB}")
    with psycopg.connect(make_conninfo(URL, dbname=TEST_DB), autocommit=True) as c:
        for role in ("anon", "authenticated", "service_role"):     # Supabase's roles
            c.execute(f"do $$ begin create role {role}; exception when duplicate_object then null; end $$")
        c.execute("create schema extensions")
        db.apply_schema(c)
        db.apply_schema(c)                                         # idempotent
        c.execute("insert into public.documents (id, kind, family, title, source_url, sha256) values "
                  "('tmc:x', 'chapter', 'rules', 'x', 'https://example.test', 'sha')")
        with c.cursor() as cur:
            cur.executemany(
                "insert into public.chunks (id, document_id, family, kind, section, breadcrumb, body, "
                "label, sublabel, href, tokens, embedding) values (%s, 'tmc:x', 'rules', 'chapter', %s, "
                "'', %s, %s, '', '', 1, %s::extensions.halfvec)",
                [(cid, sec, body, cid, json.dumps(emb)) for cid, sec, body, emb in CHUNKS])
        c.execute("set hnsw.ef_search = 1000")                     # exact on a table this small
        yield c
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute(f"drop database {TEST_DB}")


def search(conn, question: str, mode: str = "hybrid", match_count: int = 20, schema: str = "public"):
    return conn.execute(
        f"select id, pinned, rank from {schema}.search_chunks(%s, %s::extensions.halfvec, %s, %s)",
        (question, json.dumps(QUERY), mode, match_count)).fetchall()


def ids(rows) -> list[str]:
    return [r[0] for r in rows]


def test_a_section_number_pins_its_chunks_first_whatever_the_wording(conn):
    rows = search(conn, "What does § 591-2.1 say?")
    assert rows[0][:2] == ("tmc:591-2.1", True)
    assert "tmc:591-2.10" not in ids(rows)                         # exact match, not a prefix


def test_every_chunk_of_a_pinned_section_is_pinned(conn):
    rows = search(conn, "Summarize s. 681-4 and 950-1316b.")
    assert [r for r in rows if r[1]] == [("tmc:681-4:A", True, 1), ("tmc:681-4:B", True, 2),
                                         ("tmc:950-1316B", True, 3)]
    assert not any(pinned for _, pinned, _ in rows[3:])


def test_a_number_that_matches_no_section_pins_nothing(conn):
    rows = search(conn, "What does § 999-9 say?")
    assert rows and not any(pinned for _, pinned, _ in rows)


def test_lexical_matches_back_up_the_vector_list(conn):
    # Last in the vector list, outside its top 30; FTS brings it in on one shared term.
    assert "tmc:740-1" in ids(search(conn, "When can I run my leaf blower on a Sunday?"))


def test_vector_mode_skips_the_pin_and_fts(conn):
    rows = search(conn, "What does § 591-2.1 say about a leaf blower?", mode="vector")
    assert not any(pinned for _, pinned, _ in rows)
    assert "tmc:591-2.1" not in ids(rows) and "tmc:740-1" not in ids(rows)
    assert ids(rows)[:5] == ["tmc:2-00", "tmc:2-01", "tmc:2-02", "tmc:2-03", "tmc:2-04"]


def test_the_same_input_gives_the_same_order_and_ties_break_on_id(conn):
    q = "Is a permit needed under § 681-4?"
    first = search(conn, q)
    assert first == search(conn, q)
    assert [r[2] for r in first] == list(range(1, len(first) + 1))
    tied = [i for i in ids(first) if i.startswith("tmc:2-")]       # identical embeddings
    assert tied == sorted(tied)


def test_results_are_capped_at_twenty_rows(conn):
    assert len(search(conn, "permits")) == 20
    assert len(search(conn, "permits", mode="vector")) == 20
    assert len(search(conn, "§ 681-4 permits", match_count=3)) == 3


def test_staging_has_the_same_rpc(conn):
    assert search(conn, "What does § 591-2.1 say?", schema="staging") == []


def test_an_unknown_mode_is_an_error(conn):
    with pytest.raises(psycopg.errors.RaiseException, match="unknown mode"):
        search(conn, "x", mode="bm25")
