-- App tables (GUARDRAILS.md): live schema only, never touched by ingestion's load or swap.
-- Idempotent; re-running it never drops data.

-- Daily limits. `key` is 'global' or a salted IP hash (64 hex chars); never a raw IP.
create table if not exists public.usage_daily (
  day       date not null,   -- Toronto date: the limits reset at midnight Toronto time
  key       text not null,
  questions int  not null,
  primary key (day, key)
);
alter table public.usage_daily enable row level security;

-- One paid question: counted against the IP's day and, while the IP is under ip_limit, the
-- global day (an IP over its own limit can't use up everyone's). Returns the counts from before
-- this question; the app makes the decision (lib/ask/guardrails.ts). Days before yesterday are
-- deleted as it goes, so hashes don't pile up.
create or replace function public.use_quota(ip_key text, ip_limit int)
returns table (ip int, global int)
language plpgsql volatile
set search_path = public, pg_catalog
as $$
#variable_conflict use_column
declare
  today    date := (now() at time zone 'America/Toronto')::date;
  ip_n     int;
  global_n int;
begin
  insert into usage_daily as u (day, key, questions) values (today, ip_key, 1)
  on conflict (day, key) do update set questions = u.questions + 1
  returning u.questions - 1 into ip_n;

  if ip_n < ip_limit then
    insert into usage_daily as u (day, key, questions) values (today, 'global', 1)
    on conflict (day, key) do update set questions = u.questions + 1
    returning u.questions - 1 into global_n;
  else
    select u.questions into global_n from usage_daily u where u.day = today and u.key = 'global';
  end if;

  delete from usage_daily u where u.day < today - 1;
  return query select ip_n, coalesce(global_n, 0);
end
$$;

revoke execute on function public.use_quota(text, int) from public, anon, authenticated;
grant select, insert, update, delete on public.usage_daily to service_role;
grant execute on function public.use_quota(text, int) to service_role;

-- The answer cache: exact match, no TTL. `key` is sha256(normalised question, snapshot id,
-- config version) (lib/ask/cache.ts), so a new snapshot or config misses and old rows are just
-- never read again. `response` is the AskResponse the API sent.
create table if not exists public.answer_cache (
  key        text primary key,
  response   jsonb not null,
  created_at timestamptz not null default now()
);
alter table public.answer_cache enable row level security;

grant select, insert on public.answer_cache to service_role;
