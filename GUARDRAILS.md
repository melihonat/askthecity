# Public demo guardrails

How the public demo stays cheap, available and hard to abuse. Costs come from
[`STACK.md`](STACK.md); the limit responses are typed in [`CONTRACT.md`](CONTRACT.md) and
worded in [`UI.md`](UI.md#limit).

## Spend

- **Ceiling: $10 prepaid AI Gateway credit (the minimum top-up), auto top-up off.** ≈ 9,000
  answers or ≈ 20,000 refusals. A zero balance returns 402, which the app turns into the `budget` limit.
- A **$2/month Gateway budget** is an early-warning alert only (Gateway budgets are a soft
  cap). Refill is manual; nothing renews on its own.

## Rate limits

- **Burst:** the one Hobby firewall rule on `/api/ask`: 10 requests / 60 s per IP → 429
  (configured below).
- **Daily, in Postgres**: a `usage_daily` table keyed by Toronto date + salted IP hash (no raw
  IPs stored). **30 questions per IP per day, 500 paid questions per day globally** (≈ $0.55/day
  worst case: a sustained bot needs ~18 days to drain $10, and the $2 alert fires around day
  4). Cache hits and example questions don't count. No Upstash: one fewer free tier to keep
  alive.
- **How the daily check runs:** one `use_quota(ip_hash, 30)` RPC ([`db/app.sql`](db/app.sql)),
  started beside the query embedding so it adds no latency, before the search. It counts the
  question against the IP and, only while the IP is under 30, against the global day (one IP
  over its limit can't use up everyone's 500), and returns the counts from before it; the app
  decides (`lib/ask/guardrails.ts`). The limits reset at midnight Toronto time, and days
  before yesterday are deleted as it goes. The hash is HMAC-SHA256 of the client IP
  (`x-real-ip`) keyed by `IP_HASH_SALT`; with no salt set, public requests get `unavailable`.

### The burst rule

A Vercel WAF custom rule, configured in the dashboard (Firewall → Configure) or with
`vercel firewall rules add --json … && vercel firewall publish --yes`:

```json
{
  "name": "Burst limit /api/ask",
  "conditionGroup": [{ "conditions": [
    { "type": "path", "op": "eq", "value": "/api/ask" },
    { "type": "method", "op": "eq", "value": "POST" },
    { "type": "header", "key": "x-eval-key", "op": "eq", "neg": true, "value": "<EVAL_HEADER_SECRET>" }
  ] }],
  "action": { "mitigate": { "action": "rate_limit",
    "rateLimit": { "algo": "fixed_window", "window": 60, "limit": 10, "keys": ["ip"], "action": "rate_limit" } } }
}
```

It answers 429 before the function runs, so the UI maps a 429 to the `burst` notice. Counters
are per region; the app runs in one (`iad1`). The harness (~30 calls a minute) is exempt by an
exact match on the eval secret, so the secret also lives in the firewall config: **rotating
`EVAL_HEADER_SECRET` means editing this rule too**, or the next ladder run is throttled.

## Degraded states

`/api/ask` never returns a raw 500; every limit is a typed `limit` response the UI renders.
Upstream errors map by status: a Gateway 402 (credit gone) is `budget`, a 429 is `burst`, and
anything else (a DB or provider outage, a corpus mismatch) is `unavailable`, logged server-side.
A limit decided before the search is the only event; a failure after the `passages` event
still ends in a `limit` final event, and the UI drops the passages.
Example questions (including at least one cached refusal) and the eval table keep working at
$0, so a 3-minute visit still shows the headline behaviour.

## Answer cache

- **Exact match only, in Postgres** (`answer_cache`). Key = hash of the normalised question
  (lowercase, trimmed, whitespace collapsed) + snapshot id + config version (model ids,
  prompt version, refusal threshold). Stores the full typed response. No TTL; a key change
  invalidates.
- **No semantic cache:** a near-miss serving someone else's answer is the quiet wrongness
  this demo exists to avoid.
- Example questions are pre-warmed by a script after deploy.

## The eval header

The eval harness sends a secret header. It skips the cache (so the table measures retrieval
and real latency, not cache hits) and the per-IP and global limits (the harness's runs are
bounded and would otherwise trip 30/IP). It also unlocks the `debug` event and rung presets
([`CONTRACT.md`](CONTRACT.md#the-debug-event-eval-header-only)). Never sent by the public UI.

`x-eval-key: <EVAL_HEADER_SECRET>`, compared in constant time; with no secret configured
nothing is unlocked. The harness also sends `x-eval-run: <run-id>`, and every Gateway call of
that request (embed, rerank, generate) is tagged `eval:<run-id>`.

## Keep-alive and failure detection

- **Two staggered daily Vercel crons** (e.g. 06:00 and 18:00 UTC) on `/api/keepalive`,
  guarded by `CRON_SECRET`, call the real `search_chunks` RPC with a stored precomputed
  query embedding: real DB work at $0, so Supabase Free never pauses.
- **One daily GitHub Actions workflow** on `/api/health` runs a DB-only check. A paused or
  broken DB fails the workflow and GitHub e-mails the owner. Kept because Vercel does not
  alert on cron failures, and a dead DB takes down the cache, examples and limits, the one
  failure the degraded states can't absorb.
- Caveat for the README: GitHub disables scheduled workflows after 60 days without a commit;
  re-enable it in Actions.

## Input and prompt injection

- **300-character question cap**, enforced server-side with a typed `too_long` limit, plus a
  UI counter; control characters stripped. No blocklist, no injection classifier.
- **The defence is structural.** Off-topic and "ignore your instructions" questions mostly
  fall below the reranker gate and are refused before any LLM call. For what passes: the
  model has no tools and no secrets in context; passages are delimited and the system prompt
  says answer only from them; every citation is range-checked server-side, and an answer
  left with no valid citation becomes a `no_valid_citation` refusal
  ([`CONTRACT.md`](CONTRACT.md)); output is capped at ~400 tokens. Injection inside the City's
  own documents is low risk and covered by the same validation.
- **No BotID.** Damage is already bounded by the burst, daily and credit limits; BotID would
  flag the eval harness's scripted calls. Revisit only if abuse shows up.
