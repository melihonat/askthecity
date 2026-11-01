# Extraction and chunking

How the snapshot's documents become chunks, as tested on real samples of the Code, amending
by-laws and item pages. What enters the corpus is in [`CORPUS.md`](CORPUS.md). Terms are defined in [`CONTEXT.md`](CONTEXT.md).

## Engine

**pdfplumber** for every PDF: text lines with font name and position, and table cells. It
keeps `(1)`/`(a)` labels with their text and reads table decimals correctly, where PyMuPDF's
table finder corrupts them. **BeautifulSoup** (`windows-1252`) for saved item pages. PDF
bookmarks are not used: page numbers come from extraction, so `…pdf#page=N` works for every
chapter, including the 21 without § bookmarks.

## Budget

- Ceiling **~800 tokens** of body text per chunk (cl100k count). No minimum: a 40-token §
  stays its own chunk.
- **No overlap.** Each chunk instead starts with a **breadcrumb** header that is embedded and
  indexed with the body (not shown as body text in the UI).

## Rules: Municipal Code chapters

1. **Drop** the 9 "Reserved" stubs (one page, no sections), the running header (top 62 pt),
   the footer after reading its date as `consolidated_as_of`, footnotes (under 11 pt), the
   page-1 table of contents (bold § lines before the body starts) and each article's
   `[Adopted …]` note. The footer is the page-number line (`681-12 May 21, 2026`) in the
   bottom 75 pt; position alone can't tell it from body text, which reaches 71 pt from the
   bottom. Five chapters (39, 95, 433, 789, 835) print no date: their chunks say
   "consolidation date not printed". The chapter number comes from the manifest ref, the
   title from the running header (`CHAPTER 591, NOISE`, `CHAPTER 142 LOCAL APPEAL BODY`, or
   only `TAXATION, VACANT HOME TAX`).
2. **Section boundary** = a bold line at the left margin matching
   `^§\s*(\d+[A-Z]?-\d+(?:\.\d+)*[A-Z]?)\.?\s+(.*)`. Inline references are regular weight
   and never split. Article headings are tracked for the breadcrumb.
3. **Chunk unit = one §.** Empty sections (schedule stubs, repealed, reserved: nothing but
   a bracketed note) are dropped. A note that starts on the heading line belongs to the body.
4. **A § over the ceiling** splits at its top-level subsections (`A.`, `B.`, … at x≈72),
   packing consecutive subsections up to the ceiling. The chunk records the range
   (`C–D`). A single subsection still over the ceiling splits at its next level the same
   way (`C(1)–C(3)`, then `C(3)(a)–C(3)(k)`). Levels are `A.`/`A.1.`, `1.`, `(1)`, `(a)`; a
   label counts only if it continues its sequence, and the level whose sequence starts
   first wins (a `1.` list can sit inside a `(8)`). **Definitions** sections split into
   runs of whole defined terms (`TERM - …` paragraphs at a shared indent); the range names
   the first and last term. With no structure left, whole paragraphs are packed (`C(3),
   part 2`), and a single paragraph over the ceiling splits at sentences, then words.
5. **A heading never separates from its body**; a subsection's lead-in line stays with its
   first item, and a table's title or lead-in moves with the table.
6. **Tables**: cells from pdfplumber, rendered as markdown inside the chunk of the
   subsection they belong to; their region is removed from the line text so they don't
   appear twice. Two-column-pair layouts (Ch 681 Table 2) unfold into one row per
   parameter; empty rows are dropped. A table over the ceiling fills the current chunk row
   by row and carries on in the next, repeating its header row; one that fits alone but not
   beside the text before it starts the next chunk. Footnote markers (`mg/L5`) are kept
   as-is.
7. **Lists** stay with their parent clause. **`[Amended … by By-law …]`** notes stay in the
   text and are also parsed into `amended_by`.
8. **Schedules and appendices** printed after the last § (`Schedule A …`, `Appendix A …`)
   are their own units: id `tmc:349:schedule-a`, label `Ch 349 Schedule A`, no `section`
   (so never pinned), split like a §.

Breadcrumb:

```
[Toronto Municipal Code › Ch 608 Parks › Article IV Games, Sports and Organized Activities › § 608-19 Model aircraft and rockets]
[consolidated as of 2024-06-03 · amended since by By-law 1482-2025]
```

`amended since` is per §: every chunk of a § some linked by-law targets.

## Rules: amending by-laws

**Which** (`fetch-bylaws`): a by-law in the 2019–2026 yearly lists whose title names a
snapshot Chapter N ("Municipal Code … Chapter N"), numbered in or after N's consolidated-as-of
year, and whose title names no street, address or ward (`respecting Beverly Glen Boulevard`,
`municipally known as …`). Whole-chapter replacements and new chapters are left to the
replacement rules below.

