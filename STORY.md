# README and eval-page copy

The words a 3-minute reader sees: the README's order and first screen, and the copy on the
`/evals` page. Decided in
[⑭ The README and the 3-minute story](.scratch/ask-the-city/issues/14-readme-and-story.md).
Layout of `/evals` is in [`UI.md`](UI.md#evals); columns and noise rules in
[`EVALS.md`](EVALS.md); rungs in [`evals/LADDER.md`](evals/LADDER.md).

Numbers are never hand-typed. Every number below comes from the same run data as
`evals/RESULTS.md`.

## README

### First screen

Everything above the first scroll:

```markdown
# Ask the City

Ask a question about Toronto's by-laws and get an answer that cites the exact section,
or a plain "the documents don't cover this" when they don't.

**[Try it](<demo url>)** · **[Evals](<demo url>/evals)** · [How it works](#how-it-works)

Try: "How late can my neighbour run a leaf blower?" · "What does § 591-2.1 say?" ·
"Can I park on Abell Street overnight?" ← should be refused, and say why

<!-- headline:start (generated from evals/runs, do not edit) -->
| | refuses trick questions | cite precision | answer correct |
| --- | --- | --- | --- |
| vector search only | x / 7 | x.xx | x.xx |
| **shipped** | **x / 7** | **x.xx** | **x.xx** |
<!-- headline:end -->

24 questions written before the first build; full ladder below.
```

- The headline block compares `dense` with the passing `shipped*` rung. The harness
  rewrites it between the markers when it regenerates `RESULTS.md`.
- The three example questions mirror the UI's chips; swap them together.

### Order after the first screen

1. **Evals.** The main ladder and side table with the same words as `/evals` (below), plus:
   "Every rung was run on the final code in one sitting, switching parts off by flag. It's
   a reconstruction of the build, not its history." Links to `RESULTS.md` (all 12
   columns), `EVALS.md`, `LADDER.md`.
2. **How it works.** One diagram, then one line per box:

   ```
   OFFLINE (Python, run once)                       QUERY (TypeScript, Vercel)
   Code PDFs + by-laws + IE item pages              question
     → extract (pdfplumber) → § chunks                → search_chunks RPC:
     → embed (voyage-4-large)                            § pin + FTS + vector, RRF
     → Postgres (Supabase)  ───────────────────────►  → rerank-3 20→5  (low score → refuse)
                                                      → Haiku 5.5 → validate [n] citations
   eval harness ──── HTTP ────► the same /api/ask    → answer | refusal | limit
   ```
3. **What it knows.** The scope sentence from ③ verbatim, then: "Parking schedules and
   zoning are left out on purpose; they're the obvious trick questions."
4. **Why Postgres and not Pinecone.** Its own short section, ⑥'s Neuraflow paragraph
   verbatim (in
   [⑥'s resolution](.scratch/ask-the-city/issues/06-retrieval-stack.md)).
5. **Decisions.** One line each linking `CHUNKING.md`, `CONTRACT.md`, `EVALS.md`,
   `evals/LADDER.md`, `UI.md`.
6. **Cost.** ≈ $0.0011 per answer, $5 prepaid hard cap, daily limits, and what the demo
   does when it's out of money (examples and evals still work).
7. **Operations.** The keep-alive crons, and: "GitHub disables scheduled workflows after 60
   days without a commit. If the DB health check stops, re-enable it in Actions."
8. **Data and licence.** Code MIT. City of Toronto text is not in this repo, only a
   manifest of URLs and dates; the snapshot date.

## `/evals` page

### Intro line

> 24 questions written before the first build, 7 of them meant to be refused. Each row adds
> one thing to the row above, all run on the same final code.

### Columns

Six on the page, each with its `n` under the heading:

trick questions refused · false refusals · hit@ctx · cite precision · answer correct ·
total p50

recall@20, full@20, full@ctx, cite full, coverage and passages p50 stay in `RESULTS.md`,
linked under the table. The reranker's effect is told by the refusal columns, not the
recall@20 → hit@ctx gap.

### Main ladder: why lines

Muted, one under each rung name.

| Rung | Why line |
| --- | --- |
| `dense` | Vector search only: embed the question, take the 5 closest passages. |
| `hybrid` | Adds keyword search and exact section-number matching, so "591-2.1" finds § 591-2.1. |
| `rerank` | A reranker scores every passage against the question; if none scores high enough, it refuses before the model writes anything. |
| `shipped` | Brings in the by-laws that amended a cited section after the Code was last consolidated. |
| `shipped-2`, `shipped-3` | Fix: <one-line change>. Re-run beside `shipped` on the new code. |

### Gains and no gains

- A cell whose change from the row above is inside the run-to-run spread shows a muted `≈`
  and is never bold. Only gains beyond the spread are bold.
- A rung with no gain in any column keeps its row; its why line ends "— no measurable
  gain."
- The highlight sits on the `shipped*` rung that passes the ship bar.

### Under the table

> Generation columns are the mean of 3 runs. A row only counts as better when the gain is
> bigger than its own run-to-run spread; `≈` marks changes inside it. Answers were graded
> by Sonnet 5 against key facts written with the questions; on the first full run it agreed
> with my hand grading on x of y facts (z%).

### Side table

> Alternatives tried against `shipped`, one change each.

| Rung | Why line |
| --- | --- |
| `side-sonnet` | Sonnet 5 instead of Haiku 5.5, at ~3–5× the generation cost. |
| `side-quoted` | Asks the model to quote the supporting sentence for every citation. |

### Header link

`Evals · x/7 trick questions refused`, from the passing `shipped*` rung's refusal recall.
