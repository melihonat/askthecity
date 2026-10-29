import { describe, expect, it, vi } from "vitest";
import { type AskDeps, ask } from "./ask";
import { DEFAULT_CONFIG, REFUSAL_THRESHOLD } from "./config";
import type { AskEvent, ModelOutput, RungConfig, SearchRow } from "./types";

const SCOPE = "Knows the Toronto Municipal Code…";

const row = (id: string, rank: number, pinned = false): SearchRow => ({
  id,
  document_id: "tmc:591",
  family: "rules",
  kind: "chapter",
  section: id.split(":")[1],
  label: id,
  sublabel: "consolidated 2024-11-14",
  href: "https://example.test/591.pdf",
  amended_since: [],
  body: `body of ${id}`,
  rank,
  score: 1 / (60 + rank),
  pinned,
});

const ROWS = ["a", "b", "c", "d", "e", "f", "g"].map((s, i) => row(`tmc:591-${s}`, i + 1));
const LOW = REFUSAL_THRESHOLD / 2;
const HIGH = Math.min(1, REFUSAL_THRESHOLD * 2);

function fakeDeps(rows: SearchRow[], scores: number[], output: ModelOutput) {
  return {
    snapshot: vi.fn(async () => ({
      id: "s1",
      snapshot_date: "2026-10-20",
      embed_model: "voyage-4-large",
      embed_dim: 1024,
      scope_sentence: SCOPE,
    })),
    embed: vi.fn(async () => [0.1]),
    search: vi.fn(async () => rows),
    rerank: vi.fn(async () => scores),
    generate: vi.fn(async () => output),
  } satisfies AskDeps;
}

async function run(deps: AskDeps, config: RungConfig = DEFAULT_CONFIG) {
  const events: AskEvent[] = [];
  for await (const ev of ask("question?", config, deps, { debug: true })) events.push(ev);
  const final = events.find((e) => e.type === "final")!.response;
  const debug = events.find((e) => e.type === "debug")?.debug;
  const passages = events.find((e) => e.type === "passages")!.passages;
  return { events, final, debug, passages };
}

const ANSWER: ModelOutput = { decision: "answer", text: "Until 7 p.m. [1].", cited: [1] };

describe("ask", () => {
  it("reranks the candidates to 5 passages, best score first", async () => {
    const deps = fakeDeps(ROWS, [0.91, 0.92, 0.96, 0.93, 0.99, 0.9, 0.93], ANSWER);
    const { passages, final } = await run(deps);
    expect(passages.map((p) => [p.n, p.chunkId])).toEqual([
      [1, "tmc:591-e"],
      [2, "tmc:591-c"],
      [3, "tmc:591-d"], // tie with g: fused order wins
      [4, "tmc:591-g"],
      [5, "tmc:591-b"],
    ]);
    expect(final.kind).toBe("answer");
  });

  it("refuses below the threshold without calling the model", async () => {
    const deps = fakeDeps(ROWS, ROWS.map(() => LOW), ANSWER);
    const { final, debug, events } = await run(deps);
    expect(deps.generate).not.toHaveBeenCalled();
    expect(final).toEqual({ kind: "refusal", reason: "below_threshold", scope: SCOPE, nearest: expect.any(Array) });
    expect(final.kind === "refusal" && final.nearest).toHaveLength(3);
    expect(debug).toMatchObject({ gateScore: LOW, gateBypassed: false, declineText: null, timings: { generation_ms: null } });
    expect(events.map((e) => e.type)).toEqual(["passages", "debug", "final"]);
  });

  it("lets a pinned section through the gate and keeps it first", async () => {
    const rows = [row("tmc:591-2.1", 1, true), ...ROWS.slice(1)];
    const scores = rows.map(() => LOW);
    scores[3] = LOW * 1.5;
    const deps = fakeDeps(rows, scores, ANSWER);
    const { final, debug, passages } = await run(deps);
    expect(deps.generate).toHaveBeenCalledOnce();
    expect(passages[0].chunkId).toBe("tmc:591-2.1");
    expect(final.kind).toBe("answer");
    expect(debug).toMatchObject({ pinned: ["tmc:591-2.1"], gateBypassed: true });
  });

  it("with rerank off, takes the top 5 by fused rank and never gates", async () => {
    const deps = fakeDeps(ROWS, [], ANSWER);
    const { final, debug, passages } = await run(deps, { ...DEFAULT_CONFIG, rerank: false });
    expect(deps.rerank).not.toHaveBeenCalled();
    expect(deps.generate).toHaveBeenCalledOnce();
    expect(passages.map((p) => p.chunkId)).toEqual(ROWS.slice(0, 5).map((r) => r.id));
    expect(final.kind).toBe("answer");
    expect(debug?.gateScore).toBeNull();
  });

  it("maps a decline to model_declined and keeps the model's text out of the response", async () => {
    const decline: ModelOutput = { decision: "decline", text: "That is set by the TTC board.", cited: [] };
    const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), decline);
    const { final, debug } = await run(deps);
    expect(final).toMatchObject({ kind: "refusal", reason: "model_declined", scope: SCOPE });
    expect(JSON.stringify(final)).not.toContain("TTC board");
    expect(debug?.declineText).toBe("That is set by the TTC board.");
  });

  it("sends no debug event unless asked", async () => {
    const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
    const events: AskEvent[] = [];
    for await (const ev of ask("question?", DEFAULT_CONFIG, deps)) events.push(ev);
    expect(events.map((e) => e.type)).toEqual(["passages", "final"]);
  });
});
