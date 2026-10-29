import { CONTEXT_PASSAGES, MAX_COMPANIONS, REFUSAL_THRESHOLD } from "./config";
import { systemPrompt, userPrompt } from "./prompt";
import type {
  AskEvent,
  ChunkRow,
  CompanionRow,
  DebugEvent,
  ModelOutput,
  PassageView,
  RungConfig,
  SearchRow,
  Snapshot,
} from "./types";
import { NEAREST, validate } from "./validate";

export type AskDeps = {
  snapshot(): Promise<Snapshot>;
  embed(question: string): Promise<number[]>;
  search(question: string, embedding: number[], mode: RungConfig["search"]): Promise<SearchRow[]>;
  /** The amending chunks that target any of these §§ (the amendments table). */
  companions(sections: string[]): Promise<CompanionRow[]>;
  /** One relevance score per document, in input order. */
  rerank(question: string, documents: string[]): Promise<number[]>;
  generate(req: { model: string; system: string; prompt: string }): Promise<ModelOutput>;
};

export type AskOptions = { debug?: boolean };

export function toPassage(row: ChunkRow, n: number, companion = false): PassageView {
  return {
    n,
    chunkId: row.id,
    companion,
    family: row.family,
    label: row.label,
    sublabel: row.sublabel,
    href: row.href,
    amendedSince: row.amended_since ?? [],
    body: row.body,
  };
}

/** By-law 1482-2025 → [2025, 1482], for newest-first ordering. */
function bylawOrder(documentId: string): [number, number] {
  const [num, year] = documentId.replace(/^bl:/, "").split("-").map(Number);
  return [year || 0, num || 0];
}

/**
 * Companion passages (CONTRACT.md, "Citation"): for the passages' amended §§, the amending chunks
 * that target them, in passage order, newest by-law first, capped. Only § → amendment: a by-law
 * chunk among the passages pulls nothing in, and one already a passage is not repeated.
 */
export function pickCompanions(passages: PassageView[], rows: CompanionRow[], sectionOf: Map<string, string>): CompanionRow[] {
  const given = new Set(passages.map((p) => p.chunkId));
  const order = [...new Set(passages.map((p) => sectionOf.get(p.chunkId)).filter((s): s is string => !!s))];
  const picked: CompanionRow[] = [];
  for (const section of order) {
    const forSection = rows
      .filter((r) => r.target_section === section && !given.has(r.id))
      .sort((a, b) => {
        const [ya, na] = bylawOrder(a.document_id);
        const [yb, nb] = bylawOrder(b.document_id);
        return yb - ya || nb - na || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
      });
    for (const r of forSection) {
      if (picked.length === MAX_COMPANIONS) return picked;
      given.add(r.id);
      picked.push(r);
    }
  }
  return picked;
}

/** Pins keep their place at the top; the rest by rerank score, ties in fused order. */
function byRerank(rows: SearchRow[], scores: number[]): SearchRow[] {
  return rows
    .map((row, i) => ({ row, score: scores[i], i }))
    .sort((a, b) => Number(b.row.pinned) - Number(a.row.pinned) || b.score - a.score || a.i - b.i)
    .map((x) => x.row);
}

/**
 * The one orchestration path: embed → search → rerank → companions → gate → generate → validate.
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
  const top = ranked.slice(0, CONTEXT_PASSAGES);
  const passages = top.map((r, i) => toPassage(r, i + 1));
  // Amended Code §§ among the passages, by chunk: what their companions target.
  const amended = new Map(
    top.filter((r) => r.kind === "chapter" && r.section && r.amended_since?.length).map((r) => [r.id, r.section!]),
  );
  if (config.companions && amended.size) {
    const found = await deps.companions([...new Set(amended.values())]);
    const first = passages.length + 1; // numbered after the retrieved passages
    passages.push(...pickCompanions(passages, found, amended).map((r, i) => toPassage(r, first + i, true)));
  }
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
      response: {
        kind: "refusal",
        reason: "below_threshold",
        scope: snapshot.scope_sentence,
        nearest: passages.filter((p) => !p.companion).slice(0, NEAREST),
      },
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
