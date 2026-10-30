import type { RungConfig, Snapshot } from "./types";

// Must match the corpus (ingest/config.py); checked against the snapshot row at startup.
export const EMBEDDING = { gatewayModel: "voyage/voyage-4-large", corpusModel: "voyage-4-large", dim: 1024 };

export const CANDIDATES = 20; // fused candidates from search_chunks, reranked to CONTEXT_PASSAGES
export const CONTEXT_PASSAGES = 5; // the model sees [1]–[5]
export const MAX_COMPANIONS = 3; // then up to 3 companion passages, [6]…
export const MAX_OUTPUT_TOKENS = 400;

export const RERANK_MODEL = "voyage/rerank-3";

// Provisional and permissive: catches clearly off-corpus questions only. Calibrated from the
// dev split later (EVALS.md, "Refusal threshold"); it is part of the answer-cache key.
// A first probe: off-topic questions ~0.28-0.30, the lowest dev answer question 0.45.
export const REFUSAL_THRESHOLD = 0.35;

// Hybrid search with § pins, reranked and gated, with companion passages.
export const DEFAULT_CONFIG: RungConfig = {
  search: "hybrid",
  rerank: true,
  companions: true,
  model: "anthropic/claude-haiku-5.5",
  prompt: "default",
};

export class CorpusMismatchError extends Error {}

/** Fails when the live corpus was embedded with a different model or dimension than queries use. */
export function checkCorpus(snapshot: Pick<Snapshot, "embed_model" | "embed_dim">): void {
  if (snapshot.embed_model !== EMBEDDING.corpusModel || snapshot.embed_dim !== EMBEDDING.dim) {
    throw new CorpusMismatchError(
      `corpus is ${snapshot.embed_model}/${snapshot.embed_dim}, queries use ` +
        `${EMBEDDING.corpusModel}/${EMBEDDING.dim}; re-ingest or change lib/ask/config.ts`,
    );
  }
}
