"""use_quota against a local Postgres: the daily counts behind the ip_daily and global_daily limits.

Needs TEST_DATABASE_URL, like test_search; creates and drops its own database. Never Supabase.
"""
import os

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from ingest import db

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL is not set")

TEST_DB = "ask_city_usage_test"


@pytest.fixture
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
        yield c
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute(f"drop database {TEST_DB}")


def use(conn, ip: str, ip_limit: int = 2) -> tuple[int, int]:
    return conn.execute("select ip, global from public.use_quota(%s, %s)", (ip, ip_limit)).fetchone()


def test_returns_the_counts_from_before_each_question(conn):
    assert [use(conn, "a"), use(conn, "a"), use(conn, "b")] == [(0, 0), (1, 1), (0, 2)]


def test_an_ip_over_its_limit_stops_counting_globally(conn):
    for _ in range(5):
        use(conn, "a")
    assert use(conn, "b") == (0, 2)                                # only a's first two counted


def test_the_staging_schema_has_no_usage_table(conn):
    assert conn.execute("select to_regclass('staging.usage_daily')").fetchone() == (None,)


def test_old_days_are_deleted(conn):
    conn.execute("insert into public.usage_daily values (current_date - 10, 'old', 3)")
    use(conn, "a")
    assert conn.execute("select count(*) from public.usage_daily where key = 'old'").fetchone() == (0,)
