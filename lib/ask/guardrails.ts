import { createHmac } from "node:crypto";
import { MAX_QUESTION } from "./config";
import type { LimitKind, Usage } from "./types";

// The pure core of GUARDRAILS.md: input checks, the IP hash, and the limit decisions.

export const IP_DAILY = 30; // paid questions per IP per Toronto day
export const GLOBAL_DAILY = 500; // paid questions per Toronto day, all visitors

/** Control characters out (tab, CR and LF become spaces), trimmed: what the pipeline sees. */
export function clean(raw: string): string {
  return raw
    .replace(/[\t\r\n]/g, " ")
    .replace(/[\u0000-\u001f\u007f]/g, "")
    .trim();
}

/** The answer-cache form of a question: cleaned, lowercased, whitespace collapsed. */
export function normalise(question: string): string {
  return clean(question).toLowerCase().replace(/\s+/g, " ");
}

/** On a cleaned question; the cap counts what the UI counter counts. */
export function checkInput(question: string): "ok" | "too_long" {
  return question.length > MAX_QUESTION ? "too_long" : "ok";
}

/** Keyed hash of the client IP: `usage_daily` never holds the IP itself. */
export function ipHash(ip: string, salt: string): string {
  return createHmac("sha256", salt).update(ip).digest("hex");
}

export function usageLimit(usage: Usage): "ip_daily" | "global_daily" | null {
  if (usage.ip >= IP_DAILY) return "ip_daily";
  if (usage.global >= GLOBAL_DAILY) return "global_daily";
  return null;
}

/** The HTTP status behind an AI SDK or Gateway error, through retry and cause wrappers. */
function statusOf(error: unknown, depth = 0): number | null {
  if (!error || typeof error !== "object" || depth > 4) return null;
  const e = error as { statusCode?: unknown; lastError?: unknown; cause?: unknown };
  if (typeof e.statusCode === "number") return e.statusCode;
  return statusOf(e.lastError, depth + 1) ?? statusOf(e.cause, depth + 1);
}

/** Any failure as a limit, never a raw 500: out of credit is `budget`, rate-limited upstream is `burst`. */
export function failureLimit(error: unknown): LimitKind {
  const status = statusOf(error);
  if (status === 402) return "budget";
  if (status === 429) return "burst";
  return "unavailable";
}
