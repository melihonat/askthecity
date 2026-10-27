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
| 2 | *save TMMIS* | agent runbook → `corpus/item_page/` | — (see below) |
| 3 | `check-saves` | `snapshot/tmmis_items.txt` vs saved files | any id lacks a passing file |
| 4 | `fetch-reports` | `bgrd/` links on saved pages → `corpus/`, R2, manifest | an unreviewed label appears |
| 5 | `extract` | `corpus/` → `build/text/` | — |
| 6 | `chunk` | `build/text/` + `snapshot/review/` → `build/chunks.jsonl` | a § map is missing or incomplete |
| 7 | `embed` | chunks → `build/embeddings` | spend estimate not confirmed |
| 8 | `load` | → `staging` schema in Postgres | — |
| 9 | `smoke` | `staging` | any check fails |
| 10 | `swap` | `staging` → live, one transaction | — |

- **`restore`** pulls every manifest row from R2 into `corpus/`, verifying sha256. It
  replaces stages 1–4 on a new machine; nothing is re-fetched from the City.
- **`all`** runs stages 3–8 in order and stops at the first failure.
- **`swap` is never automatic.** The run is `all` → `smoke` → `swap`, by hand.
- Item pages are saved **within 7 days** of `fetch-rules`; `check-saves` reads
  `obtained_at` to enforce it.

## Saving TMMIS item pages

Scripts get an Akamai 403; the agent-driven preview browser loads the pages. So
stage 2 is a runbook an agent session follows, `ingest/SAVE_TMMIS.md`, not pipeline code.

1. Open the 8 IE24–IE31 meeting pages and write the 115 item ids to
   `snapshot/tmmis_items.txt`. Counts per meeting must match (15, 14, 19, 17, 14, 10, 14,
   12) or stop.
2. For each id, open the item page and run `fetch(location.href)` **inside the page** to get
   the exact bytes as served (the DOM would be already decoded, so its hash would mean
   nothing). Write them to `corpus/item_page/<id>.html`; `obtained_by=agent_fetch`.
3. A page that fails is saved by hand (Ctrl+S, "Webpage, HTML only");
   `obtained_by=browser_save`.

`check-saves` passes a file when it decodes as `windows-1252`, has the item heading and the
Tracking Status section, is over ~10 KB, and is not an Akamai "Access Denied" page. Any id
on the expected list without a passing file is printed, and the stage exits non-zero.

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
  1512-2025 → Ch 629, in force 2027-05-01). Missing → the stage writes a draft paired by
  heading similarity and exits. Coverage check: every new § maps to an old § or says `new`;
  every old § maps to a new § or says `repealed`. A replacement already in force needs no
  map.

## Embedding spend

- `voyage-4-large`, ~2–3M tokens, ≈ $0.25–0.40 at list price; in practice $0 inside
  Voyage's 200M free tokens.
- Paid by a **separate Voyage key used only by ingestion**, calling Voyage directly (not
  AI Gateway), so it draws on the free tokens for certain and never touches the demo's $5
  prepaid credit ([`GUARDRAILS.md`](GUARDRAILS.md#spend)). Account spend limit ~$2.
- `embed` prints the token count and cost estimate and asks before spending.
- Cached by `(model, sha256 of chunk text)`: a re-run pays only for changed chunks. It
  throttles itself and resumes from the cache, so it works with or without a card on the
  Voyage account (a card only makes it faster).
- Query-time embeddings stay on Gateway under the $5 credit ([`STACK.md`](STACK.md#embeddings)).

## Smoke check before `swap`

`smoke` runs against the `staging` schema and fails loudly on any of:

1. **Counts:** chunk count within ±10% of `build/chunks.jsonl`; every manifest row
   produced at least one chunk; no chunk without an embedding; no U+FFFD anywhere (a
   `windows-1252` decode went wrong).
2. **Pins:** five fixed section lookups (e.g. `§ 681-4`, `§ 591-2`, a Ch 497 § from the
   replacement) return the expected chunk ids.
3. **Dev split:** the 10-question dev split ([`EVALS.md`](EVALS.md#refusal-threshold)) through `/api/ask` on a local `next dev` with
   `DB_SCHEMA=staging` and the eval header. It must score at least what the previous
   snapshot scored, or meet the refusal-threshold calibration bar on the first run.

The full eval set and the experiment ladder ([`evals/LADDER.md`](evals/LADDER.md)) run
**after** `swap`, as evidence, not as a gate.
