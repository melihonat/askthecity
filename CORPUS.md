# Corpus

What the snapshot contains, what it leaves out, and what may be published. How it is fetched
is in [`INGESTION.md`](INGESTION.md); how it is chunked is in [`CHUNKING.md`](CHUNKING.md).
Terms are defined in [`CONTEXT.md`](CONTEXT.md).

## Rules: the Toronto Municipal Code

- **Every chapter PDF** linked from `lawmcode.htm` (128 on 2026-10-28, 9 of them one-page
  "Reserved" stubs that are fetched and recorded but yield no chunks), plus **Ch 611**, which
  exists only as By-law 1513-2025. The whole Code rather than a curated set, so a refusal
  means "the Code is silent", not "we left that chapter out".
- **Schedules printed inside a chapter PDF** after its last § are in, as their own chunks
  (36 chapters, ~78k tokens: Ch 349's prohibited animals, Ch 610's penalty amounts, Ch 415's
  development-charge rates).
- **Out:** separately published schedule and map appendices (Ch 950's 44 parking schedules
  included) and the legacy former-City (C285, C313) and Etobicoke codes.
- **Schedules have no structured lookup.** Ch 950's main text stays, so the general parking
  rule is answered and the street-specific one refused. A lookup over the Open Data
  schedules would be a second system (street matching, routing, its own evals) for one
  question family; the scope sentence names the gap instead.

## Rules: amendments since consolidation

Consolidated chapters lag their amendments, so amending by-laws are ingested and every chunk
is dated.

- **In:** every by-law enacted after a chapter's footer date whose title amends that
  chapter, found by scanning the yearly `law-lists/YYYY-laws.htm` titles for "Chapter NNN"
  (not the Recent Amendments column, which misses some, e.g. 470-2026). By-laws that amend
  schedules only are dropped. That leaves **80** main-text amending by-laws
  ([`CHUNKING.md`](CHUNKING.md#rules-amending-by-laws)).
- Every Code chunk carries `consolidated_as_of` (the footer date). A citation to a chapter
  with a later ingested by-law shows "amended since by By-law NNN-YYYY" with its link.
- By-laws carry `in_force` where it differs from enactment (Ch 611: May 1, 2027), and
  answers say so. How an amended § is answered is in [`CONTRACT.md`](CONTRACT.md).

## Decisions: one committee, one term

- **Infrastructure and Environment Committee, meetings IE24–IE31 (Sep 2025–Jul 2026),
  115 items.** The term ended with the Oct 2026 election, so the window is closed and
  stable.
- **Per item: the item page plus its staff reports.** The item page carries the Council
  decision, committee recommendations, summary, per-stage status, motions, roll-call votes
  and the by-law back-link. Staff reports are the `bgrd/` files the item page labels as
  reports, supplementary reports included.
- **Out:** attachments (maps, studies, tables; image-heavy, often scanned) and
  **communications** (residents' letters with private names: a privacy problem in a public
  demo, and not the City's position). Report vs attachment is decided by the item page's
  label for each file.

## Snapshot date

A rule, not a date: the day the ingestion run fetches the Code and by-laws. The 115 item
pages are saved within 7 days of it, and the manifest records the real per-file dates.

## Copyright

The source text is © City of Toronto. Asked by email, the City confirmed (2026-10-28) that
short quoted passages from the Code and TMMIS records in this non-commercial demo, with
attribution and links back to toronto.ca and without redistributing the documents, are fine.

- **Committed (public):** code, the snapshot manifest, the eval set and result tables.
- **Never committed:** raw PDFs, saved item pages, extracted text. They live in a gitignored
  `corpus/` and a private copy ([`INGESTION.md`](INGESTION.md#where-things-live)), which is
  required: the City overwrites URLs in place, and item pages can't be re-fetched by script.
- Postgres holds chunk text; the app shows short cited passages beside the City URL.
- Footer in the UI and README: "Source documents © City of Toronto. Quoted for reference.
  Official versions at toronto.ca."

## Scope sentence

Shown in the UI (it may split into a header line plus an expandable "what's included") and
quoted in the README:

> Knows the Toronto Municipal Code, including by-laws that have amended it since, and the
> Infrastructure and Environment Committee's decisions and staff reports from September
> 2025 to July 2026, as of <date>. It doesn't cover street-by-street parking schedules,
> zoning, or other City documents.

Zoning is named because By-law 569-2013 sits outside the Code, and fence, deck and basement
questions will hit it.

## Size

About 1.2M tokens of Code, 0.29M of amending by-laws, and an estimated 0.5–1.5M of item
pages and staff reports: roughly 2–3M tokens, well inside Supabase Free.
