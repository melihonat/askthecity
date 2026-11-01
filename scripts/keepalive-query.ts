// Writes the stored query embedding /api/keepalive searches with (GUARDRAILS.md, "Keep-alive and
// failure detection"), so the crons do real DB work with no Gateway spend. One embed call; re-run
// it only if the embedding model or dimension changes: `npm run keepalive-query`.
import { writeFileSync } from "node:fs";
import { embed } from "ai";
import { EMBEDDING } from "../lib/ask/config.ts";
import { EXAMPLES } from "../lib/ask/scope.ts";

const question = EXAMPLES[0].question;
const { embedding } = await embed({
  model: EMBEDDING.gatewayModel,
  value: question,
  providerOptions: { voyage: { inputType: "query", outputDimension: EMBEDDING.dim } },
});

// halfvec keeps about 3 significant digits, so 5 decimals lose nothing
const query = { question, model: EMBEDDING.corpusModel, embedding: embedding.map((x) => Number(x.toFixed(5))) };
writeFileSync(new URL("../app/api/keepalive/query.json", import.meta.url), JSON.stringify(query) + "\n");
console.log(`wrote ${embedding.length} dims for "${question}"`);
