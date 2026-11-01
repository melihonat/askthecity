import "server-only";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { embed, generateText, Output, rerank as rerankDocuments } from "ai";
import { z } from "zod";
import type { AskDeps } from "./ask";
import { CANDIDATES, CorpusMismatchError, EMBEDDING, MAX_OUTPUT_TOKENS, RERANK_MODEL, checkCorpus } from "./config";
import type { AskResponse, CompanionRow, DefinitionRow, SearchRow, Snapshot, Usage } from "./types";

// Created on first use, not at import: `next build` imports this module to collect page data,
// and preview builds have no Supabase env.
let client: SupabaseClient | null = null;
function db(): SupabaseClient {
  client ??= createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
    auth: { persistSession: false },
  });
  return client;
}

async function loadSnapshot(): Promise<Snapshot> {
  const { data, error } = await db()
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
export function getSnapshot(): Promise<Snapshot> {
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

/**
 * The app's dependencies. `tags` go on every AI Gateway call (embed, rerank, generate), so an
 * eval run's spend can be read back from its `eval:<run-id>` tag.
 */
export function createDeps(tags: string[] = []): AskDeps {
  const gateway: Record<string, { tags: string[] }> = tags.length ? { gateway: { tags } } : {};
  return {
    snapshot: getSnapshot,

    async embed(question) {
      const { embedding } = await embed({
        model: EMBEDDING.gatewayModel,
        value: question,
        providerOptions: { ...gateway, voyage: { inputType: "query", outputDimension: EMBEDDING.dim } },
      });
      return embedding;
    },

    async search(question, embedding, mode) {
      const { data, error } = await db().rpc("search_chunks", {
        query_text: question,
        query_embedding: JSON.stringify(embedding),
        mode,
        match_count: CANDIDATES,
      });
      if (error) throw new Error(`search_chunks: ${error.message}`);
      return data as SearchRow[];
    },

    async companions(sections) {
      const { data, error } = await db().rpc("companion_chunks", { sections });
      if (error) throw new Error(`companion_chunks: ${error.message}`);
      return data as CompanionRow[];
    },

    async definitions(documents) {
      const { data, error } = await db().rpc("definition_chunks", { documents });
      if (error) throw new Error(`definition_chunks: ${error.message}`);
      return data as DefinitionRow[];
    },

    async rerank(question, documents) {
      const { ranking } = await rerankDocuments({ model: RERANK_MODEL, query: question, documents, providerOptions: gateway });
      const scores = new Array<number>(documents.length).fill(0);
      for (const r of ranking) scores[r.originalIndex] = r.score;
      return scores;
    },

    async generate({ model, system, prompt }) {
      const { output } = await generateText({
        model,
        system,
        prompt,
        maxOutputTokens: MAX_OUTPUT_TOKENS,
        output: Output.object({ schema: modelOutput }),
        // adaptive thinking would spend the whole output cap before the answer
        providerOptions: { ...gateway, anthropic: { thinking: { type: "disabled" } } },
      });
      return output;
    },

    async useQuota(ipHash, ipLimit) {
      const { data, error } = await db().rpc("use_quota", { ip_key: ipHash, ip_limit: ipLimit }).single();
      if (error) throw new Error(`use_quota: ${error.message}`);
      return data as Usage;
    },

    async cached(key) {
      const { data, error } = await db().from("answer_cache").select("response").eq("key", key).maybeSingle();
      if (error) throw new Error(`reading answer_cache: ${error.message}`);
      return (data?.response as AskResponse | undefined) ?? null;
    },

    async store(key, response) {
      const { error } = await db().from("answer_cache").upsert({ key, response }, { onConflict: "key", ignoreDuplicates: true });
      if (error) throw new Error(`writing answer_cache: ${error.message}`);
    },
  };
}
