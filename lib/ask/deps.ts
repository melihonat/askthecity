import "server-only";

import { createClient } from "@supabase/supabase-js";
import { embed, generateText, Output } from "ai";
import { z } from "zod";
import type { AskDeps } from "./ask";
import { CorpusMismatchError, EMBEDDING, MAX_OUTPUT_TOKENS, checkCorpus } from "./config";
import type { SearchRow, Snapshot } from "./types";

const db = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
  auth: { persistSession: false },
});

async function loadSnapshot(): Promise<Snapshot> {
  const { data, error } = await db
    .from("snapshot")
    .select("id, snapshot_date, embed_model, embed_dim, scope_sentence")
    .single();
  if (error) throw new Error(`reading snapshot: ${error.message}`);
  checkCorpus(data);
  return data;
}

// Checked once per instance, starting at module load. A model or dimension mismatch stays
// failed, so every request fails fast; any other error is retried on the next request.
let snapshot: Promise<Snapshot> | null = null;
function getSnapshot(): Promise<Snapshot> {
  snapshot ??= loadSnapshot().catch((e) => {
    if (!(e instanceof CorpusMismatchError)) snapshot = null;
    throw e;
  });
  return snapshot;
}
getSnapshot().catch(() => {});

const modelOutput = z.object({
  decision: z.enum(["answer", "decline"]),
  text: z.string(),
  cited: z.array(z.number().int()),
});

export const deps: AskDeps = {
  snapshot: getSnapshot,

  async embed(question) {
    const { embedding } = await embed({
      model: EMBEDDING.gatewayModel,
      value: question,
      providerOptions: { voyage: { inputType: "query", outputDimension: EMBEDDING.dim } },
    });
    return embedding;
  },

  async search(question, embedding, mode) {
    const { data, error } = await db.rpc("search_chunks", {
      query_text: question,
      query_embedding: JSON.stringify(embedding),
      mode,
      match_count: 20,
    });
    if (error) throw new Error(`search_chunks: ${error.message}`);
    return data as SearchRow[];
  },

  async generate({ model, system, prompt }) {
    const { output } = await generateText({
      model,
      system,
      prompt,
      maxOutputTokens: MAX_OUTPUT_TOKENS,
      output: Output.object({ schema: modelOutput }),
      // adaptive thinking would spend the whole output cap before the answer
      providerOptions: { anthropic: { thinking: { type: "disabled" } } },
    });
    return output;
  },
};
