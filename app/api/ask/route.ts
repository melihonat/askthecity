import { ask } from "@/lib/ask/ask";
import { CorpusMismatchError, DEFAULT_CONFIG } from "@/lib/ask/config";
import { deps } from "@/lib/ask/deps";
import type { AskEvent } from "@/lib/ask/types";

export const maxDuration = 30;

const MAX_QUESTION = 300;

/** POST { question } → NDJSON: one `passages` event, then one `final` AskResponse. */
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  // control characters out (CR/LF/tab become spaces)
  const question = String(body?.question ?? "")
    .replace(/[\t\r\n]/g, " ")
    .replace(/[\u0000-\u001f\u007f]/g, "")
    .trim();
  if (!question) return Response.json({ error: "question is required" }, { status: 400 });

  if (question.length > MAX_QUESTION) {
    return ndjson([{ type: "final", response: { kind: "limit", limit: "too_long" } }]);
  }

  // Fail fast, before streaming, if the corpus doesn't match the query embedding config.
  try {
    await deps.snapshot();
  } catch (e) {
    const status = e instanceof CorpusMismatchError ? 500 : 503;
    console.error(e);
    return Response.json({ error: (e as Error).message }, { status });
  }

  return ndjson(ask(question, DEFAULT_CONFIG, deps));
}

function ndjson(events: AsyncIterable<AskEvent> | AskEvent[]) {
  const enc = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        for await (const ev of events) controller.enqueue(enc.encode(JSON.stringify(ev) + "\n"));
      } catch (e) {
        console.error(e);
        controller.enqueue(enc.encode(JSON.stringify({ type: "error", message: "The demo hit an error." }) + "\n"));
      }
      controller.close();
    },
  });
  return new Response(stream, { headers: { "content-type": "application/x-ndjson; charset=utf-8" } });
}
