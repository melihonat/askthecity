# Ingestion

How the one-off snapshot is built, and rebuilt by hand later. What enters
the corpus is in [`CORPUS.md`](CORPUS.md); how it
is chunked is [`CHUNKING.md`](CHUNKING.md); the tables it fills are in
[`CONTRACT.md`](CONTRACT.md). Terms are defined in [`CONTEXT.md`](CONTEXT.md).

## Where things live

| What | Where | Public? |
| --- | --- | --- |
| Raw files (PDFs, saved item pages) | private **Cloudflare R2** bucket, `raw/<sha256>.<ext>` | no |
| Working copy of the raw files | `corpus/` (gitignored) | no |
| Extracted text, chunks, embeddings | `build/` (gitignored) | no |
| Manifest, expected TMMIS list, hand-review files | `snapshot/` (committed) | yes |
| Pipeline code | `ingest/` (committed) | yes |
| Secrets (Voyage, Supabase service role, R2) | local `.env` | no |

The raw copy is about 0.6–0.7 GB; By-law 1517-2025 alone is 365 MB, which is why it is R2
(10 GB free, 5 GB per object) and not Supabase Storage (50 MB per file on Free) or a GitHub
repo (100 MB per file). Files are content-addressed, so the manifest's `sha256` is the key.

## The manifest

`snapshot/manifest.csv`, one row per raw file. Raw facts only; extraction stats belong to
the chunk stage.

| Column | Meaning |
| --- | --- |
| `sha256` | identity and R2 key |
| `kind` | `code_chapter` · `amending_bylaw` · `item_page` · `staff_report` |
| `ref` | `ch-681`, `bylaw-470-2026`, `2026.IE29.6`, `backgroundfile-286369` |
| `parent_ref` | staff report → its item; empty otherwise |
| `source_url` | where it came from |
| `obtained_by` | `script` · `agent_fetch` · `browser_save` |
| `obtained_at` | UTC timestamp |
| `last_modified`, `etag` | HTTP headers as sent; empty for browser saves |
| `bytes`, `content_type` | sanity check |
| `encoding` | `windows-1252` for item pages; empty for PDFs |

Saved item pages keep the HTML only, never the browser's `_files/` folder.
`snapshot/SNAPSHOT.md` records the snapshot date (the day `fetch-rules` runs), row
counts per kind, and the restore command.

## Stages

One local CLI, `python -m ingest <stage>`. No CI: the run is one-off, one step needs an agent
browser, and the secrets stay on the machine. Every stage reads files and writes files, so
any stage re-runs alone.

| # | Stage | Reads → writes | Stops when |
| --- | --- | --- | --- |
| 1 | `fetch-rules` | toronto.ca → `corpus/`, R2, manifest rows | a download fails |
| 1b | `fetch-bylaws` | yearly by-law lists + `build/documents.jsonl` → `corpus/`, R2, manifest rows | a download fails |
| 2 | *save TMMIS* | agent runbook + `receive-saves` → `corpus/item_page/`, R2, manifest rows | — (see below) |
| 3 | `check-saves` | `snapshot/tmmis_items.txt` vs saved files | any id lacks a passing file |
| 4 | `fetch-reports` | `bgrd/` links on saved pages → `corpus/`, R2, manifest | an unreviewed label appears |
| 5 | `extract` | `corpus/` → `build/text/` | — |
| 6 | `chunk` | `build/text/` + `snapshot/review/` → `build/chunks.jsonl`, `build/amendments.jsonl` | a § map is missing or incomplete |
| 7 | `embed` | chunks → `build/embeddings` | spend estimate not confirmed |
| 8 | `load` | → `staging` schema in Postgres | — |
| 9 | `smoke` | `staging` | any check fails |
| 10 | `swap` | `staging` → live, one transaction | — |

