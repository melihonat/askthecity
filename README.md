# Ask the City

Ask a question about Toronto's by-laws and get an answer that cites the exact section,
or a plain "the documents don't cover this" when they don't.

**[Try it](https://ask-the-city.vercel.app)** · **[Evals](https://ask-the-city.vercel.app/evals)** · [How it works](#how-it-works)

Try: "How late can my neighbour run a leaf blower?" · "What does § 591-2.1 say?" ·
"Can I park on Abell Street overnight?" ← should be refused, and say why

<!-- headline:start (generated from evals/runs, do not edit) -->
| | refuses trick questions | cite precision | answer correct |
| --- | --- | --- | --- |
| vector search only | – | – | – |
| **shipped** | **–** | **–** | **–** |
<!-- headline:end -->

## Evals

<!-- ladder:start (generated from evals/runs, do not edit) -->
No test-split run is committed yet.
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