**Linked** (`chunk`, `ingest/link.py`): a fetched by-law amends N *since* its consolidation
only if its number is **absent from N's own bracketed notes** (`[Amended …]`, `[Added …]`,
`[History: …]`, read across wrapped lines) and it **took effect after** N's consolidated-as-of
date (the later of enactment and in-force; a consolidation includes what took effect that
day). By-laws whose targeted instructions all name a Schedule or Appendix are dropped, as are
the schedule-only clauses of the rest. Dropped by-laws go to `build/skipped.jsonl` with the
reason. On 2026-10-29: 151 fetched, 89 already folded in, 10 schedule-only, 1 with no live
clause, **51 in** (157 chunks, ~47k tokens), 201 `amendments` rows over 163 §§. The Code had
been re-consolidated since the prototype count (80 in): Ch 681 now carries 470-2026, Ch 813
carries 402-2026's tree rules.

**Chunks:** one chunk per **operative clause** (`bl:1482-2025:cl1`), however short, so a
clause's id is stable and a companion is no wider than the clause that amends the §. The
in-force clause ("This by-law comes into force on …") is not a chunk; its date goes on every
chunk. A clause over the ceiling splits at its lettered items (`A.`, `a.` or `(a)` at the
indent of its first item; items quoted inside the new text sit deeper and stay put), packed up
to the ceiling: `bl:1482-2025:cl1:O-Y`. The authority preamble, the recitals ("Whereas …"),
the signature and anything after it (attachments: new schedules, maps, whole new chapters)
are not chunked. Clauses some PDFs lay out as a one-text-cell-per-row table are read back as
lines.

Each chunk records `amends`, parsed from its **instruction paragraphs** only (those that
amend, delete, add, insert, replace, repeal …; never the quoted words they insert): "Subsection
681-4(J)" → `§ 681-4(J)`, "subsection § 629-38F" → `§ 629-38 F` (the letter is a subsection
unless the snapshot has a § 629-38F), "§ 610-6.2.A." → `§ 610-6.2 A`. Only chapters the
by-law names count, and only §§ the snapshot has. The document records `enacted` ("Enacted and
passed on …") and `in_force` when the by-law says it differs ("comes into force on January 1,
2027"; also retroactive dates).

**Whole-chapter replacement** (`ingest/replace.py`; 1511-2025 → Ch 497, 1512-2025 → Ch 629):
`fetch-bylaws` takes a title that repeals Chapter N and replaces it "with new Chapter N",
numbered in or after N's consolidated-as-of year (a new chapter with no old one, 1513-2025 →
Ch 611, is out). The new chapter set out in the by-law's **Schedule A** runs through the
chapter splitter as Chapter N; the by-law's own clauses are not chunked. Its chunks carry the
by-law as source (`kind = replacement_bylaw`, href to the by-law PDF) and its `in_force` date.
**It supersedes only once in force:**

- **In force on the snapshot date**: the stale consolidated PDF is dropped and the
  replacement's §§ take `tmc:` ids. Amending by-laws link to it as to its chapter, with its
  in-force date as the consolidation date. If the City has already re-consolidated the
  chapter with it (the number is in the chapter's notes, or the consolidation is dated on or
  after its in-force date), the chapter stays and the by-law is dropped. That is 1511-2025
  (in force 2026-06-01): Ch 497 was re-consolidated as of that day, so `fetch-bylaws` doesn't
  even fetch it (2025 is before the consolidation year).
