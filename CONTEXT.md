# Ask the City — domain language

Terms settled while planning (see `.scratch/ask-the-city/map.md`). Use these words in code,
docs and UI copy.

- **Snapshot** — the frozen, dated set of source documents the assistant knows. Taken by
  hand, never refreshed automatically. Its **snapshot date** is the day the ingestion run
  fetches the Code and by-laws.
- **Manifest** — the committed list of every file in the snapshot: source URL,
  Last-Modified/ETag, sha256, and the date it was fetched or saved. Public; the files
  themselves are not.
- **Scope sentence** — the one sentence telling the visitor what the snapshot covers and
  names what it doesn't (parking schedules, zoning). A refusal is explained against it.
- **Rules** — the Toronto Municipal Code plus its amending by-laws.
- **Chapter** — one Municipal Code chapter PDF (e.g. Ch 591 Noise), in its consolidated form.
- **Consolidated as of** — a chapter's footer date: the last amendment folded into its text.
  Text amended later is not in the chapter.
- **Amending by-law** — a by-law enacted after a chapter's consolidated-as-of date that
  changes its main text. Ingested alongside the chapter so answers aren't stale.
- **In force** — the date a by-law takes effect, when it differs from enactment (Ch 611:
  May 1, 2027).
- **Schedule** — a table appended to a chapter (e.g. Ch 950's street-by-street parking
  schedules). Not in the snapshot.
- **Decisions** — the Infrastructure and Environment Committee's (IE) items, IE24–IE31.
- **Item** — one agenda item (e.g. 2026.IE29.6): its **item page** (decision text, status per
  stage, motions, votes) plus its **staff reports**. Attachments and communications are not
  part of an item in the snapshot.
- **Replacement by-law** — an amending by-law that repeals and replaces a whole chapter
  (1511-2025 for Ch 497, 1512-2025 for Ch 629). Once **in force** it stands in for that
  chapter and the stale consolidated PDF is dropped; until then the old chapter is the law
  and the replacement's §§ ride along as companion passages.
- **Staff report** — a `bgrd/` file whose item-page label reads "Report from …" or
  "Supplementary Report from …". Not every `bgrd/` file is one: attachments and councillor
  letters live there too and are not in the snapshot.
- **Status stamp** — the line every Decisions chunk carries saying where its item ended up
  (adopted, amended, referred, deferred; by whom, when). Keeps a referred item from reading
  as adopted.
- **Chunk** — the retrievable unit: one Code §, one amending by-law (or one of its
  operative clauses), one item-page block, or one staff-report section; split further only
  above ~800 tokens. See `CHUNKING.md`.
- **Breadcrumb** — the header line(s) prepended to a chunk for embedding and search: where
  it sits (chapter › article › §, or item › block) plus its dates or status stamp.
- **Citation** — a pointer from a claim in an answer to one chunk the model was given,
  shown to the visitor as a label built from that chunk's metadata (`Ch 681 § 681-5 C–D ·
  p. 7`) linking to its source. No quoted span: the chunk is the unit a reader checks.
- **Passage** — a chunk as it appears in one answer: retrieved, numbered `[1]`–`[5]` and
  shown to the model. Its number means nothing outside that answer; a citation resolves it
  back to the chunk.
- **Answer** — a reply that makes claims about the snapshot, each backed by at least one
  citation. An answer with no valid citation is not an answer.
- **Refusal** — a reply saying the snapshot doesn't cover the question, with its reason
  (below threshold, model declined, no valid citation), the scope sentence and the nearest
  passages that weren't good enough. A judgement about the documents.
  _Avoid_: "I don't know", empty answer, error.
- **Limit** — a reply saying the demo won't answer right now (per-IP or global daily limit,
  burst, budget, question too long). A fact about the infrastructure, never counted as a
  refusal.
- **Companion passage** — an amending by-law's chunk added to an answer because it amends a
  § that was retrieved, not because it ranked itself. Numbered after the retrieved passages
  and citeable like them.
- **Chunk id** — a chunk's readable, deterministic name built from where it sits
  (`tmc:681-5:C-D`, `bl:470-2026:cl1`, `ie:2026.IE29.6:council`, `sr:286369:comments:2`).
  The same source yields the same id on every ingestion; gold answers are written in it.
  _Avoid_: UUID, row id.
- **Gold** — what the eval counts as a right source for a question: **required groups** of
  chunk-id patterns (exact, or a prefix like `tmc:681-5:*`; any pattern satisfies its
  group), plus **acceptable** patterns that may be cited without satisfying anything. See
  `EVALS.md`.
- **Context** (in the eval) — every passage the model was given for one answer: the reranked
  top 5 plus companion passages. `hit@ctx` is scored against it.
- **Stale gold** — a required group that matches no chunk in the current snapshot. Flagged
  and dropped from scoring for that run, never a miss.
- **Unstable question** — one whose outcome differed across the 3 runs of a rung.
- **Gate** — the check after reranking and before generation: top rerank score (the **gate
  score**) against the **threshold**. Below it, a `below_threshold` refusal with no LLM call.
  Permissive by design; a pinned section match skips it. See `CONTRACT.md`, "Refusal rule".
- **Pin** — a chunk placed at the top by the section-number exact match, not by ranking.
- **Gap sentence** — the one uncited sentence a partial answer ends with, naming what the
  snapshot doesn't cover. Not counted in citation coverage.
- **Rung** — one named configuration in the eval table (`dense`, `hybrid`, `rerank`,
  `shipped`, …), selected per request by a preset under the eval header. The **main ladder**
  adds one component per rung up to `shipped`; a **side rung** changes one thing on `shipped`.
  Pre-registered in `evals/LADDER.md`.
- **Ship bar** — the pass/fail checks `shipped` must meet (0 false refusals, refusal recall
  ≥ 6/7, cite precision ≥ 0.9, no contradicted fact, total p50 < 5 s). A miss appends a
  **fix rung** (`shipped-2`); rows are never edited.
- **Dev split** — the `split: dev` eval questions: used to set the threshold and tune the
  decline prompt, never shown in the table. The reported questions are `split: test`.