- **`fetch-bylaws`** needs each chapter's consolidated-as-of date, so it runs after a first
  `extract` + `chunk` of the chapters; then `extract` and `chunk` run again with the by-laws.
  It skips by-laws already in `corpus/`. The `chunk` stage links them (which are already
  folded in, which amend schedules only) and lists the dropped ones in `build/skipped.jsonl`.
  It also fetches replacement by-laws (manifest kind `replacement_bylaw`); `chunk` decides
  whether each stands in for its chapter, rides along as not yet law, or is already
  consolidated ([`CHUNKING.md`](CHUNKING.md#rules-amending-by-laws)).
- **`restore`** pulls every manifest row from R2 into `corpus/`, verifying sha256. It
  replaces stages 1–4 on a new machine; nothing is re-fetched from the City.
- **`all`** runs stages 3–8 in order and stops at the first failure (today 3 and 5–8:
  `fetch-reports` doesn't exist yet).
- **`swap` is never automatic.** The run is `all` → `smoke` → `swap`, by hand, and `swap`
  re-runs the `smoke` database checks itself and refuses if any fails.
- **`chunker_version`** (in `ingest/config.py`, stored on the `snapshot` row) is bumped
  whenever `chunk` would produce different output from the same input; `smoke` checks the
  loaded snapshot carries the current one.
- Item pages are saved **within 7 days** of `fetch-rules`; `check-saves` reads
  `obtained_at` to enforce it.

## Saving TMMIS item pages

Scripts get an Akamai 403; the agent-driven preview browser loads the pages. So
stage 2 is a runbook an agent session follows, [`ingest/SAVE_TMMIS.md`](ingest/SAVE_TMMIS.md),
not pipeline code. The only code is `receive-saves`, a localhost receiver that writes what
the page posts through the snapshot store.

1. Open the 8 IE24–IE31 meeting pages and write the 115 item ids to
   `snapshot/tmmis_items.txt`. Counts per meeting must match (15, 14, 19, 17, 14, 10, 14,
   12) or stop.
2. For each id, run `fetch()` on the item page **inside the page** to get the exact bytes as
   served (the DOM would be already decoded, so its hash would mean nothing) and POST them
   to `receive-saves`; `obtained_by=agent_fetch`.
3. A page that fails is saved by hand (Ctrl+S, "Webpage, HTML only") and posted the same way;
   `obtained_by=browser_save`.

`check-saves` passes a file when it decodes as `windows-1252`, has the item heading and the
Tracking Status section, is over 10 KB, is not an Akamai "Access Denied" page, and was saved
within 7 days of the snapshot date; the expected list must match the per-meeting counts. Any
id without a passing file is printed with its reasons, and the stage exits non-zero. On a
pass it rewrites `snapshot/SNAPSHOT.md`.

The City pointed to the TMMIS open-data API for bulk item data; it sits behind the same
Akamai wall, and the pages carry everything the chunker needs, so the snapshot saves the
pages as served.

## Hand-review inputs

Committed in `snapshot/review/`: labels, URLs and § numbers only, no City text. Each is a
hard stop at the stage that first needs it: **the stage drafts, stops, you edit, you
re-run.**

- **`report_labels.csv`** (`label, decision, note`), checked by `fetch-reports` before any
  download. Allowlisted and blocklisted labels ([`CHUNKING.md`](CHUNKING.md#decisions-what-enters))
  pass silently; any other label not already in the file goes to
  `report_labels.pending.csv` and the stage exits. Files decided `out` are never
  downloaded.
- **`section_map_<bylaw>.csv`** (`old_section, new_section, note`), checked by `chunk` for
  every replacement chapter whose `in_force` is after the snapshot date (today:
  1512-2025 → Ch 629, in force 2027-05-01). Missing or incomplete → the stage writes
  `section_map_<bylaw>.draft.csv` (the valid reviewed rows, plus a row per unmapped § paired
  by heading similarity, notes starting `draft:`) and exits. Coverage check: every new § maps
  from an old § or says `new` in `old_section`; every old § maps to a new § or says
  `repealed` in `new_section`; no row names a § that doesn't exist. One § may appear in
  several rows (629-11 → 629-4.2 and 629-4.3). A replacement already in force needs no map.
  The heading draft is only a start: for 1512-2025 it paired the heritage definitions with
  the general ones and occupancy with heritage standards, so read the text.

## Embedding spend

- `voyage-4-large`, ~2–3M tokens, ≈ $0.25–0.40 at list price; in practice $0 inside
  Voyage's 200M free tokens.
- Paid by a **separate Voyage key used only by ingestion**, calling Voyage directly (not
  AI Gateway), so it draws on the free tokens for certain and never touches the demo's $10
  prepaid credit ([`GUARDRAILS.md`](GUARDRAILS.md#spend)). Account spend limit ~$2.
- `embed` prints the token count and cost estimate and asks before spending.
- Cached by `(model, sha256 of chunk text)`: a re-run pays only for changed chunks. It
  throttles itself and resumes from the cache, so it works with or without a card on the
  Voyage account (a card only makes it faster).
- Query-time embeddings stay on Gateway under the $10 credit ([`STACK.md`](STACK.md#embeddings)).

## Smoke check before `swap`

`smoke` runs against the `staging` schema and fails loudly on any of:

1. **Counts:** exactly one `snapshot` row with the current `chunker_version`; chunk count
   within ±10% of `build/chunks.jsonl`; every manifest row produced at least one chunk
   (except those `chunk` listed in `build/skipped.jsonl`, the Reserved stubs); no chunk
   without an embedding; no U+FFFD anywhere (a `windows-1252` decode went wrong).
2. **Pins:** fixed §§ (`§ 591-2.6`, `§ 591-1.1`, `§ 681-4`, `§ 608-19`, `§ 349-1`,
   `§ 497-2.2` from Ch 497's re-consolidation with 1511-2025, `§ 629-38` and its pending
   replacement `§ 629-4.25`) hold exactly the expected chunk ids (`PINS` in
   `ingest/db.py`). `§ 608-19` and `§ 629-38` are amended since their consolidation: each of
   their chunks carries the expected `amended_since`, and `amendments` links exactly the
   expected chunks to them (`AMENDED_PINS`; for `§ 629-38` that includes
   `bl:1512-2025:629-4.25`); the other pins carry neither.
3. **Dev split** (not wired yet; it arrives with the refusal-threshold calibration): the 10-question dev split ([`EVALS.md`](EVALS.md#refusal-threshold)) through `/api/ask` on a local `next dev` with
   `DB_SCHEMA=staging` and the eval header. It must score at least what the previous
   snapshot scored, or meet the refusal-threshold calibration bar on the first run.

The full eval set and the experiment ladder ([`evals/LADDER.md`](evals/LADDER.md)) run
**after** `swap`, as evidence, not as a gate.
