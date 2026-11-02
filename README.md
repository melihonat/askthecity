# Ask the City

Ask a question about Toronto's by-laws and get an answer that cites the exact section,
or a plain "the documents don't cover this" when they don't.

**[Try it](https://ask-the-city.vercel.app)** · **[Evals](https://ask-the-city.vercel.app/evals)** · [How it works](#how-it-works)

Try: "How late can my neighbour run a leaf blower?" · "What does § 591-2.1 say?" ·
"Can I park on Abell Street overnight?" ← should be refused, and say why

<!-- headline:start (generated from evals/runs, do not edit) -->
| | refuses trick questions | cite precision | answer correct |
| --- | --- | --- | --- |
| vector search only | 7 / 7 | 0.72 | 0.81 |
| **shipped** | **7 / 7** | **0.80** | **0.93** |

24 questions written before the first build; full ladder below.
<!-- headline:end -->

## Evals

<!-- ladder:start (generated from evals/runs, do not edit) -->
24 questions written before the first build, 7 of them meant to be refused. Each row adds one thing to the row above, all run on the same final code.

| Rung | trick questions refused<br><sub>n 7</sub> | false refusals<br><sub>n 17</sub> | hit@ctx<br><sub>n 15</sub> | cite precision<br><sub>n 12–15</sub> | answer correct<br><sub>n 13–17</sub> | total p50<br><sub>n 41–51</sub> |
| --- | --- | --- | --- | --- | --- | --- |
| `dense`<br><sub>Vector search only: embed the question, take the 5 closest passages.</sub> | 7 / 7 | 2 / 17 | 0.87 | 0.72 | 0.81 | 2.0 s |
| `hybrid`<br><sub>Adds keyword search and exact section-number matching, so "591-2.1" finds § 591-2.1.</sub> | 7 / 7 | 3.3 / 17 | 0.87 | **0.76** | ≈ 0.79 | **1.8 s** |
| `rerank`<br><sub>A reranker scores every passage against the question; if none scores high enough, it refuses before the model writes anything.</sub> | 7 / 7 | **0 / 17** | **1.00** | ≈ 0.76 | **0.86** | 2.1 s |
| `shipped`<br><sub>Brings in the by-laws that amended a cited section after the Code was last consolidated.</sub> | 7 / 7 | 0 / 17 | 1.00 | ≈ 0.80 | **0.93** | ≈ 2.2 s |
| `shipped`<br><sub>The same shipped stack re-run on a0e67b2, beside the fix below it: the fix is compared against this row.</sub> | 7 / 7 | 0 / 17 | 1.00 | 0.79 | 0.87 | 2.2 s |
| `shipped-2`<br><sub>Fix: the prompt cites only the passage that states each sentence, and leads with the rule in force when a by-law changed a section.</sub> | 7 / 7 | 0 / 17 | 1.00 | **0.85** | ≈ 0.90 | ≈ 2.0 s |

The rows below the first shipped row were added after it missed the ship bar. A fix runs on its own later commit, with shipped re-run beside it on that commit, and is compared against that re-run. The rows above are left as they were.

The rows below were run after the gold audit (EVALS.md, "Gold audit"): passages that state the sentence citing them, reviewed by hand from the citations of the runs above, were added to gold. They are scored against that gold and are not compared with the rows above. Their cite precision is partly in-sample: fresh answers, but to the same questions whose citations widened the gold.

| Rung | trick questions refused<br><sub>n 7</sub> | false refusals<br><sub>n 17</sub> | hit@ctx<br><sub>n 15</sub> | cite precision<br><sub>n 12–15</sub> | answer correct<br><sub>n 13–17</sub> | total p50<br><sub>n 41–51</sub> |
| --- | --- | --- | --- | --- | --- | --- |
| `shipped`<br><sub>The same shipped stack, run after the gold audit and scored against the widened gold.</sub> | 7 / 7 | 0 / 17 | 1.00 | 0.99 | 0.91 | 2.4 s |

Generation columns are the mean of 3 runs. A row only counts as better when the gain is bigger than its own run-to-run spread; ≈ marks changes inside it. Answers were graded by Sonnet 5 against key facts written with the questions; on the first full run a human grader, blind to its verdicts, agreed with it on 32 of 34 facts (94%), and marked 1 fact contradicted that the judge passed, which the ship bar's contradicted check doesn't see. Cite precision counts a cited definition the app attached as correct; that rule was added after the first full run, when the citations outside gold turned out to be mostly definitions written after the gold was (0.69 → 0.78 for shipped), and applies to every row.

Alternatives tried against `shipped`, one change each.

| Rung | trick questions refused<br><sub>n 7</sub> | false refusals<br><sub>n 17</sub> | hit@ctx<br><sub>n 15</sub> | cite precision<br><sub>n 12–15</sub> | answer correct<br><sub>n 13–17</sub> | total p50<br><sub>n 41–51</sub> |
| --- | --- | --- | --- | --- | --- | --- |
| `side-sonnet`<br><sub>Sonnet 5.5 instead of Haiku 5.5, at ~20× the generation cost.</sub> | 7 / 7 | 0 / 17 | 1.00 | 0.71 | **0.96** | 3.1 s |
| `side-quoted`<br><sub>Asks the model to quote the supporting sentence for every citation — no measurable gain.</sub> | 7 / 7 | 1 / 17 | 1.00 | ≈ 0.81 | 0.82 | 2.9 s |

<!-- ladder:end -->

Every rung was run on the final code in one sitting, switching parts off by flag. It's a
reconstruction of the build, not its history. All columns are in
[`evals/RESULTS.md`](evals/RESULTS.md); how they're scored in [`EVALS.md`](EVALS.md); the
pre-registered rungs in [`evals/LADDER.md`](evals/LADDER.md). Every number above is generated
from `evals/runs/*/run.json` by `python -m evals results`.

## How it works

```
OFFLINE (Python, run once)                       QUERY (TypeScript, Vercel)
Code PDFs + by-laws + IE item pages              question
  → extract (pdfplumber) → § chunks                → search_chunks RPC:
  → embed (voyage-4-large)                            § pin + FTS + vector, RRF
  → Postgres (Supabase)  ───────────────────────►  → rerank-3 20→5  (low score → refuse)
                                                   → Haiku 5.5 → validate [n] citations
eval harness ──── HTTP ────► the same /api/ask    → answer | refusal | limit
```

- **Extract:** the Municipal Code chapters, the by-laws that amended them since, and the
  Infrastructure and Environment Committee's item pages, split along their own sections.
- **Embed:** every chunk once, with Voyage's `voyage-4-large`.
- **Postgres:** chunks, embeddings and citations in one Supabase database.
- **search_chunks:** one SQL function: an exact § number pin, full-text search and vector
  search, fused by reciprocal rank.
- **rerank-3:** scores the top 20 against the question and keeps 5; if none scores high
  enough, the app refuses before the model writes anything.
- **Haiku 5.5:** writes the answer with `[n]` markers; any answer without a valid citation
  becomes a refusal.
- **Eval harness:** calls the same deployed `/api/ask` as the page, so the numbers measure
  what visitors get.

## What it knows

> Knows the Toronto Municipal Code, including by-laws that have amended it since, and the
> Infrastructure and Environment Committee's decisions and staff reports from September
> 2025 to July 2026, as of October 28, 2026. It doesn't cover street-by-street parking
> schedules, zoning, or other City documents.

Parking schedules and zoning are left out on purpose; they're the obvious trick questions.

## Why Postgres and not Pinecone

Two years ago at Neuraflow I reached for Pinecone because vector search was its own
specialised system. Today pgvector, Postgres FTS and an RRF function do hybrid search in
the same database that holds the citations — one fewer system to keep in sync, and a
corpus this size never needs a dedicated vector store. Pinecone now has BM25 and hosted
reranking; I'd pick it again at tens of millions of vectors or with several teams writing
to the index.

## Decisions

- [`CORPUS.md`](CORPUS.md): what's in the snapshot and what's left out.
- [`CHUNKING.md`](CHUNKING.md): how documents split into citable chunks.
- [`CONTRACT.md`](CONTRACT.md): the `/api/ask` response shape and refusal rule.
- [`STACK.md`](STACK.md): the store, models and hosting, and what they cost.
- [`GUARDRAILS.md`](GUARDRAILS.md): spend caps, rate limits and keep-alive.
- [`EVALS.md`](EVALS.md): what each eval column measures.
- [`evals/LADDER.md`](evals/LADDER.md): the pre-registered rungs and ship bar.
- [`UI.md`](UI.md): how answers, citations, refusals and limits look.
- [`INGESTION.md`](INGESTION.md): how the snapshot is built.

## Cost

About $0.0011 per answer, against a $10 prepaid AI Gateway credit with auto top-up off, and
daily limits per visitor and overall. When the money or the daily limit runs out, the demo
says so; the example questions and the evals still work.

## Operations

Two daily Vercel crons call `/api/keepalive`, which runs a real search with a stored query
embedding, so the free Supabase database never pauses and no AI credit is spent. A daily GitHub
Actions workflow calls `/api/health` and fails, e-mailing the owner, when the database is down.

GitHub disables scheduled workflows after 60 days without a commit. If the DB health check
stops, re-enable it in Actions.

## Data and licence

Code: MIT. City of Toronto text is not in this repo, only a manifest of URLs and dates
([`snapshot/manifest.csv`](snapshot/manifest.csv)). Documents as of October 28, 2026.
