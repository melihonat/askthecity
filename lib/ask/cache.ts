import { createHash } from "node:crypto";
import { EMBEDDING, REFUSAL_THRESHOLD, RERANK_MODEL, RUNGS } from "./config";
import { normalise } from "./guardrails";
import { PROMPT_HASH, PROMPT_VERSION } from "./prompt";
import { EXAMPLES } from "./scope";
import type { RungConfig } from "./types";

// The answer cache (GUARDRAILS.md, "Answer cache"): exact match, no TTL. A changed key is the
// only invalidation, so everything that can change a response is in it.

/** What produced a public response: the `shipped` preset, models, prompt and refusal threshold. */
export type ConfigVersion = {
  rung: RungConfig; // includes the generation model id
  embedder: string;
  reranker: string;
  promptVersion: string;
  promptHash: string; // catches a wording change that forgot the version bump
  threshold: number;
};

export const CONFIG_VERSION: ConfigVersion = {
  rung: RUNGS.shipped,
  embedder: EMBEDDING.gatewayModel,
  reranker: RERANK_MODEL,
  promptVersion: PROMPT_VERSION,
  promptHash: PROMPT_HASH,
  threshold: REFUSAL_THRESHOLD,
};

/** sha256 of the normalised question, the snapshot id and the config version. */
export function cacheKey(question: string, snapshotId: string, config: ConfigVersion = CONFIG_VERSION): string {
  return createHash("sha256")
    .update(JSON.stringify([normalise(question), snapshotId, config]))
    .digest("hex");
}

const examples = new Set(EXAMPLES.map((e) => normalise(e.question)));

/** An example chip's question: never counted against the daily limits. */
export function isExample(question: string): boolean {
  return examples.has(normalise(question));
}
