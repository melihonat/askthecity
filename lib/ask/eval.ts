import { isRung, PUBLIC_RUNG } from "./config";
import { matchesSecret } from "./guardrails";
import type { Rung } from "./types";

// The eval header (GUARDRAILS.md, "The eval header"): only the harness sends it. It unlocks the
// `debug` event and rung presets, and skips the answer cache and the daily limits.
export const EVAL_HEADER = "x-eval-key";
// The harness's run id; every Gateway call of the request is tagged `eval:<run-id>`.
export const EVAL_RUN_HEADER = "x-eval-run";

const RUN_ID = /^[\w.-]{1,64}$/;

export type EvalRequest = { eval: boolean; rung: Rung; tags: string[] };

/**
 * What a request may select. Without the eval header the `rung` field is ignored and every
 * request is `PUBLIC_RUNG`; with it, an unknown rung is an error (null), never a silent fallback.
 */
export function resolveEval(headers: Headers, body: { rung?: unknown }, secret: string | undefined): EvalRequest | null {
  if (!matchesSecret(headers.get(EVAL_HEADER), secret)) return { eval: false, rung: PUBLIC_RUNG, tags: [] };
  const rung = body.rung ?? PUBLIC_RUNG;
  if (!isRung(rung)) return null;
  const runId = headers.get(EVAL_RUN_HEADER);
  return { eval: true, rung, tags: runId && RUN_ID.test(runId) ? [`eval:${runId}`] : [] };
}
