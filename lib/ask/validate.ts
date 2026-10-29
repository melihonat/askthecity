import type { AskResponse, ModelOutput, PassageView } from "./types";

const MARKER = /\s*\[(\d+(?:\s*,\s*\d+)*)\]/g;
export const NEAREST = 3; // passages shown under a refusal

/**
 * Turns the model's structured output into an AskResponse (CONTRACT.md, "Generation and
 * validation"). Pure. A citation is kept when its number is in range of the passages given
 * and appears as [n] in the text; every other marker is stripped. The text is what the
 * visitor reads, so `cited` alone never makes a citation. Uncited sentences are kept.
 */
export function validate(output: ModelOutput, passages: PassageView[], scope: string): AskResponse {
  const nearest = passages.slice(0, NEAREST);
  if (output.decision === "decline") {
    return { kind: "refusal", reason: "model_declined", scope, nearest };
  }

  const byN = new Map(passages.map((p) => [p.n, p]));
  const inRange = (n: number) => byN.has(n);
  const kept: number[] = [];
  const text = output.text
    .replace(MARKER, (whole, list: string) => {
      const valid = list.split(",").map(Number).filter(inRange);
      if (!valid.length) return "";
      for (const n of valid) if (!kept.includes(n)) kept.push(n);
      const lead = whole.match(/^\s*/)![0];
      return lead + valid.map((n) => `[${n}]`).join("");
    })
    .trim();

  if (!kept.length) {
    return { kind: "refusal", reason: "no_valid_citation", scope, nearest };
  }
  return {
    kind: "answer",
    text,
    citations: kept.map((n) => ({ n, chunkId: byN.get(n)!.chunkId })),
    passages,
  };
}
