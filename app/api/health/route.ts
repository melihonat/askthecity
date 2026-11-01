import { pingDb } from "@/lib/ask/deps";

/**
 * GET: a DB-only check, polled daily by .github/workflows/health.yml. 503 when the DB is paused
 * or unreachable, which fails the workflow and GitHub e-mails the owner. Vercel doesn't alert on
 * cron failures, and a dead DB takes down the cache, examples and limits.
 */
export async function GET() {
  try {
    await pingDb();
    return Response.json({ ok: true });
  } catch (e) {
    console.error(e);
    return Response.json({ ok: false }, { status: 503 });
  }
}
