import { describe, expect, it } from "vitest";
import { CorpusMismatchError, checkCorpus } from "./config";

describe("checkCorpus", () => {
  it("accepts the corpus the queries are embedded for", () => {
    expect(() => checkCorpus({ embed_model: "voyage-4-large", embed_dim: 1024 })).not.toThrow();
  });

  it("fails on a different model or dimension", () => {
    expect(() => checkCorpus({ embed_model: "voyage-4", embed_dim: 1024 })).toThrow(CorpusMismatchError);
    expect(() => checkCorpus({ embed_model: "voyage-4-large", embed_dim: 2048 })).toThrow(CorpusMismatchError);
  });
});
