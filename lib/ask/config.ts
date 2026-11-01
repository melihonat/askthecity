import type { Rung, RungConfig, Snapshot } from "./types";

// Must match the corpus (ingest/config.py); checked against the snapshot row at startup.
export const EMBEDDING = { gatewayModel: "voyage/voyage-4-large", corpusModel: "voyage-4-large", dim: 1024 };

export const CANDIDATES = 20; // fused candidates from search_chunks, reranked to CONTEXT_PASSAGES
export const CONTEXT_PASSAGES = 5; // the model sees [1]–[5]
export const MAX_COMPANIONS = 3; // then up to 3 companion passages, [6]…
export const MAX_OUTPUT_TOKENS = 400;

export const MAX_QUESTION = 300; // characters; longer is the `too_long` limit

export const RERANK_MODEL = "voyage/rerank-3";

// Permissive: catches clearly off-corpus questions only. Set by `python -m evals calibrate` from
// a dev run, never by hand (EVALS.md, "Refusal threshold"); it is part of the answer-cache key.
export const REFUSAL_THRESHOLD = 0.359;

const MODEL = "anthropic/claude-haiku-5.5";
const SHIPPED: RungConfig = { search: "hybrid", rerank: true, companions: true, model: MODEL, prompt: "default" };

// evals/LADDER.md. The main ladder is cumulative, one component per rung, ending at `shipped`;
// each side rung changes one thing on `shipped`. A closed set of presets read by the one
// orchestration path; no free-form knobs.
export const RUNGS: Record<Rung, RungConfig> = {
  dense: { search: "vector", rerank: false, companions: false, model: MODEL, prompt: "default" },
  hybrid: { search: "hybrid", rerank: false, companions: false, model: MODEL, prompt: "default" },
  rerank: { search: "hybrid", rerank: true, companions: false, model: MODEL, prompt: "default" },
  shipped: SHIPPED,
  // the fix rung under `shipped` (LADDER.md, "Ship bar"): cite precision and the rule in force
  "shipped-2": { ...SHIPPED, prompt: "fix" },
  // Sonnet 5.5 can't turn thinking off, so its thinking shares the cap; 400 cut long answers mid-JSON
  "side-sonnet": { ...SHIPPED, model: "anthropic/claude-sonnet-5.5", maxOutputTokens: 1600 },
  // the quotes get their own room, so quoting can't cut the answer short
  "side-quoted": { ...SHIPPED, prompt: "quoted", maxOutputTokens: 1200 },
};

export function isRung(value: unknown): value is Rung {
  return typeof value === "string" && Object.hasOwn(RUNGS, value);
}

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
