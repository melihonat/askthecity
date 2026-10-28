import { CONTEXT_PASSAGES } from "./config";
import { systemPrompt, userPrompt } from "./prompt";
import type { AskEvent, ModelOutput, PassageView, RungConfig, SearchRow, Snapshot } from "./types";
import { validate } from "./validate";

export type AskDeps = {
  snapshot(): Promise<Snapshot>;
  embed(question: string): Promise<number[]>;
  search(question: string, embedding: number[], mode: RungConfig["search"]): Promise<SearchRow[]>;
  generate(req: { model: string; system: string; prompt: string }): Promise<ModelOutput>;
};

export function toPassage(row: SearchRow, n: number): PassageView {
  return {
    n,
    chunkId: row.id,
    companion: false,
    family: row.family,
    label: row.label,
    sublabel: row.sublabel,
    href: row.href,
    amendedSince: row.amended_since ?? [],
    body: row.body,
  };
}

/** The one orchestration path: embed → search → generate → validate. */
export async function* ask(question: string, config: RungConfig, deps: AskDeps): AsyncGenerator<AskEvent> {
  const snapshot = await deps.snapshot();
  const embedding = await deps.embed(question);
  const rows = await deps.search(question, embedding, config.search);
  const passages = rows.slice(0, CONTEXT_PASSAGES).map((r, i) => toPassage(r, i + 1));
  yield { type: "passages", passages };

  const output = await deps.generate({
    model: config.model,
    system: systemPrompt(snapshot.snapshot_date),
    prompt: userPrompt(question, passages),
  });
  yield { type: "final", response: validate(output, passages, snapshot.scope_sentence) };
}
