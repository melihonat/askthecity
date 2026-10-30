import { createHash, timingSafeEqual } from "node:crypto";
import { isRung } from "./config";
import type { Rung } from "./types";

// The eval header (GUARDRAILS.md, "The eval header"): only the harness sends it. It unlocks the
// `debug` event and rung presets, and will skip the answer cache and the rate limits.
export const EVAL_HEADER = "x-eval-key";
// The harness's run id; every Gateway call of the request is tagged `eval:<run-id>`.
export const EVAL_RUN_HEADER = "x-eval-run";

const RUN_ID = /^[\w.-]{1,64}$/;

const digest = (s: string) => createHash("sha256").update(s).digest();

/** Constant-time compare of the header against the secret; no secret configured means no eval access. */
export function isEvalRequest(header: string | null, secret: string | undefined): boolean {
  if (!secret || !header) return false;
  return timingSafeEqual(digest(header), digest(secret));
}

export type EvalRequest = { eval: boolean; rung: Rung; tags: string[] };

/**
 * What a request may select. Without the eval header the `rung` field is ignored and every
 * request is `shipped`; with it, an unknown rung is an error (null), never a silent fallback.
 */
export function resolveEval(headers: Headers, body: { rung?: unknown }, secret: string | undefined): EvalRequest | null {
  if (!isEvalRequest(headers.get(EVAL_HEADER), secret)) return { eval: false, rung: "shipped", tags: [] };
  const rung = body.rung ?? "shipped";
  if (!isRung(rung)) return null;
  const runId = headers.get(EVAL_RUN_HEADER);
  return { eval: true, rung, tags: runId && RUN_ID.test(runId) ? [`eval:${runId}`] : [] };
}
