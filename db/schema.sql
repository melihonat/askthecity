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

-- One round trip for all retrieval. Only `vector` mode exists so far; `hybrid` (FTS, RRF and
-- the section pin) arrives with the hybrid-search slice.
create or replace function {schema}.search_chunks(
  query_text      text,
  query_embedding extensions.halfvec(1024),
  mode            text default 'vector',
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
begin
  if mode <> 'vector' then
    raise exception 'search_chunks: mode % is not implemented', mode;
  end if;
  return query
    select v.id, v.document_id, v.family, v.kind, v.section,
           v.label, v.sublabel, v.href, v.amended_since, v.body,
           (row_number() over (order by v.distance, v.id))::int,
           1 - v.distance,
           false
    from (
      select c.*, (c.embedding <=> query_embedding)::float8 as distance
      from chunks c
      order by c.embedding <=> query_embedding
      limit match_count
    ) v
    order by v.distance, v.id;
end
$$;

revoke execute on function {schema}.search_chunks(text, extensions.halfvec, text, int) from public, anon, authenticated;
grant usage on schema {schema} to service_role;
grant select on all tables in schema {schema} to service_role;
grant execute on function {schema}.search_chunks(text, extensions.halfvec, text, int) to service_role;
