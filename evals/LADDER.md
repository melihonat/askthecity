# Experiment ladder (pre-registered)

The rungs the committed eval table walks through, fixed **before the first run**. Columns,
noise rule and `run.json` are in [`EVALS.md`](../EVALS.md); the `rung` request field is in
[`CONTRACT.md`](../CONTRACT.md#rungs-eval-header-only).

No rung is added, dropped or reordered after numbers are seen. Whatever they come out as is
what the table shows; a rung that doesn't beat the previous rung's spread is reported as no
gain.

## Main ladder: cumulative, one variable per rung

Ends exactly at the shipped stack. Anything not listed is as `shipped`.

| Rung | Retrieval | Rerank / gate | Companions | Generator / prompt |
| --- | --- | --- | --- | --- |
| `dense` | vector top 30 → top 5 by cosine; no pin, no FTS | off / off | off | Haiku 5.5, shipped prompt |
| `hybrid` | + FTS + section pin, RRF k = 60 → top 5 by RRF | off / off | off | same |
| `rerank` | hybrid top 20 → `rerank-3` → 5 | on / on, shipped threshold | off | same |
| `shipped` | as `rerank` | on / on | on (≤ 3) | same |

- The pin and FTS enter together as the **lexical** step: only 2 of 24 questions are
  lookups, so a pin-only rung would sit inside the noise. `report.md` lists the pinned
  questions.
- With the reranker off, the gate is off too; refusals come from the model and validation
  only. `rerank` uses the shipped reranker, so it shares the shipped threshold.
- **No fixed-size chunking rung.** A second chunker means a second ingestion and second
  chunk ids, which breaks gold. Chunking was decided by prototype
  ([`CHUNKING.md`](../CHUNKING.md)), not measured.

## Side table: alternatives to the shipped stack

Each row changes one thing on `shipped`; nothing stacks. Compared against `shipped`, not
against each other.

| Rung | Change | Question it answers |
| --- | --- | --- |
| `side-sonnet` | Generator Sonnet 5, same prompt | Is the bigger model worth ~3–5× the generation cost? |
| `side-quoted` | Prompt and output also ask for the supporting sentence per citation | Does quoting raise cite precision? |

- `side-quoted`'s sentences go to `debug` only, never the public contract (the contract rules spans
  out). Adopting it would be a contract change, not a ladder edit.
- No embedder side rung: swapping it costs a second embedding column and ingestion pass.

## How it runs

- **All rungs in one sitting, on one git SHA, against production.** The build-up is a
  reconstruction on the final code, not a history of past commits; the README says so.
- Order: `dense`, `hybrid`, `rerank`, `shipped`, `side-sonnet`, `side-quoted`.
- **Spend preflight.** The harness estimates the run's Gateway cost from the rung count,
  reads the remaining credit, and refuses to start unless ≥ $3 would remain for the public
  demo. Top up by hand first if needed.
- **Judge on its own key.** The harness calls Anthropic directly for the judge with a
  separate key capped in the Anthropic console; judging never spends demo credit.
- **Tagged.** Every eval call carries Gateway tag `eval:<run-id>`; each rung's real spend is
  read back into its `run.json`.
- Rough cost of a full ladder: ≈ $1–2 (Haiku rungs ≈ $0.40, `side-sonnet` ≈ $0.20–0.40,
  judge ≈ $0.50–1.00). A fix rung ≈ $0.25.

## Ship bar

Applies to `shipped` only. Pass/fail, not a target.

- 0 false refusals on test
- refusal recall ≥ 6 of 7
- cite precision ≥ 0.9
- no `contradicted` key fact in any run
- total p50 < 5 s

**Missing the bar appends a rung; it never edits one.** The fix goes through the dev split
(a new dev question, a prompt change, a recalibration) and the result is a new rung under
`shipped` (`shipped-2`, then `shipped-3`) with its change named in one line. A fix rung runs
on its new SHA with `shipped` re-run beside it on that SHA as its comparison. **At most two
fix rungs**; needing a third sends the problem back to planning (chunking or gold), not onto
the ladder.

The table is done when every rung above has a committed 3-run result and the last
`shipped*` rung passes the bar.
