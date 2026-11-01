import { describe, expect, it, vi } from "vitest";
import { type AskDeps, ask, toPassage } from "./ask";
import { MAX_OUTPUT_TOKENS, REFUSAL_THRESHOLD, RUNGS } from "./config";
import { GLOBAL_DAILY, IP_DAILY } from "./guardrails";
import { cacheKey } from "./cache";
import { PROMPTS } from "./prompt";
import type { AskEvent, AskResponse, CompanionRow, DefinitionRow, ModelOutput, Rung, SearchRow } from "./types";

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

const amendedRow = (id: string, rank: number, bylaws: string[]): SearchRow => ({ ...row(id, rank), amended_since: bylaws });

const companion = (id: string, target: string): CompanionRow => ({
  target_section: target,
  id,
  document_id: id.split(":").slice(0, 2).join(":"),
  family: "rules",
  kind: "amending_bylaw",
  section: null,
  label: id,
  sublabel: `amends § ${target} · in force 2026-03-02`,
  href: "https://example.test/law.pdf",
  amended_since: [],
  body: `body of ${id}`,
});

const definition = (id: string, term: string, uses: number, document_id = "tmc:591"): DefinitionRow => ({
  term,
  uses,
  id,
  document_id,
  family: "rules",
  kind: "chapter",
  section: id.split(":")[1],
  label: `Ch 591 § ${id.split(":")[1]}`,
  sublabel: "consolidated 2024-11-14",
  href: "https://example.test/591.pdf#page=5",
  amended_since: [],
  body: `${term} - what ${term.toLowerCase()} means.`,
});

function fakeDeps(rows: SearchRow[], scores: number[], output: ModelOutput, companions: CompanionRow[] = [], definitions: DefinitionRow[] = []) {
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
    companions: vi.fn(async (sections: string[]) => companions.filter((c) => sections.includes(c.target_section))),
    definitions: vi.fn(async (documents: string[]) => definitions.filter((d) => documents.includes(d.document_id))),
    rerank: vi.fn(async () => scores),
    generate: vi.fn(async (_req: Parameters<AskDeps["generate"]>[0]) => output),
    useQuota: vi.fn(async (_ipHash: string, _ipLimit: number) => ({ ip: 0, global: 0 })),
    cached: vi.fn(async (_key: string): Promise<AskResponse | null> => null),
    store: vi.fn(async (_key: string, _response: AskResponse) => {}),
  } satisfies AskDeps;
}

async function run(deps: AskDeps, rung: Rung = "shipped") {
  const events: AskEvent[] = [];
  for await (const ev of ask("question?", rung, deps, { debug: true })) events.push(ev);
  const final = events.find((e) => e.type === "final")!.response;
  const debug = events.find((e) => e.type === "debug")?.debug;
  const passages = events.find((e) => e.type === "passages")!.passages;
  return { events, final, debug, passages };
}

const ANSWER: ModelOutput = { decision: "answer", text: "Until 7 p.m. [1].", cited: [1] };

