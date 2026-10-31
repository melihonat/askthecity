# Answer and citation contract

What `/api/ask` returns, how a citation is produced and checked, and the Postgres schema the
Python ingester writes and the TypeScript app reads. The models behind it are in
[`STACK.md`](STACK.md). Chunking is in [`CHUNKING.md`](CHUNKING.md); terms are defined in [`CONTEXT.md`](CONTEXT.md).

## Citation

- A **citation is a chunk**. No quoted span, no § roll-up.
- The model sees passages numbered `[1]`–`[5]` (the reranked top 5), then **companion
  passages** `[6]`… (at most 3), and writes inline `[n]` markers. Clients never see a bare
  `n`: each is resolved to a chunk before the response leaves the server.
- **Companions:** for every top-5 Code § chunk (a `tmc:` id with a §), the chunks that
  target that § (via `amendments`, the `companion_chunks` RPC: amending clauses, and the §§ of
  a replacement not yet in force) are appended, capped at 3 per answer: in the order of the passages whose § they amend, newest by-law first, never
  repeating a chunk already among the top 5. Only § → amendment; a by-law chunk that ranks on
  its own does not pull its target in. The "amended since" badge still renders on the §.
- The model sees each passage's `sublabel` (its dates), an `amended_since` mark on an amended
  §, and an `amendment` mark on a companion. The prompt says the by-law wins where it differs
  from the §'s text, and to state an in-force date that differs from enactment (and "not yet
  in force" past the snapshot date). A passage from a replacement not yet in force is marked
  `not_yet_law` (and `replacement`, not `amendment`, as a companion); the prompt says the
  current § is the law until then and asks for "Today, X [n]. From <date>, Y [m]."
- Labels are built **once, at ingestion**, and stored on the chunk:

| Chunk | `label` | `sublabel` | `href` |
| --- | --- | --- | --- |
| Code § | `Ch 681 § 681-5 C–D` | `consolidated 2023-05-15` (`· replaced 2027-05-01 by By-law 1512-2025`, or `· repealed …`, while a replacement is pending) | chapter PDF `#page=<page_start>` |
| Amending by-law | `By-law 1482-2025 cl. 1 O–Y` | `amends § 608-8.1 B, § 608-16, § 608-19 +6 more · enacted 2025-12-17 · in force 2026-03-02` (`· in force 2026-05-21` alone when in force on enactment) | by-law PDF `#page=<page_start>` |
| Replacement chapter | `Ch 497 § 497-2.1` | `By-law 1511-2025 · in force 2026-06-01` (or `· in force 2027-05-01, not yet law`) | by-law PDF `#page=<page_start>` |
| Item page block | `Item 2026.IE29.6 · City Council decision` (or `IE Committee recommendation` / `IE Committee decision`; `(1/2)` when a stage splits) | stage date + status stamp: `2026-05-06 · Adopted with amendments by City Council 2026-05-21 · By-law 470-2026` | TMMIS item URL (no anchor) |
| Staff report | `Staff report · 2026.IE29.6 › COMMENTS › Manganese` | status stamp | `bgrd/` PDF `#page=<page_start>` |

  The stage is always named in an item-page label, so a committee recommendation never
  reads as Council's decision. A Decisions sublabel always ends with the status stamp, and an
  undecided item's stamp ends with `; no decision`: `toPassage` reads that suffix for the
  passage's `decided` flag (the `adopted` / `no decision` badge), and the prompt tells the
  model what it means.

## Generation and validation

The model's structured output:

```ts
{ decision: "answer" | "decline"; text: string; cited: number[] }
```

The answer is **buffered, not streamed**. The server:

1. `decision = "decline"` → refusal, reason `model_declined`.
2. Keeps the numbers that are in range of the passages given **and** appear as `[n]` in
   `text`; strips any other markers from `text`.
3. None left → refusal, reason `no_valid_citation`.
4. Otherwise resolves each kept `n` to its chunk and returns an answer.

The server does not remove uncited sentences. The prompt asks for a marker on every factual
sentence; how often that holds is measured by the eval as citation coverage.

## Refusal rule

The gate filters, the model judges, validation catches the rest.

