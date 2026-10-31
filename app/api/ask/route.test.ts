import { beforeEach, describe, expect, it, vi } from "vitest";
import type { AskDeps } from "@/lib/ask/ask";
import { EVAL_HEADER, EVAL_RUN_HEADER } from "@/lib/ask/eval";
import type { AskEvent, SearchRow } from "@/lib/ask/types";

const row = (id: string, rank: number): SearchRow => ({
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
  pinned: false,
});

const fake = {
  tags: [] as string[],
  deps: {
    snapshot: async () => ({ id: "s1", snapshot_date: "2026-10-20", embed_model: "voyage-4-large", embed_dim: 1024, scope_sentence: "…" }),
    embed: async () => [0.1],
    search: vi.fn(async () => [row("tmc:591-a", 1), row("tmc:591-b", 2)]),
    companions: async () => [],
    rerank: async () => [0.9, 0.8],
    generate: async () => ({ decision: "answer" as const, text: "Until 7 p.m. [1].", cited: [1] }),
  } satisfies AskDeps,
};

vi.mock("@/lib/ask/deps", () => ({
  createDeps: (tags: string[]) => {
    fake.tags = tags;
    return fake.deps;
  },
}));

const { POST } = await import("./route");

const SECRET = "s3cret-value";

async function post(body: object, headers: Record<string, string> = {}) {
  const res = await POST(new Request("http://test/api/ask", { method: "POST", body: JSON.stringify(body), headers }));
  const text = await res.text();
  return { status: res.status, events: text.trim().split("\n").map((l) => JSON.parse(l) as AskEvent) };
}

describe("POST /api/ask", () => {
  beforeEach(() => {
    vi.stubEnv("EVAL_HEADER_SECRET", SECRET);
    fake.deps.search.mockClear();
  });

  it("sends no debug event and ignores a rung without the eval header", async () => {
    const { events } = await post({ question: "When can they drill?", rung: "dense" });
    expect(events.map((e) => e.type)).toEqual(["passages", "final"]);
    expect(fake.deps.search).toHaveBeenCalledWith("When can they drill?", [0.1], "hybrid");
    expect(fake.tags).toEqual([]);
  });

  it("with the eval header, runs the named rung, tags the run and sends debug between passages and final", async () => {
    const { events } = await post({ question: "When can they drill?", rung: "dense" }, { [EVAL_HEADER]: SECRET, [EVAL_RUN_HEADER]: "r1" });
    expect(events.map((e) => e.type)).toEqual(["passages", "debug", "final"]);
    expect(events[1].type === "debug" && events[1].debug.rung).toBe("dense");
    expect(fake.deps.search).toHaveBeenCalledWith("When can they drill?", [0.1], "vector");
    expect(fake.tags).toEqual(["eval:r1"]);
  });

  it("streams the passages before generation finishes", async () => {
    let release!: () => void;
    const held = new Promise<void>((r) => (release = r));
    const generate = fake.deps.generate;
    fake.deps.generate = async () => {
      await held;
      return generate();
    };
    try {
      const res = await POST(new Request("http://test/api/ask", { method: "POST", body: JSON.stringify({ question: "q?" }) }));
      const reader = res.body!.pipeThrough(new TextDecoderStream()).getReader();
      const first = JSON.parse((await reader.read()).value!) as AskEvent;
      expect(first.type).toBe("passages");
      release();
      let rest = "";
      for (let r = await reader.read(); !r.done; r = await reader.read()) rest += r.value;
      expect((JSON.parse(rest) as AskEvent).type).toBe("final");
    } finally {
      fake.deps.generate = generate;
    }
  });

  it("rejects an unknown rung under the eval header", async () => {
    const res = await POST(
      new Request("http://test/api/ask", { method: "POST", body: JSON.stringify({ question: "q?", rung: "best" }), headers: { [EVAL_HEADER]: SECRET } }),
    );
    expect(res.status).toBe(400);
  });
});