describe("toPassage", () => {
  const item = (sublabel: string): SearchRow => ({
    ...row("ie:2026.IE29.6:council", 1),
    document_id: "ie:2026.IE29.6",
    family: "decisions",
    kind: "item_page",
    section: null,
    sublabel,
  });

  it("marks a Decisions chunk adopted or no decision from its status stamp, and a rule neither", () => {
    expect(toPassage(item("2026-05-21 · Adopted by City Council 2026-05-21 · By-law 470-2026"), 1).decided).toBe(true);
    expect(toPassage(item("2025-12-04 · Referred by IE Committee 2025-12-04; no decision"), 1).decided).toBe(false);
    expect(toPassage(item("2025-12-04 · Deferred by IE Committee 2025-12-04 · By-law 470-2026; no decision"), 1).decided).toBe(false);
    expect(toPassage(ROWS[0], 1).decided).toBeNull();
  });
});

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
    const deps = fakeDeps(ROWS, ROWS.map(() => LOW), ANSWER);
    const { final, debug, passages } = await run(deps, "hybrid");
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

  it("sends passages, then debug, then the final response", async () => {
    const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
    const { events } = await run(deps);
    expect(events.map((e) => e.type)).toEqual(["passages", "debug", "final"]);
  });

  it("sends no debug event unless asked", async () => {
    const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
    const events: AskEvent[] = [];
    for await (const ev of ask("question?", "shipped", deps)) events.push(ev);
    expect(events.map((e) => e.type)).toEqual(["passages", "final"]);
  });

  describe("companion passages", () => {
    // fused order = rerank order here: equal scores keep the fused order
    const scores = (n: number) => Array.from({ length: n }, () => HIGH);

    it("adds the amending chunks of amended §§ after the retrieved passages, numbered from 6", async () => {
      const rows = [row("tmc:591-a", 1), amendedRow("tmc:608-19", 2, ["1482-2025"]), ...ROWS.slice(2)];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, [companion("bl:1482-2025:cl1:O-Y", "608-19")]);
      const { passages } = await run(deps);
      expect(deps.companions).toHaveBeenCalledWith(["591-a", "608-19", "591-c", "591-d", "591-e"]);
      expect(passages.map((p) => [p.n, p.chunkId, p.companion])).toEqual([
        [1, "tmc:591-a", false],
        [2, "tmc:608-19", false],
        [3, "tmc:591-c", false],
        [4, "tmc:591-d", false],
        [5, "tmc:591-e", false],
        [6, "bl:1482-2025:cl1:O-Y", true],
      ]);
      expect(passages[1].amendedSince).toEqual(["1482-2025"]);
    });

    it("caps companions at 3, in passage order, newest by-law first", async () => {
      const rows = [amendedRow("tmc:608-1", 1, ["402-2026", "1482-2025"]), amendedRow("tmc:608-19", 2, ["1482-2025"]), ...ROWS.slice(2)];
      const found = [
        companion("bl:1482-2025:cl1:A-E", "608-1"),
        companion("bl:1482-2025:cl1:F-N", "608-1"),
        companion("bl:402-2026:cl3", "608-1"),
        companion("bl:1482-2025:cl1:O-Y", "608-19"),
      ];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, found);
      const { passages } = await run(deps);
      expect(passages.filter((p) => p.companion).map((p) => [p.n, p.chunkId])).toEqual([
        [6, "bl:402-2026:cl3"],
        [7, "bl:1482-2025:cl1:A-E"],
        [8, "bl:1482-2025:cl1:F-N"],
      ]);
    });

    it("goes § → amendment only: a by-law chunk that ranks on its own pulls nothing in", async () => {
      const bylawRow: SearchRow = { ...companion("bl:1482-2025:cl1:O-Y", "608-19"), rank: 1, score: 1 / 61, pinned: false };
      const rows = [bylawRow, ...ROWS.slice(1)];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, [companion("bl:1482-2025:cl1:O-Y", "608-19")]);
      const { passages } = await run(deps);
      expect(deps.companions).not.toHaveBeenCalledWith(expect.arrayContaining(["608-19"]));
      expect(passages).toHaveLength(5);
    });

    it("adds a replacement's not-yet-law § for a § it replaces, though that § is not amended", async () => {
      const replacement: CompanionRow = {
        ...companion("bl:1512-2025:629-4.25", "629-38"),
        kind: "replacement_bylaw",
        section: "629-4.25",
        label: "Ch 629 § 629-4.25",
        sublabel: "By-law 1512-2025 · in force 2027-05-01, not yet law",
      };
      const rows = [row("tmc:629-38", 1), ...ROWS.slice(1)];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, [replacement]);
      const { passages } = await run(deps);
      expect(passages[0]).toMatchObject({ chunkId: "tmc:629-38", notYetLaw: false, amendedSince: [] });
      expect(passages[5]).toMatchObject({ n: 6, chunkId: "bl:1512-2025:629-4.25", companion: true, notYetLaw: true });
      expect(deps.generate.mock.calls[0][0].prompt).toContain(
        '<passage n="6" label="Ch 629 § 629-4.25" source="By-law 1512-2025 · in force 2027-05-01, not yet law" ' +
          'replacement="replaces a section among these passages" not_yet_law=',
      );
    });

    it("treats an in-force replacement's tmc: § as the Code, not as not yet law", async () => {
      const inForce: SearchRow = { ...row("tmc:497-2.2", 1), document_id: "bl:1511-2025", kind: "replacement_bylaw" };
      const deps = fakeDeps([inForce, ...ROWS.slice(1)], scores(ROWS.length), ANSWER);
      const { passages } = await run(deps);
      expect(passages[0].notYetLaw).toBe(false);
      expect(deps.companions).toHaveBeenCalledWith(expect.arrayContaining(["497-2.2"]));
    });

    it("never repeats a chunk that is already a retrieved passage", async () => {
      const bylawRow: SearchRow = { ...companion("bl:1482-2025:cl1:O-Y", "608-19"), rank: 2, score: 1 / 62, pinned: false };
      const rows = [amendedRow("tmc:608-19", 1, ["1482-2025"]), bylawRow, ...ROWS.slice(2)];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, [
        companion("bl:1482-2025:cl1:O-Y", "608-19"),
        companion("bl:402-2026:cl3", "608-19"),
      ]);
      const { passages } = await run(deps);
      expect(passages.filter((p) => p.companion).map((p) => [p.n, p.chunkId])).toEqual([[6, "bl:402-2026:cl3"]]);
    });

    it("lets the answer cite a companion number", async () => {
      const rows = [amendedRow("tmc:608-19", 1, ["1482-2025"]), ...ROWS.slice(1)];
      const output: ModelOutput = { decision: "answer", text: "Drones need a permit [1][6].", cited: [1, 6] };
      const deps = fakeDeps(rows, scores(rows.length), output, [companion("bl:1482-2025:cl1:O-Y", "608-19")]);
      const { final } = await run(deps);
      expect(final.kind === "answer" && final.citations).toEqual([
        { n: 1, chunkId: "tmc:608-19" },
        { n: 6, chunkId: "bl:1482-2025:cl1:O-Y" },
      ]);
      expect(deps.generate.mock.calls[0][0].prompt).toContain(
        '<passage n="6" label="bl:1482-2025:cl1:O-Y" source="amends § 608-19 · in force 2026-03-02" amendment=',
      );
    });

    it("adds none when the rung turns companions off", async () => {
      const rows = [amendedRow("tmc:608-19", 1, ["1482-2025"]), ...ROWS.slice(1)];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, [companion("bl:1482-2025:cl1:O-Y", "608-19")]);
      const { passages } = await run(deps, "rerank");
      expect(deps.companions).not.toHaveBeenCalled();
      expect(passages).toHaveLength(5);
    });

    it("keeps companions out of a refusal's nearest passages", async () => {
      const rows = [amendedRow("tmc:608-19", 1, ["1482-2025"]), row("tmc:591-b", 2)];
      const deps = fakeDeps(rows, [LOW, LOW], ANSWER, [companion("bl:1482-2025:cl1:O-Y", "608-19")]);
      const { final, passages } = await run(deps);
      expect(passages.map((p) => p.n)).toEqual([1, 2, 3]);
      expect(final.kind === "refusal" && final.nearest.map((p) => p.chunkId)).toEqual(["tmc:608-19", "tmc:591-b"]);
    });
  });

  describe("definition companions", () => {
    const scores = (n: number) => Array.from({ length: n }, () => HIGH);
    const uses = (id: string, body: string, rank = 1): SearchRow => ({ ...row(id, rank), body });
    const POWER_DEVICE = definition("tmc:591-1.1:living-area", "POWER DEVICE", 1);

    it("brings the definition of a term a passage uses, cut to that term", async () => {
      const rows = [uses("tmc:591-2.6", "A. No person shall emit sound from a power device from 7 p.m."), ...ROWS.slice(1)];
      const defs = [POWER_DEVICE, definition("tmc:591-1.1:living-area", "LIVING AREA", 9)];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, [], defs);
      const { passages } = await run(deps);
      expect(deps.definitions).toHaveBeenCalledWith(["tmc:591"]);
      expect(passages[5]).toMatchObject({
        n: 6,
        chunkId: "tmc:591-1.1:living-area",
        companion: true,
        defines: ["POWER DEVICE"],
        label: "Ch 591 § 591-1.1 POWER DEVICE",
        body: "POWER DEVICE - what power device means.",
      });
      expect(passages.slice(0, 5).every((p) => p.defines.length === 0)).toBe(true);
      expect(deps.generate.mock.calls[0][0].prompt).toContain(
        '<passage n="6" label="Ch 591 § 591-1.1 POWER DEVICE" source="consolidated 2024-11-14" definition="defines POWER DEVICE for the passages above">',
      );
    });

    it("never brings a term defined in another chapter", async () => {
      const rows = [uses("tmc:591-2.6", "No sound from a power device."), ...ROWS.slice(1)];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, [], [definition("tmc:545-1:operator", "POWER DEVICE", 1, "tmc:545")]);
      const { passages } = await run(deps);
      expect(passages).toHaveLength(5);
    });

    it("takes each passage's rarest term, and lets two terms share their definitions chunk", async () => {
      const rows = [
        uses("tmc:591-2.6", "No person shall use a power device.", 1),
        uses("tmc:591-2.7", "No person shall make persistent noise.", 2),
        ...ROWS.slice(2),
      ];
      const defs = [
        definition("tmc:591-1.1:living-area", "PERSON", 40),
        POWER_DEVICE,
        definition("tmc:591-1.1:living-area", "PERSISTENT NOISE", 3),
      ];
      const { passages } = await run(fakeDeps(rows, scores(rows.length), ANSWER, [], defs));
      expect(passages.filter((p) => p.companion).map((p) => [p.n, p.chunkId, p.defines, p.body])).toEqual([
        [6, "tmc:591-1.1:living-area", ["POWER DEVICE", "PERSISTENT NOISE"],
          "POWER DEVICE - what power device means.\n\nPERSISTENT NOISE - what persistent noise means."],
      ]);
    });

    it("takes the companion slots amendments leave, after them", async () => {
      const rows = [
        amendedRow("tmc:608-19", 1, ["1482-2025"]),
        uses("tmc:591-2.6", "No power device.", 2),
        uses("tmc:591-2.7", "No persistent noise.", 3),
        ...ROWS.slice(3),
      ];
      const amending = [companion("bl:1482-2025:cl1:O-Y", "608-19"), companion("bl:402-2026:cl3", "608-19")];
      const defs = [POWER_DEVICE, definition("tmc:591-1.1:p", "PERSISTENT NOISE", 3)];
      const { passages } = await run(fakeDeps(rows, scores(rows.length), ANSWER, amending, defs));
      expect(passages.filter((p) => p.companion).map((p) => [p.n, p.chunkId])).toEqual([
        [6, "bl:402-2026:cl3"],
        [7, "bl:1482-2025:cl1:O-Y"],
        [8, "tmc:591-1.1:living-area"],
      ]);
    });

    it("skips a definitions chunk already among the passages, and one there brings no more", async () => {
      const defsRow = uses("tmc:591-1.1:living-area", "POWER DEVICE - … PERSON …", 2);
      const rows = [uses("tmc:591-2.6", "No power device.", 1), defsRow, ...ROWS.slice(2)];
      const defs = [POWER_DEVICE, definition("tmc:591-1.1:a", "PERSON", 40)];
      const { passages } = await run(fakeDeps(rows, scores(rows.length), ANSWER, [], defs));
      expect(passages).toHaveLength(5);
    });

    it("matches whole words in any case, plurals too", async () => {
      const at = async (body: string) => {
        const rows = [uses("tmc:591-2.6", body), ...ROWS.slice(1)];
        const { passages } = await run(fakeDeps(rows, scores(rows.length), ANSWER, [], [POWER_DEVICE]));
        return passages.length;
      };
      expect(await at("Power Devices may not run.")).toBe(6);
      expect(await at("A power-device-free zone.")).toBe(5);
      expect(await at("A superpower device.")).toBe(5);
    });

    it("brings none when the rung turns companions off", async () => {
      const rows = [uses("tmc:591-2.6", "No power device."), ...ROWS.slice(1)];
      const deps = fakeDeps(rows, scores(rows.length), ANSWER, [], [POWER_DEVICE]);
      const { passages } = await run(deps, "rerank");
      expect(deps.definitions).not.toHaveBeenCalled();
      expect(passages).toHaveLength(5);
    });
  });

  describe("rung presets", () => {
    const amended = [amendedRow("tmc:608-19", 1, ["1482-2025"]), ...ROWS.slice(1)];
    const found = [companion("bl:1482-2025:cl1:O-Y", "608-19")];
    // the reranker lifts the last fused candidate to the top, so a reranked rung shows in the passages
    const lifted = amended.map((_, i) => (i === amended.length - 1 ? HIGH + 0.1 : HIGH));

    it.each([
      ["dense", "vector", false, false],
      ["hybrid", "hybrid", false, false],
      ["rerank", "hybrid", true, false],
      ["shipped", "hybrid", true, true],
      ["side-sonnet", "hybrid", true, true],
      ["side-quoted", "hybrid", true, true],
    ] as const)("%s: search %s, rerank %s, companions %s", async (rung, search, rerank, companions) => {
      const deps = fakeDeps(amended, lifted, ANSWER, found);
      const { passages, debug } = await run(deps, rung);
      expect(deps.search).toHaveBeenCalledWith("question?", [0.1], search);
      expect(deps.rerank).toHaveBeenCalledTimes(rerank ? 1 : 0);
      expect(passages[0].chunkId).toBe(rerank ? "tmc:591-g" : "tmc:608-19");
      expect(passages.some((p) => p.companion)).toBe(companions);
      expect(deps.generate.mock.calls[0][0].model).toBe(RUNGS[rung].model);
      expect(debug).toMatchObject({ rung, config: RUNGS[rung] });
    });

    it("records what produced the answer in debug", async () => {
      const { debug } = await run(fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER));
      expect(debug?.build).toMatchObject({
        promptVersion: PROMPTS.default.version,
        promptHash: expect.stringMatching(/^[0-9a-f]{12}$/),
        embedder: "voyage/voyage-4-large",
        reranker: "voyage/rerank-3",
      });
      expect(debug?.quotes).toBeNull();
    });

    it("side-sonnet changes only the generator, with room for the thinking it can't turn off", () => {
      expect(RUNGS["side-sonnet"]).toEqual({ ...RUNGS.shipped, model: "anthropic/claude-sonnet-5.5", maxOutputTokens: 1600 });
    });

    it.each([
      ["shipped", MAX_OUTPUT_TOKENS],
      ["side-sonnet", 1600],
      ["side-quoted", 1200],
    ] as const)("%s generates with an output cap of %i tokens", async (rung, cap) => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      await run(deps, rung);
      expect(deps.generate.mock.calls[0][0].maxOutputTokens).toBe(cap);
    });

    it("leaves the shipped preset without a cap field, so the public cache key is unchanged", () => {
      expect(RUNGS.shipped).not.toHaveProperty("maxOutputTokens");
    });

    it("side-quoted asks for quotes and keeps them in debug, out of the response", async () => {
      const quotes = [{ n: 1, sentence: "No person shall use a leaf blower." }];
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), { ...ANSWER, quotes });
      const { final, debug } = await run(deps, "side-quoted");
      const req = deps.generate.mock.calls[0][0];
      expect(req.quotes).toBe(true);
      expect(req.system).toContain('"quotes"');
      expect(debug).toMatchObject({ quotes, build: { promptVersion: PROMPTS.quoted.version, promptHash: PROMPTS.quoted.hash } });
      expect(JSON.stringify(final)).not.toContain("quotes");
    });

    it("gives the quoted prompt its own version and hash", () => {
      expect(PROMPTS.quoted.version).not.toBe(PROMPTS.default.version);
      expect(PROMPTS.quoted.hash).not.toBe(PROMPTS.default.hash);
    });
  });

  describe("limits", () => {
    async function events(deps: AskDeps, ipHash?: string) {
      const out: AskEvent[] = [];
      for await (const ev of ask("question?", "shipped", deps, { ipHash })) out.push(ev);
      return out;
    }
    const limitOnly = (limit: string) => [{ type: "final", response: { kind: "limit", limit } }];
    const upstream = (statusCode: number) => Object.assign(new Error(`HTTP ${statusCode}`), { statusCode });

    it("meters a request by its IP hash against the per-IP limit", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      await events(deps, "hash-1");
      expect(deps.useQuota).toHaveBeenCalledWith("hash-1", IP_DAILY);
    });

    it("sends no IP hash for the eval header, so nothing is metered", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      await events(deps);
      expect(deps.useQuota).not.toHaveBeenCalled();
    });

    it.each([
      [{ ip: IP_DAILY, global: 0 }, "ip_daily"],
      [{ ip: 0, global: GLOBAL_DAILY }, "global_daily"],
    ])("stops at %o with only the final %s event, before the search", async (usage, limit) => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps.useQuota.mockResolvedValue(usage);
      expect(await events(deps, "hash-1")).toEqual(limitOnly(limit));
      expect(deps.search).not.toHaveBeenCalled();
      expect(deps.generate).not.toHaveBeenCalled();
    });

    it("maps an upstream 402 to budget, sending only the final event", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps.embed.mockRejectedValue(upstream(402));
      expect(await events(deps, "hash-1")).toEqual(limitOnly("budget"));
    });

    it("maps a 429 behind the SDK's retry wrapper to burst", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps.rerank.mockRejectedValue(Object.assign(new Error("retries exhausted"), { lastError: upstream(429) }));
      expect(await events(deps, "hash-1")).toEqual(limitOnly("burst"));
    });

    it("ends with a limit, not an error, when generation fails after the passages", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps.generate.mockRejectedValue(upstream(402));
      const out = await events(deps, "hash-1");
      expect(out.map((e) => e.type)).toEqual(["passages", "final"]);
      expect(out[1]).toEqual(limitOnly("budget")[0]);
    });

    it.each([
      ["the snapshot", "snapshot"],
      ["the quota", "useQuota"],
      ["the search", "search"],
    ] as const)("maps any other failure (%s) to unavailable", async (_, dep) => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps[dep].mockRejectedValue(new Error("connection refused"));
      expect(await events(deps, "hash-1")).toEqual(limitOnly("unavailable"));
    });
  });
  describe("answer cache", () => {
    async function events(deps: AskDeps, opts: { cache?: boolean; ipHash?: string } = {}) {
      const out: AskEvent[] = [];
      for await (const ev of ask("How late can my neighbour run a leaf blower?", "shipped", deps, opts)) out.push(ev);
      return out;
    }
    const KEY = cacheKey("How late can my neighbour run a leaf blower?", "s1");
    const STORED: AskResponse = { kind: "answer", text: "Until 7 p.m. [1].", citations: [{ n: 1, chunkId: "tmc:591-a" }], passages: [] };

    it("serves a hit as the only event, skipping embed, search, generate and the limits", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps.cached.mockResolvedValue(STORED);
      expect(await events(deps, { cache: true, ipHash: "hash-1" })).toEqual([{ type: "final", response: STORED }]);
      expect(deps.cached).toHaveBeenCalledWith(KEY);
      for (const dep of [deps.embed, deps.search, deps.rerank, deps.generate, deps.useQuota, deps.store]) expect(dep).not.toHaveBeenCalled();
    });

    it("serves a hit while a daily limit is active", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps.cached.mockResolvedValue(STORED);
      deps.useQuota.mockResolvedValue({ ip: IP_DAILY, global: GLOBAL_DAILY });
      expect(await events(deps, { cache: true, ipHash: "hash-1" })).toEqual([{ type: "final", response: STORED }]);
    });

    it("on a miss, runs the pipeline and stores the response it sends", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      const out = await events(deps, { cache: true, ipHash: "hash-1" });
      const final = out.at(-1)!;
      expect(final.type === "final" && final.response.kind).toBe("answer");
      expect(deps.useQuota).toHaveBeenCalledOnce();
      expect(deps.store).toHaveBeenCalledWith(KEY, final.type === "final" && final.response);
    });

    it("stores a gate refusal too", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => LOW), ANSWER);
      await events(deps, { cache: true });
      expect(deps.store).toHaveBeenCalledWith(KEY, expect.objectContaining({ kind: "refusal", reason: "below_threshold" }));
    });

    it("never stores a limit", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps.generate.mockRejectedValue(Object.assign(new Error("HTTP 402"), { statusCode: 402 }));
      await events(deps, { cache: true });
      deps.useQuota.mockResolvedValue({ ip: IP_DAILY, global: 0 });
      await events(deps, { cache: true, ipHash: "hash-1" });
      expect(deps.store).not.toHaveBeenCalled();
    });

    it("still sends the response when storing it fails", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      deps.store.mockRejectedValue(new Error("connection refused"));
      const final = (await events(deps, { cache: true })).at(-1)!;
      expect(final.type === "final" && final.response.kind).toBe("answer");
    });

    it("is neither read nor written without the cache option (the eval header)", async () => {
      const deps = fakeDeps(ROWS, ROWS.map(() => HIGH), ANSWER);
      await events(deps);
      expect(deps.cached).not.toHaveBeenCalled();
      expect(deps.store).not.toHaveBeenCalled();
    });
  });
});