1. **Gate (`below_threshold`)**, after reranking, before generation: the top rerank score
   below the threshold → refuse, no LLM call. The threshold is set **permissively**, with one
   job: never refuse an answerable question. It catches clearly off-corpus questions only;
   near-misses with a trap passage are expected to pass it. How it is set is in
   [`EVALS.md`](EVALS.md#refusal-threshold).
2. **A pin skips the gate.** If the section-number exact match placed any chunk, the question
   goes to the model whatever its score. A number matching no chunk pins nothing and is
   gated normally.
3. **Model (`model_declined`).** The prompt's rule: decline unless the passages *directly
   state* what was asked; related rules, definitions or the same topic under another
   authority are not enough; never answer from general knowledge. Two named cues: decline
   what the City doesn't set (provincial acts, the TTC board, zoning, tax rates) even when a
   passage mentions it, and decline events after the snapshot date (which the prompt
   carries). Any few-shot examples come from the `dev` split, never `test`.
4. **Validation (`no_valid_citation`)**, mechanical, as above.

**Partial coverage is an answer.** The covered part is answered with citations, followed by
one **gap sentence** with no `[n]` marker naming what the snapshot doesn't cover. If the gap
is all there is to say — only trap-passage trivia beside it — the model declines.

**Wording is fixed per reason and rendered by the client.** No model-written text appears in
a refusal; on a decline, the model's `text` goes only to the `debug` event. Meaning fixed
here, visual treatment in [`UI.md`](UI.md#refusal):

| Reason | Line under the headline **"The documents don't cover this."** | Nearest-passages heading |
| --- | --- | --- |
| `below_threshold` | Nothing in the snapshot comes close to this question. | Closest passages (not a match) |
| `model_declined` | I found related passages, but none of them answers it. | Related, but not an answer |
| `no_valid_citation` | I couldn't back an answer with a citation, so I'm not giving one. | Passages I had |

The scope sentence follows the line.

## Response

Streamed as two events: `passages` as soon as reranking finishes (the sources panel fills
while the model writes), then one final `AskResponse`. A refusal below the threshold sends
no generation call; a limit or an answer-cache hit sends only the final event.

```ts
type AskResponse =
  | { kind: "answer";
      text: string;                 // [n] markers, all valid
      citations: Citation[];        // cited passages only, keyed by n
      passages: PassageView[] }     // every passage given, companions included
  | { kind: "refusal";
      reason: "below_threshold" | "model_declined" | "no_valid_citation";
      scope: string;                // the scope sentence
      nearest: PassageView[] }      // top 2–3 that weren't good enough
  | { kind: "limit";
      limit: "ip_daily" | "global_daily" | "burst" | "budget" | "too_long" | "unavailable" };

type PassageView = {
  n: number; chunkId: string; companion: boolean;
  family: "rules" | "decisions";
  label: string; sublabel: string; href: string;
  amendedSince: string[];           // by-law numbers, for the badge
  body: string;                     // display text, markdown tables kept
};

type Citation = { n: number; chunkId: string };
```

The cache (`answer_cache`), the example questions and the eval harness all store or read
this same object.

### The `debug` event (eval header only)

A request carrying the eval header ([`GUARDRAILS.md`](GUARDRAILS.md#the-eval-header)) gets a third event, `debug`, before the final
`AskResponse`. Same code path; it only exposes what the path already computed. Never sent to
the public. Scoring that uses it is in [`EVALS.md`](EVALS.md).

```ts
type DebugEvent = {
  candidates: { chunkId: string; rrfRank: number; rerankScore: number }[]; // the 20, fused order
  pinned: string[];        // chunk ids placed by the section-number exact match
  gateScore: number;       // top rerank score the refusal threshold was compared to
  threshold: number;
  gateBypassed: boolean;   // a pin fired, so the threshold was not applied
  declineText: string | null; // the model's text on decision = "decline"; never public
  timings: { retrieval_ms: number; rerank_ms: number; generation_ms: number | null; total_ms: number };
  rung: Rung;
  config: RungConfig;      // resolved from the rung
  build: { sha: string | null; promptVersion: string; promptHash: string; embedder: string; reranker: string };
};
```

With the rerank off, `rerankScore` and `gateScore` are `null`. `build.sha` is the deployed
commit (`VERCEL_GIT_COMMIT_SHA`), so `run.json` can tell which code it measured.

### Rungs (eval header only)

The rungs themselves are in [`evals/LADDER.md`](evals/LADDER.md).

A request carrying the eval header may name a `rung` in the body (`{ question, rung }`); an
unknown rung is a 400. Without the header the field is ignored and every request is
`shipped`.

```ts
type Rung = "dense" | "hybrid" | "rerank" | "shipped" | "side-sonnet" | "side-quoted"; // + shipped-2, shipped-3

type RungConfig = {
  search: "vector" | "hybrid";      // search_chunks mode arg: vector skips FTS and the pin
  rerank: boolean;                  // false: top 5 by fused rank, and the gate is off
  companions: boolean;
  model: string;                    // pinned id, never an alias
  prompt: "default" | "quoted";
};
```

- Presets are a **closed enum in app code**, each a `RungConfig`; no free-form knobs. The
  one orchestration function reads the config; branches are flags inside the shipped path,
  never a second implementation.
- `search_chunks` takes the mode as an argument: still one RPC.
- The `debug` event carries `rung` and the resolved `config`, and `run.json` records both.

## Chunk ids

Deterministic and readable, built from where the chunk sits; the same source gives the same
id on every ingestion:

| Chunk | Id |
| --- | --- |
| Code § (with subsection range) | `tmc:681-5:C-D`, `tmc:681-2:A(3)(a)-A(3)(k)` |
| Code definitions run (first term) | `tmc:591-1.1:ambient-sound-level` |
| Code §, part of a unit split by paragraph | `tmc:681-4:Jp2`, `tmc:213-2.4:p1` |
| Code schedule printed in the chapter | `tmc:349:schedule-a` |
| Amending by-law clause | `bl:470-2026:cl1` |
| Replacement chapter §, in force | `tmc:497-2.1` (document `bl:1511-2025`) |
| Replacement chapter §, not yet in force | `bl:1512-2025:629-4.25` (a companion of the old §) |
| Item page block | `ie:2026.IE29.6:council` |
| Staff report section | `sr:286369:comments:2` |

Eval gold answers are written in chunk ids. A gold id that no longer exists after a
re-ingestion is a **stale gold id**: the scorer flags it and never counts it as a miss.

## Schema

```sql
snapshot   -- exactly one row
  id text, snapshot_date date, embed_model text, embed_dim int,
  scope_sentence text, chunker_version text

documents  -- one row per manifest file
  id text primary key,       -- 'tmc:681', 'bl:470-2026', 'ie:2026.IE29.6', 'sr:286369'
  kind text,                 -- chapter | amending_bylaw | replacement_bylaw | item_page | staff_report
                             -- (a replacement in force keeps its kind; its chunks have tmc: ids)
  family text,               -- rules | decisions
  title text, source_url text, sha256 text, fetched_at date,
  consolidated_as_of date, enacted date, in_force date,              -- rules
  item_id text, status_stamp text, decision_date date, bylaws text[] -- decisions

chunks
  id text primary key,       -- chunk id
  document_id text references documents,
  family text, kind text,    -- copied from documents: search_chunks never joins
  section text,              -- '681-5'; exact-match pin; null for decisions
  subsection_range text, stage text, heading text,
  breadcrumb text,           -- embedded and indexed, not shown as body
  body text,
  label text, sublabel text, href text,
  amended_since text[],
  page_start int, page_end int, tokens int,
  fts tsvector generated always as (to_tsvector('english', breadcrumb || ' ' || body)) stored,
  embedding halfvec(1024)

amendments -- the join behind companion passages: amending clause or pending replacement § → old §
  amending_chunk_id text references chunks,
  target_section text        -- btree index
```

`companion_chunks(sections text[])` returns the amending chunks targeting those §§ (with the
§ each targets), the passage fields only; the app orders and caps them.

- No `sections` table: a § is a column on its chunks; §-level matching uses the id prefix.
- `usage_daily` and `answer_cache` ([`GUARDRAILS.md`](GUARDRAILS.md)) live alongside and are never touched by
  ingestion.

## Re-ingestion

One live snapshot. A re-ingestion deletes and re-inserts `snapshot`, `documents`, `chunks`
and `amendments` **inside one transaction**, so `/api/ask` sees the old snapshot or the new
one, never a mix. The answer cache invalidates itself because its key includes
`snapshot.id`. Earlier snapshots survive only as committed manifests.

The rows come from a `staging` schema with the same tables and RPC, filled by `load` and
checked by `smoke` before the swap copies it into live. Run mechanics are in
[`INGESTION.md`](INGESTION.md).
