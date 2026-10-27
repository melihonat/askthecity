# Retrieval stack

The store, models and placement behind `/api/ask`. The request and response shapes and the
refusal rule are in [`CONTRACT.md`](CONTRACT.md); spend and abuse limits are in
[`GUARDRAILS.md`](GUARDRAILS.md). Terms are defined in [`CONTEXT.md`](CONTEXT.md).

## Store: Supabase Postgres alone

pgvector plus built-in full-text search, in the one database that already holds the
citations. No Pinecone.

**The Neuraflow paragraph** (quoted in the README; no knock on Pinecone):

> Two years ago at Neuraflow I reached for Pinecone because vector search was its own
> specialised system. Today pgvector, Postgres FTS and an RRF function do hybrid search in
> the same database that holds the citations — one fewer system to keep in sync, and a
> corpus this size never needs a dedicated vector store. Pinecone now has BM25 and hosted
> reranking; I'd pick it again at tens of millions of vectors or with several teams writing
> to the index.

## Retrieval

All search runs in one SQL RPC, `search_chunks`, in one round trip:

1. **Section-number pin.** Each chunk stores its section number in its own column. A regex
   on the query (e.g. `591-2.1`, `950-1200`) matches it exactly and pins hits to the top,
   ahead of fusion. The `english` tokenizer can't be trusted with these.
2. **Lexical:** `ts_rank_cd` + `websearch_to_tsquery`. No BM25: unverified on Supabase, and
   the difference is small under a reranker.
3. **Vector:** `voyage-4-large`, `halfvec(1024)`, HNSW cosine.
4. **Fusion:** top 30 from each side, RRF `k = 60`, equal weights. The merged top 20 go to
   the reranker.

Then, in TypeScript:

5. **Rerank: Voyage `rerank-3` via AI Gateway**, 20 → 5. It ships by default because the
   refusal needs an absolute query–passage relevance score; RRF scores are rank arithmetic
   and mean nothing in absolute terms. Fallback if too slow: `rerank-3-lite`, or 10–15
   candidates.
6. **Refusal gate** on the top rerank score, before any LLM call
   ([`CONTRACT.md`](CONTRACT.md#refusal-rule)).
7. **Generate: Claude Haiku 5.5 via AI Gateway**, structured output. The model id is pinned
   in config, never a moving alias, so evals stay reproducible.

Retrieval logic lives in SQL (search and fusion) and TypeScript (orchestration), nowhere
else; the eval harness calls the same `/api/ask`.

## Embeddings

The embedding model and dimension are recorded on the snapshot. Ingestion refuses to mix
them, and `/api/ask` checks them at startup. Query embeddings go through AI Gateway;
ingestion calls Voyage directly with the same model
([`INGESTION.md`](INGESTION.md#embedding-spend)).

## Placement

One Vercel Node function, `/api/ask`, in `iad1`; Supabase in `us-east-1`. Embed →
`search_chunks` → rerank → stream generation.

## Cost and latency

- **Per question:** ≈ $0.0011 answered (generation ≈ $0.00055, rerank ≈ $0.0003–0.0006,
  embed ≈ $0.000001); a refusal at the gate ≈ $0.0005 (no generation).
- **Latency budget (p50):** embed ~150 ms, SQL ~100 ms, rerank ~400 ms; first token
  **< 1.5 s**, full answer **< 5 s**. The eval harness records time to first token and
  total per question, so latency is a column in the eval table, not a claim.