- **Not yet in force** (1512-2025, 2027-05-01): the consolidated chapter stays the law. The
  replacement's §§ get `bl:<n>:<§>` ids and are recorded in `amendments` against the old §
  each one replaces, from the hand-reviewed old → new § map
  ([`INGESTION.md`](INGESTION.md#hand-review-inputs); numbering changes, e.g. 629-38 →
  629-4.25), so they arrive as companion passages. An old § the map says is `repealed` has
  no companion; its sublabel says so instead. The answer reads "today X; from <in_force>, Y".

Not yet in force, the new § and the old § it replaces:

```
[By-law 1512-2025 › new Ch 629 Property Standards › Article 4 Standards › § 629-4.25 Heating and cooling]
[enacted 2025-12-17 · in force 2027-05-01, not yet law · replaces § 629-38]
sublabel: By-law 1512-2025 · in force 2027-05-01, not yet law

[Toronto Municipal Code › Ch 629 Property Standards › Article IV Standards › § 629-38 Heating and air conditioning]
[consolidated as of 2025-04-30 · amended since by By-law 67-2026 · replaced by § 629-4.25 of By-law 1512-2025 from 2027-05-01]
sublabel: consolidated 2025-04-30 · replaced 2027-05-01 by By-law 1512-2025   (or "repealed …")
```

A § heading that wraps onto a second bold line ("… other similar parts of" / "buildings and
structures.") is joined back into one heading, in chapters and replacements alike.

Breadcrumb:

```
[By-law 1482-2025 › To amend City of Toronto Municipal Code Chapter 608 Parks.]
[amends Ch 608 Parks § 608-8.1 B, § 608-19, … · enacted 2025-12-17 · in force 2026-03-02]
```

## Decisions: what enters

- **Item page**, read as `windows-1252`. **Communications and Speakers blocks are stripped**
  (they name members of the public). Motions and Votes stay.
- **Staff reports only**, chosen by the label the item page gives each `bgrd/` link in its
  Background Information: in = `Report from …`, `Supplementary Report from …`; out =
  `Attachment(s) …`, `Letter from Councillor …`, anything under `/comm/`. **Any other label
  is flagged** by `fetch-reports` for a hand decision in `snapshot/review/report_labels.csv`,
  not guessed. The decisions so far: a report bundled with its attachments (`Report and
  Attachment 1 from …`) and a lowercase `Supplementary report …` are in; a `Revised Report …`
  is in and the original it replaces on the same item is out; presentations, letters from
  Council or the Mayor, answers to Administrative Inquiries, notices and schedules are out.

## Decisions: item pages

- Under the ceiling: one chunk. Otherwise one chunk per `h4` block (Council Decision,
  Committee Recommendations / Committee Decision, Decision Advice, Origin + Summary, Motions
  + Votes), packed up to the ceiling. Blocks of different stages never share a chunk.
- Ids: `ie:2026.IE29.6:council`, `ie:2026.IE29.6:committee`; a stage split over the ceiling
  numbers its chunks (`ie:2025.IE24.13:committee:1`, `:2`, …). An h4 block with no text of
  its own ("2a - Supplementary Report …") prefixes the next block's heading.
- Labels name the stage: `City Council decision`, `IE Committee recommendation` (the card has
  Committee Recommendations, so Council decided), or `IE Committee decision`.
- **Every Decisions chunk carries the item's status stamp**, staff-report chunks included,
  built from the newest Tracking Status line and its `See also By-law` line. A referred or
  deferred item then never reads as adopted. The stamp names who did what and when, then any
  by-laws, and an undecided item's stamp **ends with `; no decision`** (deferred, referred,
  received for information, ruled out of order). An unknown Tracking Status sentence, or an
  item still awaiting Council, stops the stage.

Breadcrumb:

```
[IE Committee item 2025.IE26.14 · Electricity and Toronto's Climate Commitments › Committee Decision]
[Status: Referred by IE Committee 2025-12-04; no decision]
```

## Decisions: staff reports

Split at the template's size-13 bold all-caps majors (SUMMARY, RECOMMENDATIONS, FINANCIAL
IMPACT, DECISION HISTORY, COMMENTS, and any other, e.g. EQUITY IMPACT STATEMENT): one chunk
per major. A major over the ceiling packs its bold title-case subheads (size 12 or 13) up to
the ceiling. A subhead stands alone; a bold line the paragraph runs on from ("Stage 1: An
initial screening which …") is text. A subhead with no text before the next joins it
(`Background › Objectives …`). The title block before SUMMARY, the footers and footnotes
(under 11 pt), and CONTACT, SIGNATURE and ATTACHMENTS are dropped; attachments bundled into
the PDF sit under ATTACHMENTS, so they go too. Tables as in the Code.

- Ids: `sr:286369:summary`; a major split over the ceiling numbers its chunks
  (`sr:286369:comments:1`, `:2`, …).
- Label `Staff report · 2026.IE29.6 › COMMENTS › Review of Manganese Quality Limit in Sewers
  By-law` (`(2/7)` when split), sublabel the item's status stamp, href the report PDF
  `#page=<page_start>`. The prompt says a staff report is what staff recommended, not what
  was decided.

```
[Staff report for 2026.IE29.6 · Amending the Foundation Drainage Policy … › COMMENTS › Review of Manganese Quality Limit]
[Status: Adopted with amendments by City Council 2026-05-21 · By-law 470-2026]
```

## Metadata per chunk

| Field | Code § | Amending by-law | Item page | Staff report |
| --- | --- | --- | --- | --- |
| `family` | rules | rules | decisions | decisions |
| `doc_id`, `source_url`, `page_start`/`page_end` | ✓ | ✓ | ✓ (no pages) | ✓ |
| `chapter`, `article`, `section`, `subsection_range`, `heading` | ✓ | `amends[]` | — | `heading` |
| `consolidated_as_of` | ✓ | — | — | — |
| `amended_by[]` (folded in) / `amended_since[]` (ingested, later) | ✓ | — | — | — |
| `enacted`, `in_force` | — | ✓ | — | — |
| `item_id`, `committee`, `meeting`, `stage`, `status`, `decision_date`, `bylaws[]` | — | — | ✓ | ✓ |
| `breadcrumb`, `text`, `tokens` | ✓ | ✓ | ✓ | ✓ |

How these land in Postgres, and how a citation is shaped from them, is in [`CONTRACT.md`](CONTRACT.md).
