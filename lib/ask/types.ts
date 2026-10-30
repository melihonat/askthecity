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
  body: string; // display text, markdown tables kept
};

export type Citation = { n: number; chunkId: string };

export type RefusalReason = "below_threshold" | "model_declined" | "no_valid_citation";
export type LimitKind = "ip_daily" | "global_daily" | "burst" | "budget" | "too_long";

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
  timings: { retrieval_ms: number; rerank_ms: number; generation_ms: number | null; total_ms: number };
};

export type AskEvent =
  | { type: "passages"; passages: PassageView[] }
  | { type: "debug"; debug: DebugEvent }
  | { type: "final"; response: AskResponse };

/** What the generator returns (structured output). */
export type ModelOutput = { decision: "answer" | "decline"; text: string; cited: number[] };

export type RungConfig = {
  search: "vector" | "hybrid"; // search_chunks mode arg
  rerank: boolean; // false: top 5 by fused rank, and the gate is off
  companions: boolean;
  model: string; // pinned id, never an alias
  prompt: "default" | "quoted";
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

export type Snapshot = {
  id: string;
  snapshot_date: string;
  embed_model: string;
  embed_dim: number;
  scope_sentence: string;
};
