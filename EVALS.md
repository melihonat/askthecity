# Eval scoring

What each column of the eval table measures, how gold is written and what a committed run
records. The response
shape and the `debug` event are in [`CONTRACT.md`](CONTRACT.md); terms are defined in
[`CONTEXT.md`](CONTEXT.md).

## Harness

- Python, on the offline side of the language split. It calls the deployed `/api/ask` over
  HTTP with the **eval header** ([`GUARDRAILS.md`](GUARDRAILS.md#the-eval-header)), which bypasses the answer cache and the rate limits and
  unlocks the `debug` event. Retrieval logic exists only in the app.
- Calls are **sequential**, never concurrent. The first call of a run is a discarded
  warm-up.
- Every question runs **3 times** per rung.
- **A `limit` response or an HTTP error invalidates the run.** A 5xx is retried once, then
  the run aborts. A run with any unscored question is never committed.
- One rung per invocation: `python -m evals run --rung shipped [--split dev] [--base-url …]`
  writes `evals/runs/<date>-<rung>[-dev]/` and refuses to overwrite one; `--suffix 2`
  names a second run of the rung on the same day (`…-dev-2/`). The scorer
  (`evals/score.py`) is pure: run data, gold and the snapshot's chunk ids in, columns out.

## Gold

Each question in `evals/questions.yaml`:

```yaml
- id: rules-manganese-limit
  question: How much manganese can a business put down the sewer?
  category: amended_since          # categories in evals/questions.yaml
  expect: answer                   # answer | refuse
  required:                        # groups; each group is any-of
    - [ "tmc:681-4:*" ]
    - [ "bl:470-2026:cl1" ]
  acceptable: [ "tmc:681-1:*" ]    # fine to cite, satisfies nothing
  key_facts:
    - The manganese limit is … mg/L
  split: test                      # test = reported; dev = threshold and prompt tuning only
  notes: …
```

- A **pattern** is an exact chunk id or a prefix ending in `*` (`tmc:681-5:*` = any chunk of
  § 681-5, including `tmc:681-5` itself when the § is one chunk). The question's author picks
  the granularity; the scorer only does exact-or-prefix matching.
- A **required group** is satisfied when any of its patterns matches.
- `refuse` questions carry no `required`, `acceptable` or `key_facts`.
- **Stale gold:** a required group whose patterns match zero chunks in the snapshot. The
  question is dropped from the retrieval and citation columns for that run and listed in the
  report. Never scored as a miss.

## Columns

Retrieval and citation columns are computed over `answer` questions only, and the citation
and correctness columns only over those the system actually answered. Every column shows
its **n scored**.

| Column | Definition |
| --- | --- |
| **recall@20** | Share of questions with at least one required group satisfied among the 20 fused candidates (pre-rerank, from `debug`). |
| **full@20** | Share with every required group satisfied among the 20. |
| **hit@ctx** | At least one required group satisfied in the **context**: the reranked top 5 plus companion passages (≤ 8). |
| **full@ctx** | Every required group satisfied in the context. |
| **cite precision** | Per answer, cited chunks matching `required` or `acceptable`, or a **definition companion** of that answer, ÷ cited chunks; mean over answered `answer` questions. One right, one wrong = 0.5. |
| **cite full** | Share of answered `answer` questions where every required group is matched by a citation (`acceptable` doesn't count). |
| **coverage** | Per answer, counted sentences with ≥ 1 valid `[n]` ÷ counted sentences; mean over answers. |
| **answer correct** | Per answer, key facts judged `present` ÷ key facts, **0 if any is `contradicted`**; mean over answered `answer` questions. |
| **refusal recall** | Of `refuse` questions, the share refused. |
| **false refusals** | Of `answer` questions, the share refused. |
| **passages p50** | Server `retrieval_ms + rerank_ms`, all calls. |
| **total p50 / p95** | Server `total_ms`, answered calls only (a `below_threshold` refusal skips generation and would flatter a rung that refuses more). |

**Definition companions in cite precision** (added 2026-11-01, after the first full ladder
run, applied to every rung): gold was written before definition companions existed, so a
citation of a definition the app attached to that answer counts as acceptable. It satisfies
no required group, so cite full is unchanged. The run that prompted it scored `shipped` at
0.69 cite precision without the rule and 0.78 with it.

**Gold audit** (2026-11-01, #56, after `shipped-2` missed the bar): every distinct citation
outside gold in the committed test runs (25 question/chunk pairs, `python -m evals gold-audit`)
was reviewed by hand in `evals/gold_audit.csv`. 23 were accepted because the passage states the
sentence citing it, and were added to `acceptable` (marked `# audit` in `evals/questions.yaml`).
`required`, key facts and splits are unchanged. Rows run before the audit keep the scores they ran
with: re-scored against gold widened from their own citations, every rung's cite precision goes to
0.99–1.00 by construction, so the column would no longer tell them apart. Only runs after the audit
are scored against it.

The reranker's contribution is the gap between recall@20 and hit@ctx; the companions'
contribution shows in full@ctx and cite full.

### Coverage sentences

A fixed sentence splitter that does not break on `§`, `s.`, `ss.`, `No.` or decimals. Every
sentence counts except those under 6 words and the scope/gap sentence the prompt asks for.
No judge.

### Answer judge

- Sees **only** the question, its `key_facts` and the answer text; no passages (citations
  already measure grounding).
- Returns, per fact, `present | absent | contradicted` with the quoted span from the answer
  that justifies it.
- Pinned model from a different tier than the generator (Sonnet 5, `claude-sonnet-5`,
  judging Haiku 5.5), prompt versioned in the repo (`evals/judge_prompt.md`,
  `PROMPT_VERSION` in `evals/judge.py`); its id, prompt version and prompt hash go in every
  run, with its token cost on its own key.
- **No temperature 0:** Sonnet 5 takes no sampling parameters. The judge runs with thinking
  off and a fixed JSON schema instead; on the dev answers it gave the same verdict twice for
  every fact. A quoted span that isn't in the answer word for word is flagged in
  `report.md`, not fatal.
- `python -m evals run` judges by default; `--skip-judge` leaves the column out (and the
  ship bar reads "not judged yet").
- **Human audit:** the user hand-scores the first full run; judge/human agreement is
  committed and shown under the table. Changing the judge model or prompt means a fresh
  audit: the renderer drops an agreement whose judge differs from the published `shipped`
  run's.
  1. `python -m evals audit sheet evals/runs/<run> [--runs 1]` writes
     `evals/judge_audit.csv`, one row per key fact of each judged answer, without the
     judge's verdict.
  2. Fill `human` with `present`, `absent` or `contradicted` (`p`/`a`/`c`).
  3. `python -m evals audit agreement` writes `evals/judge_agreement.json` (agree, total,
     the run, its judge, each disagreement); `python -m evals results` publishes it.

## Noise

- **Retrieval columns** come from run 1. The harness asserts runs 2–3 returned identical
  candidates; a mismatch is flagged as a bug (e.g. a non-deterministic RRF tiebreak).
- **Generation columns** (cite, coverage, answer correct, refusal columns) are the **mean of
  the 3 runs**. A question whose outcome differed across runs is listed as **unstable**.
- A rung counts as an improvement only when it beats the previous rung by more than its own
  run-to-run spread.

## Refusal threshold

The gate's only job is never to refuse an answerable question, so the threshold comes from a
rule, not a search:

- **`threshold = 0.5 × the lowest gate score among un-pinned `split: dev` answer
  questions`**, from one dev run, each question's lowest score across its runs (rerank
  scores jitter in the 4th decimal), floored to 3 places. The 0.5 margin covers unseen
  rephrasings. Dev refusals falling below it are a bonus, never a target.
- **Never tuned on `test`.** A `below_threshold` false refusal in a reported run stays in
  the table; the fix is a dev question covering that case, then a recalibration.
- **Recalibrated only** when the reranker, `chunker_version` or embedder changes. The
  threshold is in the answer-cache key, so a change invalidates cached answers.
- **Recorded** in app config, in every `run.json` header, and here: the generated table
  below (dev question, gate score, pinned, outcome) with its date. Not hand-edited.
- The decline prompt is tuned on the same dev split; its hash goes in `run.json` like the
  judge's.

<!-- calibrate:start -->
Generated 2026-11-01 by `python -m evals calibrate` from run `2026-10-31-shipped-dev-231639`: lowest un-pinned dev answer gate score 0.719 → **threshold 0.359**.

| Dev question | Expect | Gate score (lowest) | Spread | Pinned | Outcome (3 runs) | Gate at threshold |
| --- | --- | --- | --- | --- | --- | --- |
| `dev-driverless-tickets` | answer | 0.805 | 0.0000 | no | answer ×3 | passes |
| `dev-pool-permit` | answer | 0.780 | 0.0009 | no | answer ×3 | passes |
| `dev-park-bonfire` | answer | 0.768 | 0.0000 | no | answer ×3 | passes |
| `dev-fireworks-backyard` | answer | 0.768 | 0.0014 | no | answer ×3 | passes |
| `dev-lawn-height` | answer | 0.719 | 0.0000 | no | answer ×3 | passes |
| `dev-refuse-garbage-day` | refuse | 0.707 | 0.0002 | no | model_declined ×3 | passes |
| `dev-refuse-landlord-entry` | refuse | 0.600 | 0.0000 | no | answer ×2, model_declined ×1 | passes |
| `dev-refuse-401-speed` | refuse | 0.562 | 0.0007 | no | model_declined ×3 | passes |
| `dev-refuse-patio` | refuse | 0.351 | 0.0000 | no | model_declined ×3 | refuses |
| `dev-refuse-leafs` | refuse | 0.264 | 0.0009 | no | below_threshold ×3 | refuses |
<!-- calibrate:end -->

## Ladder

The rungs, their order, the ship bar and the spend preflight are pre-registered in
[`evals/LADDER.md`](evals/LADDER.md). The judge
calls Anthropic directly on its own capped key, not through the app. `run.json`'s header
also records the `rung` and its resolved `RungConfig`, and each rung's real Gateway spend
read back from its `eval:<run-id>` tag.

## Files

```
evals/
  questions.yaml
  LADDER.md                  # pre-registered rungs, ship bar
  judge_prompt.md
  judge_audit.csv            # the hand scores (python -m evals audit sheet)
  judge_agreement.json       # judge vs hand scores (python -m evals audit agreement)
  RESULTS.md                 # generated from runs/*/run.json, never hand-edited
  runs/<date>-<rung>/
    run.json
    report.md
```

- **`run.json`**: a config header (git SHA, `snapshot.id`, `chunker_version`, embedder,
  reranker, LLM and judge model ids, judge and generation prompt hashes, refusal threshold,
  harness version, date), then per question per run: the `AskResponse`, the `debug` event and the judge
  verdicts.
- **Passage `body` is stripped** before committing ([`CORPUS.md`](CORPUS.md#copyright): City text stays out of the public
  repo). Chunk ids, labels and hrefs stay, so every citation can still be followed to the
  City's PDF. The model's answer text stays.
- **`report.md`**: citations outside `required`/`acceptable` listed by name (widen
  `acceptable` in a commit, or accept the miss), unstable questions, the refusal-reason
  breakdown in each direction, stale gold, and harness wall-clock p50 with where it ran
  from.
- **`RESULTS.md`**: one row per rung. The app's eval page renders from the same data.
- **`python -m evals results`** (`evals/results.py`) regenerates `RESULTS.md`, the README's
  `headline` and `ladder` blocks (text outside the markers untouched) and
  `app/evals/results.json`, which the static `/evals` page and the header's
  `Evals · x/7` link read. It publishes the latest `split: test` run of each rung; dev runs
  never appear. The judge/human audit is read from `evals/judge_agreement.json` once
  committed (and only for the judge it audited), and the ship bar's contradicted check from
  `answer_correct.contradicted`, the count of contradicted facts over every run; an
  unjudged `shipped` reads "not judged yet" and isn't highlighted.
