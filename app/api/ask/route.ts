import { ask } from "@/lib/ask/ask";
import { createDeps } from "@/lib/ask/deps";
import { resolveEval } from "@/lib/ask/eval";
import { checkInput, clean, ipHash } from "@/lib/ask/guardrails";
import type { AskEvent, LimitKind } from "@/lib/ask/types";

export const maxDuration = 30;

/**
 * POST { question, rung? } → NDJSON: one `passages` event, then one `final` AskResponse. Under the
 * eval header, `rung` selects a preset and a `debug` event comes between the two. A limit is a
 * `final` event too, never a 500.
 */
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const question = clean(String(body?.question ?? ""));
  if (!question) return Response.json({ error: "question is required" }, { status: 400 });

  const evalReq = resolveEval(req.headers, body ?? {}, process.env.EVAL_HEADER_SECRET);
  if (!evalReq) return Response.json({ error: "unknown rung" }, { status: 400 });

  if (checkInput(question) === "too_long") return ndjson([limit("too_long")]);

  // The eval header skips the daily limits; everyone else is metered by a salted IP hash.
  let hash: string | undefined;
  if (!evalReq.eval) {
    const salt = process.env.IP_HASH_SALT;
    if (!salt) {
      console.error("IP_HASH_SALT is not set");
      return ndjson([limit("unavailable")]);
    }
    hash = ipHash(clientIp(req.headers), salt);
  }

  return ndjson(ask(question, evalReq.rung, createDeps(evalReq.tags), { debug: evalReq.eval, ipHash: hash }));
}

/** Vercel sets both headers; `x-real-ip` is the client as Vercel saw it. */
function clientIp(headers: Headers): string {
  return headers.get("x-real-ip") ?? headers.get("x-forwarded-for")?.split(",")[0].trim() ?? "unknown";
}

function limit(kind: LimitKind): AskEvent {
  return { type: "final", response: { kind: "limit", limit: kind } };
}

function ndjson(events: AsyncIterable<AskEvent> | AskEvent[]) {
  const enc = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        for await (const ev of events) controller.enqueue(enc.encode(JSON.stringify(ev) + "\n"));
      } catch (e) {
        // ask() turns its own failures into limits; this only catches a broken stream
        console.error(e);
        controller.enqueue(enc.encode(JSON.stringify(limit("unavailable")) + "\n"));
      }
      controller.close();
    },
  });
  return new Response(stream, { headers: { "content-type": "application/x-ndjson; charset=utf-8" } });
}
