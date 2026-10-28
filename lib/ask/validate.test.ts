import { describe, expect, it } from "vitest";
import type { ModelOutput, PassageView } from "./types";
import { validate } from "./validate";

const passage = (n: number): PassageView => ({
  n,
  chunkId: `tmc:591-2.${n}`,
  companion: false,
  family: "rules",
  label: `Ch 591 § 591-2.${n}`,
  sublabel: "consolidated 2024-11-14",
  href: `https://example.test/591.pdf#page=${n}`,
  amendedSince: [],
  body: "…",
});
const PASSAGES = [1, 2, 3, 4, 5].map(passage);
const SCOPE = "Knows the Toronto Municipal Code…";

const answer = (text: string, cited: number[]): ModelOutput => ({ decision: "answer", text, cited });

describe("validate", () => {
  it("resolves valid markers to their chunks, in marker order", () => {
    const r = validate(answer("Power devices stop at 7 p.m. [3]. Animals too [1].", [3, 1]), PASSAGES, SCOPE);
    expect(r).toEqual({
      kind: "answer",
      text: "Power devices stop at 7 p.m. [3]. Animals too [1].",
      citations: [
        { n: 3, chunkId: "tmc:591-2.3" },
        { n: 1, chunkId: "tmc:591-2.1" },
      ],
      passages: PASSAGES,
    });
  });

  it("strips out-of-range markers and keeps the rest", () => {
    const r = validate(answer("Until 8 a.m. [2][7]. Not on Sundays [0].", [2, 7, 0]), PASSAGES, SCOPE);
    expect(r.kind === "answer" && r.text).toBe("Until 8 a.m. [2]. Not on Sundays.");
    expect(r.kind === "answer" && r.citations).toEqual([{ n: 2, chunkId: "tmc:591-2.2" }]);
  });

  it("drops numbers listed in cited that never appear in the text", () => {
    const r = validate(answer("Until 7 p.m. [2].", [2, 4]), PASSAGES, SCOPE);
    expect(r.kind === "answer" && r.citations.map((c) => c.n)).toEqual([2]);
  });

  it("keeps an in-range marker in the text even when cited omits it", () => {
    const r = validate(answer("Until 7 p.m. [2]. Except parks [4].", [2]), PASSAGES, SCOPE);
    expect(r.kind === "answer" && r.citations.map((c) => c.n)).toEqual([2, 4]);
  });

  it("splits grouped markers and strips the invalid members", () => {
    const r = validate(answer("Weekdays and weekends differ [1, 9, 5].", [1, 5]), PASSAGES, SCOPE);
    expect(r.kind === "answer" && r.text).toBe("Weekdays and weekends differ [1][5].");
  });

  it("refuses with no_valid_citation when every marker is invalid", () => {
    const r = validate(answer("Leaf blowers are banned [8]. Always [0].", [8, 0]), PASSAGES, SCOPE);
    expect(r).toEqual({ kind: "refusal", reason: "no_valid_citation", scope: SCOPE, nearest: PASSAGES.slice(0, 3) });
  });

  it("refuses with no_valid_citation when the text has no markers at all", () => {
    const r = validate(answer("Leaf blowers stop at 7 p.m.", [1]), PASSAGES, SCOPE);
    expect(r.kind === "refusal" && r.reason).toBe("no_valid_citation");
  });

  it("keeps uncited sentences, including a gap sentence", () => {
    const text = "No. Power devices stop at 7 p.m. [3]. The documents don't set fines for this.";
    const r = validate(answer(text, [3]), PASSAGES, SCOPE);
    expect(r.kind === "answer" && r.text).toBe(text);
  });

  it("refuses with model_declined on a decline and drops the model's text", () => {
    const r = validate({ decision: "decline", text: "Try the province [1].", cited: [1] }, PASSAGES, SCOPE);
    expect(r).toEqual({ kind: "refusal", reason: "model_declined", scope: SCOPE, nearest: PASSAGES.slice(0, 3) });
  });
});
