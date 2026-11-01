// Shapes from CONTRACT.md. Later slices extend these; they never change their meaning.

export type Family = "rules" | "decisions";

export type PassageView = {
  n: number;
  chunkId: string;
  companion: boolean;
  family: Family;
  label: string;
  sublabel: string;
  href: string;
  amendedSince: string[]; // by-law numbers, for the badge
  notYetLaw: boolean; // a § of a replacement chapter not in force on the snapshot date
  decided: boolean | null; // Decisions: adopted, or false for "no decision"; null for the rules family
  defines: string[]; // a definition companion: the terms its body is cut to; else empty
  body: string; // display text, markdown tables kept
};

export type Citation = { n: number; chunkId: string };

export type RefusalReason = "below_threshold" | "model_declined" | "no_valid_citation";
export type LimitKind = "ip_daily" | "global_daily" | "burst" | "budget" | "too_long" | "unavailable";

export type AskResponse =
  | { kind: "answer"; text: string; citations: Citation[]; passages: PassageView[] }
  | { kind: "refusal"; reason: RefusalReason; scope: string; nearest: PassageView[] }
  | { kind: "limit"; limit: LimitKind };

/** What the orchestrator already computed; sent only under the eval header (CONTRACT.md). */
export type DebugEvent = {
  candidates: { chunkId: string; rrfRank: number; rerankScore: number | null }[]; // the 20, fused order
  pinned: string[]; // chunk ids placed by the § number match
  gateScore: number | null; // top rerank score; null with rerank off
  threshold: number;
  gateBypassed: boolean; // a pin fired, so the threshold was not applied
  declineText: string | null; // the model's text on decision = "decline"; never public
  quotes: Quote[] | null; // the `quoted` prompt's sentences; never public (CONTRACT.md: no quoted span)
  timings: { retrieval_ms: number; rerank_ms: number; generation_ms: number | null; total_ms: number };
  rung: Rung;
  config: RungConfig; // resolved from the rung
  build: { sha: string | null; promptVersion: string; promptHash: string; embedder: string; reranker: string };
};

export type AskEvent =
  | { type: "passages"; passages: PassageView[] }
  | { type: "debug"; debug: DebugEvent }
  | { type: "final"; response: AskResponse };

/** A cited passage's supporting sentence, from the `quoted` prompt only. */
export type Quote = { n: number; sentence: string };

/** What the generator returns (structured output); `quotes` only from the `quoted` prompt. */
export type ModelOutput = { decision: "answer" | "decline"; text: string; cited: number[]; quotes?: Quote[] };

/** Named configurations for the eval table (evals/LADDER.md); only the eval header selects one. */
export type Rung = "dense" | "hybrid" | "rerank" | "shipped" | "shipped-2" | "side-sonnet" | "side-quoted";

export type RungConfig = {
  search: "vector" | "hybrid"; // search_chunks mode arg
  rerank: boolean; // false: top 5 by fused rank, and the gate is off
  companions: boolean;
  model: string; // pinned id, never an alias
  prompt: "default" | "quoted" | "fix";
  maxOutputTokens?: number; // side rungs only; absent means MAX_OUTPUT_TOKENS, so `shipped` and its cache key don't change
};

/** The chunk fields a passage is built from. */
export type ChunkRow = {
  id: string;
  document_id: string;
  family: Family;
  kind: string;
  section: string | null;
  label: string;
  sublabel: string;
  href: string;
  amended_since: string[];
  body: string;
};

/** One row from the search_chunks RPC. */
export type SearchRow = ChunkRow & {
  rank: number;
  score: number; // fused RRF score: rank arithmetic, no absolute meaning
  pinned: boolean; // placed by the § number match; the gate skips on it
};

/** One row from the companion_chunks RPC: an amending chunk and the § it targets. */
export type CompanionRow = ChunkRow & { target_section: string };

/** One row from the definition_chunks RPC: a defined term, its definitions chunk cut to it. */
export type DefinitionRow = ChunkRow & { term: string; uses: number };

/** Paid questions already counted today, before this one (the use_quota RPC). */
export type Usage = { ip: number; global: number };

export type Snapshot = {
  id: string;
  snapshot_date: string;
  embed_model: string;
  embed_dim: number;
  scope_sentence: string;
};
