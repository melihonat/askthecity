// Pre-warms the answer cache for the example chips (GUARDRAILS.md, "Answer cache"). Run after a
// deploy, a re-ingestion or a config change: `npm run prewarm -- [base-url]`. Each chip goes
// through the public path, so what's stored is exactly what the API returns; examples aren't
// metered, so this spends no one's daily limit. Fails if a chip ends in a limit or the trick
// question isn't refused.
import { EXAMPLES } from "../lib/ask/scope.ts";

const base = (process.argv[2] ?? "https://ask-the-city.vercel.app").replace(/\/$/, "");

let failed = false;
for (const { question, trick } of EXAMPLES) {
  const res = await fetch(`${base}/api/ask`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const lines = res.ok ? (await res.text()).trim().split("\n") : [];
  const final = lines.map((l) => JSON.parse(l)).find((ev) => ev.type === "final")?.response;
  const got = !final ? `HTTP ${res.status}` : final.kind === "answer" ? "answer" : `${final.kind}: ${final.reason ?? final.limit}`;
  const ok = final && final.kind !== "limit" && (!trick || final.kind === "refusal");
  if (!ok) failed = true;
  console.log(`${ok ? "ok  " : "FAIL"} ${question} → ${got}`);
}
process.exit(failed ? 1 : 0);
