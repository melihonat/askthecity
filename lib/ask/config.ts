import type { RungConfig, Snapshot } from "./types";

// Must match the corpus (ingest/config.py); checked against the snapshot row at startup.
export const EMBEDDING = { gatewayModel: "voyage/voyage-4-large", corpusModel: "voyage-4-large", dim: 1024 };

export const CONTEXT_PASSAGES = 5; // the model sees [1]–[5]
export const MAX_OUTPUT_TOKENS = 400;

// The tracer path: vector search, top 5 by rank, no rerank, gate or companions yet.
export const DEFAULT_CONFIG: RungConfig = {
  search: "vector",
  rerank: false,
  companions: false,
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
