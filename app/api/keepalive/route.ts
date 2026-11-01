import { createDeps } from "@/lib/ask/deps";
import { matchesSecret } from "@/lib/ask/guardrails";
import query from "./query.json";

/**
 * GET, called by the two daily crons in vercel.json with `Authorization: Bearer $CRON_SECRET`.
 * Runs the real `search_chunks` RPC with a stored query embedding: real DB work, no Gateway
 * spend, so Supabase Free never pauses (GUARDRAILS.md, "Keep-alive and failure detection").
 */
export async function GET(req: Request) {
  const secret = process.env.CRON_SECRET;
  if (!matchesSecret(req.headers.get("authorization"), secret && `Bearer ${secret}`)) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  try {
    const rows = await createDeps().search(query.question, query.embedding, "hybrid");
    return Response.json({ ok: true, rows: rows.length });
  } catch (e) {
    console.error(e);
    return Response.json({ ok: false }, { status: 500 });
  }
}
