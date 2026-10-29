-- Snapshot tables and the search_chunks RPC (CONTRACT.md, "Schema").
-- A template: `ingest.db` applies it once for {schema} = public (live) and once for staging.
-- Idempotent; re-running it never drops data.

create extension if not exists vector with schema extensions;
create schema if not exists {schema};

create table if not exists {schema}.snapshot (
  id              text primary key,
  snapshot_date   date not null,
  embed_model     text not null,
  embed_dim       int  not null,
  scope_sentence  text not null,
  chunker_version text not null
);

create table if not exists {schema}.documents (
  id                 text primary key,
  kind               text not null,   -- chapter | amending_bylaw | replacement_bylaw | item_page | staff_report
  family             text not null,   -- rules | decisions
  title              text not null,
  source_url         text not null,
  sha256             text not null,
  fetched_at         date,
  consolidated_as_of date,
  enacted            date,
  in_force           date,
  item_id            text,
  status_stamp       text,
  decision_date      date,
  bylaws             text[]
);

create table if not exists {schema}.chunks (
  id               text primary key,
  document_id      text not null references {schema}.documents on delete cascade,
  family           text not null,
  kind             text not null,
  section          text,
  subsection_range text,
  stage            text,
  heading          text,
  breadcrumb       text not null,
  body             text not null,
  label            text not null,
  sublabel         text not null,
  href             text not null,
  amended_since    text[] not null default '{}',
  page_start       int,
  page_end         int,
  tokens           int not null,
  fts              tsvector generated always as (to_tsvector('english', breadcrumb || ' ' || body)) stored,
  embedding        extensions.halfvec(1024) not null
);

create index if not exists chunks_embedding_idx on {schema}.chunks
  using hnsw (embedding extensions.halfvec_cosine_ops);
create index if not exists chunks_fts_idx on {schema}.chunks using gin (fts);
create index if not exists chunks_section_idx on {schema}.chunks (section);

create table if not exists {schema}.amendments (
  amending_chunk_id text not null references {schema}.chunks on delete cascade,
  target_section    text not null
);
create index if not exists amendments_target_idx on {schema}.amendments (target_section);

-- Server-only data: RLS on with no policies, so only the service role reads it.
alter table {schema}.snapshot   enable row level security;
alter table {schema}.documents  enable row level security;
alter table {schema}.chunks     enable row level security;
alter table {schema}.amendments enable row level security;

-- One round trip for all retrieval (STACK.md, "Retrieval"). `hybrid`: § numbers in the query
-- pin their chunks to the top; the rest is RRF (k = 60, equal weights) over the lexical and
-- vector top 30. `vector`: the vector list alone, no pin, no FTS. `score` is the fused RRF
-- score: rank arithmetic, no absolute meaning. Ties break on the chunk id in byte order, so
-- the order never depends on the database collation.
create or replace function {schema}.search_chunks(
  query_text      text,
  query_embedding extensions.halfvec(1024),
  mode            text default 'hybrid',
  match_count     int  default 20
)
returns table (
  id text, document_id text, family text, kind text, section text,
  label text, sublabel text, href text, amended_since text[], body text,
  rank int, score float8, pinned boolean
)
language plpgsql stable
set search_path = {schema}, extensions, pg_catalog
as $$
#variable_conflict use_column
declare
  hybrid   boolean := mode = 'hybrid';
  sections text[];
  lexical  tsquery;
begin
  if mode is null or mode not in ('vector', 'hybrid') then
    raise exception 'search_chunks: unknown mode %', mode;
  end if;
  if hybrid then
    -- '591-2.1', '950-1316B': the `english` parser splits these, so they never reach the FTS.
    select coalesce(array_agg(distinct upper(m[1])), '{}') into sections
    from regexp_matches(query_text, '(?<![\w.-])(\d{1,4}-\d+(?:\.\d+)*[a-z]?)(?![\w-])', 'gi') m;
    -- websearch parsing, but any term may match: a question ANDed term by term matches nothing.
    lexical := replace(websearch_to_tsquery('english', query_text)::text, ' & ', ' | ')::tsquery;
  end if;
  return query
    with vec as (
      select c.id, row_number() over (order by c.embedding <=> query_embedding, c.id collate "C") as r
      from (select id, embedding from chunks
            order by embedding <=> query_embedding limit 30) c
    ),
    lex as (
      select c.id, row_number() over (order by ts_rank_cd(c.fts, lexical) desc, c.id collate "C") as r
      from (select id, fts from chunks
            where hybrid and fts @@ lexical
            order by ts_rank_cd(fts, lexical) desc, id collate "C" limit 30) c
    ),
    pin as (
      select id from chunks where hybrid and section = any(sections)
    ),
    fused as (
      select coalesce(v.id, l.id) as id,
             coalesce(1.0 / (60 + v.r), 0) + coalesce(1.0 / (60 + l.r), 0) as rrf
      from vec v full join lex l on l.id = v.id
    ),
    ranked as (
      select * from (
        select coalesce(f.id, p.id) as id, coalesce(f.rrf, 0)::float8 as rrf, p.id is not null as is_pin
        from fused f full join pin p on p.id = f.id
      ) u
      order by u.is_pin desc, u.rrf desc, u.id collate "C"
      limit match_count
    )
    select c.id, c.document_id, c.family, c.kind, c.section,
           c.label, c.sublabel, c.href, c.amended_since, c.body,
           (row_number() over (order by k.is_pin desc, k.rrf desc, k.id collate "C"))::int,
           k.rrf, k.is_pin
    from ranked k join chunks c on c.id = k.id
    order by k.is_pin desc, k.rrf desc, k.id collate "C";
end
$$;

revoke execute on function {schema}.search_chunks(text, extensions.halfvec, text, int) from public, anon, authenticated;
grant usage on schema {schema} to service_role;
grant select on all tables in schema {schema} to service_role;
grant execute on function {schema}.search_chunks(text, extensions.halfvec, text, int) to service_role;
