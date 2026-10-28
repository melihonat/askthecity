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
[Toronto Municipal Code › Ch 681 Sewers › Article I › § 681-5 Pollution prevention planning (C–D)]
[consolidated as of 2023-05-15 · amended since by By-law 470-2026]
```

## Rules: amending by-laws

**Which:** a by-law in the 2019–2026 yearly lists whose title names Chapter N, enacted in or
after N's consolidated-as-of year, and whose number is **absent from N's own `[Amended …]`
notes**. Then drop titles naming a street or address, and drop by-laws whose numbered
operative clauses all touch a Schedule or Appendix. At prototype time: 120 candidates, 40
schedule-only, **80 in** (~287k tokens).

**Chunks:** a by-law under the ceiling is one chunk; a bigger one splits by numbered
operative clause. Each chunk records `amends: [{chapter, section}]` parsed from clause text
("Subsection 681-4(J)" → `681`, `681-4 J`), plus `enacted`, and `in_force` when the by-law
says it differs ("comes into force on January 1, 2027").

**Whole-chapter replacement** (1511-2025 → Ch 497, 1512-2025 → Ch 629): the by-law runs
through the chapter splitter as that chapter. Its chunks carry the by-law as source and its
`in_force` date. **It supersedes only once in force:**

- **In force on the snapshot date** (1511-2025, 2026-06-01): the stale consolidated PDF is
  dropped and the replacement's §§ take `tmc:` ids.
- **Not yet in force** (1512-2025, 2027-05-01): the consolidated chapter stays as the law.
  The replacement's §§ get `bl:<n>:<§>` ids and are recorded in `amendments` against the
  old § each one replaces (a hand-reviewed old → new § map; numbering changes, e.g.
  629-38 → 629-4.25), so they arrive as companion passages. The answer reads "today X;
  from <in_force>, Y".

Breadcrumb:

```
[By-law 470-2026 › amends Ch 681 Sewers § 681-4 J · enacted 2026-05-21 · in force on enactment]
```

## Decisions: what enters

- **Item page**, read as `windows-1252`. **Communications and Speakers blocks are stripped**
  (they name members of the public). Motions and Votes stay.
- **Staff reports only**, chosen by the label the item page gives each `bgrd/` link:
  in = `Report from …`, `Supplementary Report from …`; out = `Attachment …`, `Letter from
  Councillor …`, anything under `/comm/`. **Any other label is flagged** for a hand decision
  during the save step, not guessed.

## Decisions: item pages

- Under the ceiling: one chunk. Otherwise one chunk per `h4` block (Council Decision,
  Committee Recommendations / Committee Decision, Decision Advice, Origin + Summary, Motions
  + Votes), packed up to the ceiling. Blocks of different stages never share a chunk.
- **Every Decisions chunk carries the item's status stamp**, staff-report chunks included,
  built from the Tracking Status and per-stage `Status:` lines. A referred or deferred item
  then never reads as adopted.

Breadcrumb:

```
[IE Committee item 2025.IE26.14 · Electricity and Toronto's Climate Commitments › Committee Decision]
[Status: Referred by IE Committee 2025-12-04 to the Executive Director, Environment, Climate and Forestry; no decision]
```

## Decisions: staff reports

Split at the template's size-13 bold majors (SUMMARY, RECOMMENDATIONS, FINANCIAL IMPACT,
DECISION HISTORY, COMMENTS); a section over the ceiling splits at its size-12 bold subheads.
CONTACT, SIGNATURE and the ATTACHMENTS list are dropped. Tables as in the Code.

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
