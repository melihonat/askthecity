import { CONTEXT_PASSAGES, REFUSAL_THRESHOLD } from "./config";
import { systemPrompt, userPrompt } from "./prompt";
import type { AskEvent, DebugEvent, ModelOutput, PassageView, RungConfig, SearchRow, Snapshot } from "./types";
import { NEAREST, validate } from "./validate";

export type AskDeps = {
  snapshot(): Promise<Snapshot>;
  embed(question: string): Promise<number[]>;
  search(question: string, embedding: number[], mode: RungConfig["search"]): Promise<SearchRow[]>;
  /** One relevance score per document, in input order. */
  rerank(question: string, documents: string[]): Promise<number[]>;
  generate(req: { model: string; system: string; prompt: string }): Promise<ModelOutput>;
};

export type AskOptions = { debug?: boolean };

export function toPassage(row: SearchRow, n: number): PassageView {
  return {
    n,
    chunkId: row.id,
    companion: false,
    family: row.family,
    label: row.label,
    sublabel: row.sublabel,
    href: row.href,
    amendedSince: row.amended_since ?? [],
    body: row.body,
  };
}

/** Pins keep their place at the top; the rest by rerank score, ties in fused order. */
function byRerank(rows: SearchRow[], scores: number[]): SearchRow[] {
  return rows
    .map((row, i) => ({ row, score: scores[i], i }))
    .sort((a, b) => Number(b.row.pinned) - Number(a.row.pinned) || b.score - a.score || a.i - b.i)
    .map((x) => x.row);
}

/**
 * The one orchestration path: embed → search → rerank → gate → generate → validate.
 * With rerank off the top 5 are by fused rank and the gate is off; a pin skips the gate.
 */
export async function* ask(
  question: string,
  config: RungConfig,
  deps: AskDeps,
  opts: AskOptions = {},
): AsyncGenerator<AskEvent> {
  const t0 = performance.now();
  const snapshot = await deps.snapshot();
  const embedding = await deps.embed(question);
  const rows = await deps.search(question, embedding, config.search);
  const t1 = performance.now();

  const scores = config.rerank && rows.length ? await deps.rerank(question, rows.map((r) => `${r.label}\n${r.body}`)) : null;
  const t2 = performance.now();

  const ranked = scores ? byRerank(rows, scores) : rows;
  const passages = ranked.slice(0, CONTEXT_PASSAGES).map((r, i) => toPassage(r, i + 1));
  yield { type: "passages", passages };

  const pinned = rows.filter((r) => r.pinned).map((r) => r.id);
  const gateScore = config.rerank ? Math.max(0, ...(scores ?? [])) : null;
  const gateBypassed = pinned.length > 0;
  const debug = (declineText: string | null, generation_ms: number | null): DebugEvent => ({
    candidates: rows.map((r, i) => ({ chunkId: r.id, rrfRank: r.rank, rerankScore: scores?.[i] ?? null })),
    pinned,
    gateScore,
    threshold: REFUSAL_THRESHOLD,
    gateBypassed,
    declineText,
    timings: {
      retrieval_ms: Math.round(t1 - t0),
      rerank_ms: Math.round(t2 - t1),
      generation_ms,
      total_ms: Math.round(performance.now() - t0),
    },
  });

  if (gateScore !== null && !gateBypassed && gateScore < REFUSAL_THRESHOLD) {
    if (opts.debug) yield { type: "debug", debug: debug(null, null) };
    yield {
      type: "final",
      response: { kind: "refusal", reason: "below_threshold", scope: snapshot.scope_sentence, nearest: passages.slice(0, NEAREST) },
    };
    return;
  }

  const t3 = performance.now();
  const output = await deps.generate({
    model: config.model,
    system: systemPrompt(snapshot.snapshot_date),
    prompt: userPrompt(question, passages),
  });
  const generation_ms = Math.round(performance.now() - t3);
  const response = validate(output, passages, snapshot.scope_sentence);

  if (opts.debug) yield { type: "debug", debug: debug(output.decision === "decline" ? output.text : null, generation_ms) };
  yield { type: "final", response };
}
