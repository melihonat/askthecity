# 2026-11-02-shipped-dev-default9-exc-170108

Rung `shipped` · split `dev` · 3 runs · http://localhost:3124  
Git `f719fd5` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 12 | 0.00 |
| full@20 | 0.92 | 12 | 0.00 |
| hit@ctx | 1.00 | 12 | 0.00 |
| full@ctx | 0.92 | 12 | 0.00 |
| cite_precision | 0.78 | 11 | 0.16 |
| cite_full | 0.91 | 11 | 0.01 |
| coverage | 0.98 | 11 | 0.03 |
| answer_correct | 0.83 | 11 | 0.04 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.03 | 12 | 0.08 |
| passages_p50 | 915 ms | 51 | 127 ms |
| total_p50 | 3,151 ms | 35 | 384 ms |
| total_p95 | 4,122 ms | 35 | 436 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.11 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-dev-default9-exc-170108`): $0.0579 over 150 requests
Harness wall-clock p50: 2,915 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-holistic-fees`
- `dev-fireworks-backyard`
- `dev-leaf-blower`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

- `dev-deleted-dealer-hours`: answer → answer → refusal:model_declined

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-park-bonfire` run 2: `tmc:608-11`
- `dev-park-bonfire` run 3: `tmc:608-11`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-night` run 1: `tmc:608-34`
- `dev-exception-park-night` run 2: `tmc:608-34`
- `dev-exception-park-night` run 3: `tmc:608-34`
- `dev-exception-park-night` run 3: `bl:1482-2025:cl1:O-Y`

## Contradicted key facts (answer correct 0 for that answer)

- `dev-deleted-holistic-fees` run 2 fact 1: “Yes. Every owner must file with the Municipal Licensing and Standards Division a list of all services offered”
- `dev-deleted-holistic-fees` run 3 fact 1: “Yes. Every owner must file with the Municipal Licensing and Standards Division a list of all services offered at the holistic centre and the fees charged”
- `dev-deleted-dealer-hours` run 1 fact 1: “The Tuesday restriction therefore applies, so staying open until midnight on a Tuesday is not allowed under the consolidated text”

## Judge spans not found word for word in the answer (check the verdict)

None.

## Refusal reasons

- Answer questions refused: model_declined × 1
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
