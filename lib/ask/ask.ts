import { cacheKey } from "./cache";
import { CONTEXT_PASSAGES, EMBEDDING, MAX_COMPANIONS, REFUSAL_THRESHOLD, RERANK_MODEL, RUNGS } from "./config";
import { failureLimit, IP_DAILY, usageLimit } from "./guardrails";
import { PROMPTS, systemPrompt, userPrompt } from "./prompt";
import type {
  AskEvent,
  AskResponse,
  ChunkRow,
  CompanionRow,
  DebugEvent,
  DefinitionRow,
  ModelOutput,
  PassageView,
  Rung,
  RungConfig,
  SearchRow,
  Snapshot,
  Usage,
} from "./types";
import { NEAREST, validate } from "./validate";

export type AskDeps = {
  snapshot(): Promise<Snapshot>;
  embed(question: string): Promise<number[]>;
  search(question: string, embedding: number[], mode: RungConfig["search"]): Promise<SearchRow[]>;
  /** The amending chunks that target any of these §§ (the amendments table). */
  companions(sections: string[]): Promise<CompanionRow[]>;
  /** Every defined term of these documents, each with its definitions chunk cut to it. */
  definitions(documents: string[]): Promise<DefinitionRow[]>;
  /** One relevance score per document, in input order. */
  rerank(question: string, documents: string[]): Promise<number[]>;
  /** `quotes` asks the structured output for a supporting sentence per citation too. */
  generate(req: { model: string; system: string; prompt: string; quotes: boolean }): Promise<ModelOutput>;
  /**
   * Counts one paid question against the IP's day and, while the IP is under `ipLimit`, the
   * global day. Returns the counts from before it.
   */
  useQuota(ipHash: string, ipLimit: number): Promise<Usage>;
  /** The stored response for a cache key, or null. */
  cached(key: string): Promise<AskResponse | null>;
  /** Stores a response; a key already stored keeps its response. */
  store(key: string, response: AskResponse): Promise<void>;
};

/**
 * `ipHash` meters the request against the daily limits; the eval header and example questions
 * send none. `cache` reads and fills the answer cache; the eval header skips it.
 */
export type AskOptions = { debug?: boolean; ipHash?: string; cache?: boolean };

export function toPassage(row: ChunkRow, n: number, companion = false, defines: string[] = []): PassageView {
  return {
    n,
    chunkId: row.id,
    companion,
    family: row.family,
    label: row.label,
    sublabel: row.sublabel,
    href: row.href,
    amendedSince: row.amended_since ?? [],
    // a replacement in force takes `tmc:` ids and is the Code; one not yet in force keeps `bl:` ids
    notYetLaw: row.kind === "replacement_bylaw" && !row.id.startsWith("tmc:"),
    // a Decisions sublabel ends with the item's status stamp, which ends "; no decision" when undecided
    decided: row.family === "decisions" ? !row.sublabel.endsWith("; no decision") : null,
    defines,
    body: row.body,
  };
}

/** By-law 1482-2025 → [2025, 1482], for newest-first ordering. */
function bylawOrder(documentId: string): [number, number] {
  const [num, year] = documentId.replace(/^bl:/, "").split("-").map(Number);
  return [year || 0, num || 0];
}

/**
 * Companion passages (CONTRACT.md, "Citation"): for the passages' Code §§, the chunks that target
 * them (amending clauses, and the §§ of a replacement not yet in force), in passage order, newest
 * by-law first, capped. Only § → amendment: a by-law chunk among the passages pulls nothing in,
 * and one already a passage is not repeated.
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

/** A defined term used in a body: whole words, any case, a plural allowed (ingest/chunk.py too). */
function termPattern(term: string): RegExp {
  return new RegExp(`(?<![\\w-])${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?:e?s)?(?![\\w-])`, "i");
}

/**
 * Definition companions (CONTRACT.md, "Citation"): for each retrieved Code § in order, the
 * rarest term its body uses that its own chapter defines, as that term's definitions chunk cut
 * to the term. Two terms from one definitions chunk share a passage. At most `room` chunks; a
 * chunk already given is skipped, and a definitions run among the passages brings no more.
 */
