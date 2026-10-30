import { describe, expect, it } from "vitest";
import { EVAL_HEADER, EVAL_RUN_HEADER, isEvalRequest, resolveEval } from "./eval";

const SECRET = "s3cret-value";
const headers = (h: Record<string, string> = {}) => new Headers(h);

describe("isEvalRequest", () => {
  it("accepts only the exact secret", () => {
    expect(isEvalRequest(SECRET, SECRET)).toBe(true);
    expect(isEvalRequest("s3cret-valu", SECRET)).toBe(false);
    expect(isEvalRequest(null, SECRET)).toBe(false);
  });

  it("grants nothing when no secret is configured", () => {
    expect(isEvalRequest("", "")).toBe(false);
    expect(isEvalRequest("anything", undefined)).toBe(false);
  });
});

describe("resolveEval", () => {
  it("ignores a rung without the eval header and runs shipped", () => {
    expect(resolveEval(headers(), { rung: "dense" }, SECRET)).toEqual({ eval: false, rung: "shipped", tags: [] });
    expect(resolveEval(headers({ [EVAL_HEADER]: "wrong" }), { rung: "not-a-rung" }, SECRET)).toMatchObject({ rung: "shipped" });
  });

  it("selects the rung and tags the run under the eval header", () => {
    const h = headers({ [EVAL_HEADER]: SECRET, [EVAL_RUN_HEADER]: "2026-10-30-dense-dev-1405" });
    expect(resolveEval(h, { rung: "dense" }, SECRET)).toEqual({ eval: true, rung: "dense", tags: ["eval:2026-10-30-dense-dev-1405"] });
  });

  it("defaults to shipped under the eval header, and rejects an unknown rung", () => {
    const h = headers({ [EVAL_HEADER]: SECRET });
    expect(resolveEval(h, {}, SECRET)).toEqual({ eval: true, rung: "shipped", tags: [] });
    expect(resolveEval(h, { rung: "toString" }, SECRET)).toBeNull();
  });

  it("drops a malformed run id instead of forwarding it as a tag", () => {
    const h = headers({ [EVAL_HEADER]: SECRET, [EVAL_RUN_HEADER]: "a b,c" });
    expect(resolveEval(h, {}, SECRET)?.tags).toEqual([]);
  });
});
