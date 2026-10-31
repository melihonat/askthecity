import { describe, expect, it } from "vitest";
import { CONFIG_VERSION, cacheKey, isExample } from "./cache";
import { EXAMPLES } from "./scope";

describe("cacheKey", () => {
  const base = cacheKey("How late can my neighbour run a leaf blower?", "s1");

  it("is the same for questions that differ only in case and spacing", () => {
    expect(cacheKey("  how LATE can my neighbour\n run a leaf blower? ", "s1")).toBe(base);
  });

  it("changes with the question", () => {
    expect(cacheKey("How late can my neighbour run a lawn mower?", "s1")).not.toBe(base);
  });

  it("changes with the snapshot id", () => {
    expect(cacheKey("How late can my neighbour run a leaf blower?", "s2")).not.toBe(base);
  });

  it.each([
    ["the generation model", { rung: { ...CONFIG_VERSION.rung, model: "anthropic/claude-sonnet-5" } }],
    ["the embedder", { embedder: "voyage/voyage-4" }],
    ["the reranker", { reranker: "voyage/rerank-3-lite" }],
    ["the prompt version", { promptVersion: "default-99" }],
    ["the prompt hash", { promptHash: "0".repeat(16) }],
    ["the refusal threshold", { threshold: CONFIG_VERSION.threshold + 0.01 }],
  ])("changes with %s", (_, change) => {
    expect(cacheKey("How late can my neighbour run a leaf blower?", "s1", { ...CONFIG_VERSION, ...change })).not.toBe(base);
  });
});

describe("isExample", () => {
  it("knows every chip, however it is typed", () => {
    for (const ex of EXAMPLES) expect(isExample(` ${ex.question.toUpperCase()} `)).toBe(true);
  });

  it("is false for any other question", () => {
    expect(isExample("How late can my neighbour run a lawn mower?")).toBe(false);
  });
});