export function pickDefinitions(passages: ChunkRow[], rows: DefinitionRow[], given: Set<string>, room: number): { row: ChunkRow; terms: string[] }[] {
  const defining = new Set(rows.map((r) => r.id));
  const picked = new Map<string, { row: ChunkRow; terms: string[] }>();
  for (const p of passages) {
    if (defining.has(p.id)) continue;
    const best = rows
      .filter((r) => r.document_id === p.document_id && !given.has(r.id) && termPattern(r.term).test(p.body))
      .sort((a, b) => a.uses - b.uses || (a.term < b.term ? -1 : a.term > b.term ? 1 : 0))[0];
    if (!best) continue;
    const same = picked.get(best.id);
    if (same && !same.terms.includes(best.term)) {
      same.terms.push(best.term);
      same.row = { ...same.row, body: `${same.row.body}\n\n${best.body}` };
    } else if (!same && picked.size < room) {
      picked.set(best.id, { row: best, terms: [best.term] });
    }
  }
  return [...picked.values()].map(({ row, terms }) => ({ row: { ...row, label: `${row.label} ${terms.join(", ")}` }, terms }));
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
 * The rung's preset switches steps inside it. With rerank off the top 5 are by fused rank and
 * the gate is off; a pin skips the gate. A daily limit stops it before the search and is the only
 * event. Any failure becomes a typed limit (upstream 402 → `budget`, 429 → `burst`), never a 500.
 * A cache hit comes first, before any limit or paid call, and is the only event.
 */
export async function* ask(question: string, rung: Rung, deps: AskDeps, opts: AskOptions = {}): AsyncGenerator<AskEvent> {
  try {
    yield* run(question, rung, deps, opts);
  } catch (e) {
    console.error(e);
    yield { type: "final", response: { kind: "limit", limit: failureLimit(e) } };
  }
}

async function* run(question: string, rung: Rung, deps: AskDeps, opts: AskOptions): AsyncGenerator<AskEvent> {
  const config = RUNGS[rung];
  const t0 = performance.now();
  const snapshot = await deps.snapshot();
  const key = opts.cache ? cacheKey(question, snapshot.id) : null;
  const hit = key && (await deps.cached(key));
  if (hit) {
    yield { type: "final", response: hit };
    return;
  }
  // The quota round trip runs beside the embedding, so it adds no latency.
  const [usage, embedding] = await Promise.all([
    opts.ipHash ? deps.useQuota(opts.ipHash, IP_DAILY) : null,
    deps.embed(question),
  ]);
  const limit = usage && usageLimit(usage);
  if (limit) {
    yield { type: "final", response: { kind: "limit", limit } };
    return;
  }
  const rows = await deps.search(question, embedding, config.search);
  const t1 = performance.now();

  const scores = config.rerank && rows.length ? await deps.rerank(question, rows.map((r) => `${r.label}\n${r.body}`)) : null;
  const t2 = performance.now();

  const ranked = scores ? byRerank(rows, scores) : rows;
  const top = ranked.slice(0, CONTEXT_PASSAGES);
  const passages = top.map((r, i) => toPassage(r, i + 1));
  // Code §§ among the passages, by chunk: what companions target. Not only amended ones: a § whose
  // chapter has a replacement not yet in force carries no `amended_since`, but has companions.
  const codeSections = new Map(top.filter((r) => r.id.startsWith("tmc:") && r.section).map((r) => [r.id, r.section!]));
  // Chapter §§ among the passages (a pending replacement's too): what definitions serve.
  const sectionRows = top.filter((r) => r.family === "rules" && r.section);
  if (config.companions && sectionRows.length) {
    const [found, defined] = await Promise.all([
      codeSections.size ? deps.companions([...new Set(codeSections.values())]) : [],
      deps.definitions([...new Set(sectionRows.map((r) => r.document_id))]),
    ]);
    // Amendments first: they change the law. Definitions take the slots left.
    const amendments = pickCompanions(passages, found, codeSections);
    const given = new Set([...top, ...amendments].map((r) => r.id));
    const definitions = pickDefinitions(sectionRows, defined, given, MAX_COMPANIONS - amendments.length);
    const first = passages.length + 1; // numbered after the retrieved passages
    passages.push(
      ...amendments.map((r, i) => toPassage(r, first + i, true)),
      ...definitions.map((d, i) => toPassage(d.row, first + amendments.length + i, true, d.terms)),
    );
  }
  yield { type: "passages", passages };

  const pinned = rows.filter((r) => r.pinned).map((r) => r.id);
  const gateScore = config.rerank ? Math.max(0, ...(scores ?? [])) : null;
  const gateBypassed = pinned.length > 0;
  const debug = (output: ModelOutput | null, generation_ms: number | null): DebugEvent => ({
    candidates: rows.map((r, i) => ({ chunkId: r.id, rrfRank: r.rank, rerankScore: scores?.[i] ?? null })),
    pinned,
    gateScore,
    threshold: REFUSAL_THRESHOLD,
    gateBypassed,
    declineText: output?.decision === "decline" ? output.text : null,
    quotes: output?.quotes ?? null,
    timings: {
      retrieval_ms: Math.round(t1 - t0),
      rerank_ms: Math.round(t2 - t1),
      generation_ms,
      total_ms: Math.round(performance.now() - t0),
    },
    rung,
    config,
    build: {
      sha: process.env.VERCEL_GIT_COMMIT_SHA ?? null,
      promptVersion: PROMPTS[config.prompt].version,
      promptHash: PROMPTS[config.prompt].hash,
      embedder: EMBEDDING.gatewayModel,
      reranker: RERANK_MODEL,
    },
  });

  if (gateScore !== null && !gateBypassed && gateScore < REFUSAL_THRESHOLD) {
    if (opts.debug) yield { type: "debug", debug: debug(null, null) };
    const response: AskResponse = {
      kind: "refusal",
      reason: "below_threshold",
      scope: snapshot.scope_sentence,
      nearest: passages.filter((p) => !p.companion).slice(0, NEAREST),
    };
    if (key) await store(deps, key, response);
    yield { type: "final", response };
    return;
  }

  const t3 = performance.now();
  const output = await deps.generate({
    model: config.model,
    system: systemPrompt(snapshot.snapshot_date, config.prompt),
    prompt: userPrompt(question, passages),
    quotes: config.prompt === "quoted",
  });
  const generation_ms = Math.round(performance.now() - t3);
  const response = validate(output, passages, snapshot.scope_sentence);

  if (opts.debug) yield { type: "debug", debug: debug(output, generation_ms) };
  if (key) await store(deps, key, response);
  yield { type: "final", response };
}

/** A failed write costs only a future hit; the response is still good, so it is still sent. */
async function store(deps: AskDeps, key: string, response: AskResponse): Promise<void> {
  try {
    await deps.store(key, response);
  } catch (e) {
    console.error(e);
  }
}
